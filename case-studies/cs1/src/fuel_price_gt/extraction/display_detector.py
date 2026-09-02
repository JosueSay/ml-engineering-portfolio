"""Localiza el visor de precio en la fotografía y lo endereza.

Es la primera de las dos etapas del reconocimiento, y la que más pesa: con la
calibración por encuadre fijo, diez de dieciséis recortes apuntaban a la
carcasa o al bisel, y ningún reconocedor puede leer lo que no está.

La segunda parte es igual de importante y menos evidente. Aunque el recorte
acierte, el visor llega en trapecio porque la fotografía se toma desde abajo y
de lado. Los motores de reconocimiento confunden entonces los dígitos que más
se parecen al inclinarse —el nueve con el cuatro, el cinco con el cero, el cero
con el seis—, que es exactamente el patrón de errores observado. Rectificar el
cuadrilátero a rectángulo antes de leer elimina esa causa.

El visor tiene tres rasgos que lo distinguen del resto del dispensador y que no
dependen del encuadre:

- Es claro y uniforme, porque está retroiluminado, sobre una carcasa más oscura.
- Es alargado: los precios ocupan una franja de proporción ancha.
- Tiene contenido oscuro dentro, los propios dígitos, mientras que la carcasa
  es lisa.

Buscar por esos rasgos en vez de por posición es lo que permite que funcione
con fotografías de años distintos y encuadres distintos.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Proporción ancho/alto plausible de una franja de precio. Un visor de cuatro
# dígitos con punto es claramente apaisado; por debajo de dos suele ser un
# fragmento de carcasa y por encima de nueve, una junta o una sombra alargada.
PROPORCION_MINIMA = 2.0
PROPORCION_MAXIMA = 9.0

# Fracción del panel que el visor debe ocupar como mínimo. Descarta reflejos y
# manchas claras pequeñas.
AREA_MINIMA_RELATIVA = 0.02

# Tamaño al que se rectifica. Alto suficiente para que los segmentos no se
# fundan al reescalar, y proporción fija para que el clasificador reciba
# siempre dígitos de la misma forma.
ALTO_RECTIFICADO = 120


@dataclass
class DisplayDetection:
    """Visor localizado y enderezado, listo para leer.

    `quad` son las cuatro esquinas en la imagen de entrada, para poder dibujar
    encima qué se detectó, y `confidence` cuánto encaja con los rasgos de un
    visor. Cuando la detección falla, `found` es falso y `image` trae el recorte
    de respaldo sin rectificar: es preferible leer algo torcido a no leer nada.
    """

    image: np.ndarray
    found: bool
    quad: np.ndarray | None = None
    confidence: float = 0.0
    reason: str = ""


def _ordenar_esquinas(puntos: np.ndarray) -> np.ndarray:
    """Ordena cuatro esquinas como arriba-izq, arriba-der, abajo-der, abajo-izq.

    La transformación de perspectiva necesita saber qué esquina va a dónde; sin
    un orden fijo, el resultado sale reflejado o girado.
    """
    puntos = puntos.reshape(4, 2).astype(np.float32)
    suma = puntos.sum(axis=1)
    resta = np.diff(puntos, axis=1).ravel()
    return np.array(
        [
            puntos[np.argmin(suma)],   # arriba izquierda: menor x+y
            puntos[np.argmin(resta)],  # arriba derecha: menor y-x
            puntos[np.argmax(suma)],   # abajo derecha
            puntos[np.argmax(resta)],  # abajo izquierda
        ],
        dtype=np.float32,
    )


def _candidatos(gris: np.ndarray) -> list[np.ndarray]:
    """Contornos de las regiones claras que podrían ser el visor.

    Se usa umbral de Otsu y no uno fijo porque la iluminación cambia por
    completo entre una foto a mediodía y otra al atardecer, y un corte fijo
    acertaría solo en una de las dos.
    """
    desenfocado = cv2.GaussianBlur(gris, (5, 5), 0)
    _, claro = cv2.threshold(desenfocado, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Cerrar une los dígitos con el fondo del visor, para que la región salga
    # como un bloque y no como letras sueltas.
    nucleo = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 9))
    cerrado = cv2.morphologyEx(claro, cv2.MORPH_CLOSE, nucleo)

    contornos, _ = cv2.findContours(cerrado, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return list(contornos)


def _puntuar(contorno: np.ndarray, area_panel: float, gris: np.ndarray) -> tuple[float, np.ndarray | None]:
    """Puntúa cuánto se parece un contorno a un visor de precio.

    Devuelve la puntuación y las cuatro esquinas del rectángulo mínimo que lo
    contiene, o `None` si no cumple los mínimos.
    """
    area = cv2.contourArea(contorno)
    if area < area_panel * AREA_MINIMA_RELATIVA:
        return 0.0, None

    rect = cv2.minAreaRect(contorno)
    (_, _), (ancho, alto), _ = rect
    if ancho < 1 or alto < 1:
        return 0.0, None

    largo, corto = max(ancho, alto), min(ancho, alto)
    proporcion = largo / corto
    if not (PROPORCION_MINIMA <= proporcion <= PROPORCION_MAXIMA):
        return 0.0, None

    esquinas = cv2.boxPoints(rect)

    # Un visor tiene dígitos dentro: su interior no es liso. Una zona clara y
    # uniforme de la carcasa puntúa bajo aquí, y es justo lo que se colaba.
    mascara = np.zeros(gris.shape, np.uint8)
    cv2.drawContours(mascara, [esquinas.astype(np.int32)], -1, 255, -1)
    interior = gris[mascara == 255]
    if interior.size == 0:
        return 0.0, None
    contraste_interno = float(interior.std())

    # Lo que se llena de verdad frente a su rectángulo: un visor es casi
    # rectangular, una sombra irregular no.
    llenado = area / (largo * corto)

    puntuacion = (
        min(contraste_interno / 60.0, 1.0) * 0.5
        + llenado * 0.3
        + min(area / area_panel, 0.5) * 0.4
    )
    return puntuacion, esquinas


def _rectificar(imagen: np.ndarray, esquinas: np.ndarray) -> np.ndarray:
    """Endereza el cuadrilátero detectado a un rectángulo recto.

    Es lo que quita la perspectiva. Sin esto los dígitos llegan en trapecio y
    el reconocedor confunde los que se parecen al inclinarse.
    """
    ordenadas = _ordenar_esquinas(esquinas)
    ancho_arriba = np.linalg.norm(ordenadas[1] - ordenadas[0])
    ancho_abajo = np.linalg.norm(ordenadas[2] - ordenadas[3])
    ancho = int(max(ancho_arriba, ancho_abajo))
    alto_izq = np.linalg.norm(ordenadas[3] - ordenadas[0])
    alto_der = np.linalg.norm(ordenadas[2] - ordenadas[1])
    alto = int(max(alto_izq, alto_der))
    if ancho < 10 or alto < 5:
        return imagen

    escala = ALTO_RECTIFICADO / alto
    destino_ancho = max(20, int(ancho * escala))
    destino = np.array(
        [
            [0, 0],
            [destino_ancho - 1, 0],
            [destino_ancho - 1, ALTO_RECTIFICADO - 1],
            [0, ALTO_RECTIFICADO - 1],
        ],
        dtype=np.float32,
    )
    matriz = cv2.getPerspectiveTransform(ordenadas, destino)
    return cv2.warpPerspective(imagen, matriz, (destino_ancho, ALTO_RECTIFICADO))


def detect_display(panel_rgb: np.ndarray) -> DisplayDetection:
    """Localiza el visor dentro del recorte de un panel y lo endereza.

    Si no encuentra nada que se parezca a un visor lo dice, en vez de devolver
    un recorte cualquiera como si lo fuera: esa distinción es la que permite
    separar un fallo de localización de uno de lectura.
    """
    if panel_rgb.size == 0:
        return DisplayDetection(panel_rgb, False, reason="panel vacio")

    gris = cv2.cvtColor(panel_rgb, cv2.COLOR_RGB2GRAY)
    area_panel = float(gris.shape[0] * gris.shape[1])

    mejor_puntuacion, mejores_esquinas = 0.0, None
    for contorno in _candidatos(gris):
        puntuacion, esquinas = _puntuar(contorno, area_panel, gris)
        if esquinas is not None and puntuacion > mejor_puntuacion:
            mejor_puntuacion, mejores_esquinas = puntuacion, esquinas

    if mejores_esquinas is None:
        return DisplayDetection(
            panel_rgb, False, reason="ninguna region con forma de visor"
        )

    return DisplayDetection(
        image=_rectificar(panel_rgb, mejores_esquinas),
        found=True,
        quad=mejores_esquinas,
        confidence=round(min(mejor_puntuacion, 1.0), 3),
    )
