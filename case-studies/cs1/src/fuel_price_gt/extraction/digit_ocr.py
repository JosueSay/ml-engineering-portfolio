"""Lectura de dígitos de un visor LCD de 7 segmentos.

Se implementa un clasificador de 7 segmentos "clásico" (sin dependencias de
sistema) como motor por defecto: es determinista, no requiere el binario
`tesseract` ni modelos pesados, y está hecho a la medida de paneles LED/LCD
(a diferencia de Tesseract, que está afinado para tipografías impresas).
Si el binario de `tesseract` está disponible en el sistema (p. ej. dentro
del contenedor Docker, que sí lo instala) se usa como motor alterno/mejor
esfuerzo y se compara con el resultado del clasificador de 7 segmentos.

Ver Business Understanding: "Tesseract/EasyOCR" como herramientas candidatas,
y el riesgo R6 (falla de lectura) con su mitigación de preprocesamiento +
validación estadística.
"""
from __future__ import annotations

import functools
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

# Mapa de patrones de 7 segmentos -> dígito.
# Orden de segmentos: (arriba, sup-izq, sup-der, medio, inf-izq, inf-der, abajo)
_PATTERNS: dict[tuple[int, ...], str] = {
    (1, 1, 1, 0, 1, 1, 1): "0",
    (0, 0, 1, 0, 0, 1, 0): "1",
    (1, 0, 1, 1, 1, 0, 1): "2",
    (1, 0, 1, 1, 0, 1, 1): "3",
    (0, 1, 1, 1, 0, 1, 0): "4",
    (1, 1, 0, 1, 0, 1, 1): "5",
    (1, 1, 0, 1, 1, 1, 1): "6",
    (1, 0, 1, 0, 0, 1, 0): "7",
    (1, 1, 1, 1, 1, 1, 1): "8",
    (1, 1, 1, 1, 0, 1, 1): "9",
}


@dataclass
class OcrReading:
    """Resultado de leer un visor: texto, valor, confianza y qué motor lo leyó.

    El texto crudo se conserva junto al valor porque explica los rechazos:
    un `3?.95` dice que falló un dígito concreto, no la lectura entera.
    """
    text: str
    value: float | None
    confidence: float
    engine: str


def _deskew(binary: np.ndarray) -> np.ndarray:
    """Endereza el visor antes de segmentar.

    Corrige la ligera inclinación con la que suele quedar el visor (el
    tótem rara vez se fotografía perfectamente de frente). Sin esto, la
    segmentación por proyección de columnas mezcla dígitos vecinos porque
    su tinta ya no cae en rangos de columna separados.
    """
    ink = (binary < 128).astype(np.uint8)
    ys, xs = np.where(ink > 0)
    if len(xs) < 20:
        return binary
    pts = np.column_stack([xs, ys]).astype(np.float32)
    (_, _), (rw, rh), angulo = cv2.minAreaRect(pts)
    if rw < rh:
        angulo = angulo - 90
    if abs(angulo) < 0.5 or abs(angulo) > 20:
        return binary
    center = (binary.shape[1] / 2, binary.shape[0] / 2)
    matrix = cv2.getRotationMatrix2D(center, angulo, 1.0)
    return cv2.warpAffine(
        binary, matrix, (binary.shape[1], binary.shape[0]),
        borderValue=255, flags=cv2.INTER_NEAREST,
    )


def _segment_characters(binary: np.ndarray) -> list[np.ndarray]:
    """Parte la imagen en un recorte por carácter.

    Separa la imagen binaria (fondo blanco=255, tinta negra=0) en
    sub-imágenes por carácter, usando la proyección vertical de tinta.
    """
    if binary.size == 0:
        return []
    ink = (binary < 128).astype(np.uint8)
    columns = ink.sum(axis=0)
    threshold = max(1, int(0.06 * binary.shape[0]))
    activo = columns > threshold

    bloques: list[tuple[int, int]] = []
    inicio = None
    for i, v in enumerate(activo):
        if v and inicio is None:
            inicio = i
        if not v and inicio is not None:
            bloques.append((inicio, i))
            inicio = None
    if inicio is not None:
        bloques.append((inicio, len(activo)))

    # Fusiona bloques separados por huecos minúsculos (ruido de anti-aliasing)
    fusionados: list[tuple[int, int]] = []
    for b in bloques:
        if fusionados and b[0] - fusionados[-1][1] < max(2, int(0.02 * binary.shape[1])):
            fusionados[-1] = (fusionados[-1][0], b[1])
        else:
            fusionados.append(b)

    return [binary[:, s:e] for s, e in fusionados if e - s >= 2]


def _crop_to_ink(character: np.ndarray) -> np.ndarray:
    """Ajusta el recorte del carácter a su tinta.

    Recorta el carácter a la caja delimitadora real de sus píxeles de
    tinta (filas y columnas), quitando el margen blanco sobrante que deja
    la segmentación por columnas (que solo acota en X, no en Y).
    """
    ink = character < 128
    rows = np.where(ink.any(axis=1))[0]
    cols = np.where(ink.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return character
    return character[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]


def _is_decimal_point(character: np.ndarray) -> bool:
    h, w = character.shape[:2]
    if h == 0 or w == 0:
        return False
    ink = character < 128
    filas_con_tinta = np.where(ink.any(axis=1))[0]
    if len(filas_con_tinta) == 0:
        return False
    centro_vertical = filas_con_tinta.mean() / h
    fill_ratio = ink.mean()
    return centro_vertical > 0.68 and w < h * 1.3 and fill_ratio > 0.15


_CANVAS_W, _CANVAS_H = 40, 64
_THICKNESS = 6

# Extremos (x, y) de cada uno de los 7 segmentos sobre el lienzo _CANVAS_W x _CANVAS_H.
_SEGMENT_COORDS: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    "top": ((9, 5), (31, 5)),
    "top_left": ((6, 7), (6, 30)),
    "top_right": ((34, 7), (34, 30)),
    "middle": ((9, 32), (31, 32)),
    "bottom_left": ((6, 34), (6, 57)),
    "bottom_right": ((34, 34), (34, 57)),
    "bottom": ((9, 59), (31, 59)),
}
_SEGMENT_ORDER = ["top", "top_left", "top_right", "middle", "bottom_left", "bottom_right", "bottom"]


def _draw_template(patron: tuple[int, ...]) -> np.ndarray:
    canvas = np.zeros((_CANVAS_H, _CANVAS_W), dtype=np.uint8)
    for activo, name in zip(patron, _SEGMENT_ORDER, strict=False):
        if activo:
            p1, p2 = _SEGMENT_COORDS[name]
            cv2.line(canvas, p1, p2, 255, _THICKNESS)
    return canvas


@functools.lru_cache(maxsize=1)
def _templates() -> dict[str, np.ndarray]:
    return {digit: _draw_template(patron) for patron, digit in _PATTERNS.items()}


def _classify_digit(character: np.ndarray) -> tuple[str | None, float]:
    """Decide qué dígito es un carácter, y con cuánta confianza.

    Clasifica un carácter comparando su forma (por solapamiento tipo IoU)
    contra plantillas de 7 segmentos dibujadas para cada dígito 0-9. Es más
    robusto que umbrales de densidad por zona fija, porque compara la forma
    completa en vez de decidir "encendido/apagado" segmento por segmento con
    un único punto de corte.
    """
    character = _crop_to_ink(character)
    h, w = character.shape[:2]
    if h < 4 or w < 2:
        return None, 0.0

    grid = cv2.resize(character, (_CANVAS_W, _CANVAS_H), interpolation=cv2.INTER_LINEAR)
    ink = (grid < 128).astype(np.uint8)
    ink = cv2.dilate(ink, np.ones((3, 3), np.uint8))  # tolera trazos finos

    best_digit, best_score = None, 0.0
    for digit, plantilla in _templates().items():
        plantilla_bin = (plantilla > 0).astype(np.uint8)
        intersection = np.logical_and(ink, plantilla_bin).sum()
        union_area = np.logical_or(ink, plantilla_bin).sum()
        score = intersection / union_area if union_area else 0.0
        if score > best_score:
            best_digit, best_score = digit, score

    if best_digit is not None and best_score > 0.30:
        return best_digit, min(1.0, best_score * 1.4)

    return None, 0.0


# --- Correccion de italica --------------------------------------------------------
# Los digitos de estos visores estan inclinados por diseno, como los de un reloj
# digital: no es perspectiva de la fotografia sino la tipografia del display.
# Las plantillas de comparacion son de trazos rectos, asi que sin enderezar
# antes el solapamiento se cae y se confunden los digitos que mas se parecen al
# inclinarse: el nueve con el cuatro, el cinco con el cero, el cero con el seis.
#
# Medido sobre los recortes de referencia, corregir la inclinacion lleva la
# lectura de cero digitos correctos a cuatro de cinco.
ANGULOS_ITALICA = (0, 5, 8, 10, 12, 15, 18, 20)


def _cizallar(binaria: np.ndarray, grados: float) -> np.ndarray:
    """Aplica una cizalla horizontal para enderezar los trazos inclinados."""
    if not grados:
        return binaria
    alto, ancho = binaria.shape[:2]
    k = np.tan(np.deg2rad(grados))
    matriz = np.float32([[1, k, -k * alto / 2], [0, 1, 0]])
    return cv2.warpAffine(
        binaria, matriz, (int(ancho + abs(k) * alto), alto), borderValue=255
    )


def _nitidez_de_columnas(binaria: np.ndarray) -> float:
    """Cuanto se separan los digitos entre si al proyectarlos sobre el eje x.

    Un texto enderezado deja columnas de tinta bien definidas y huecos limpios
    entre caracteres; uno inclinado las emborrona unas sobre otras. La varianza
    de esa proyeccion sirve de criterio sin necesidad de saber que dice el
    visor, que es lo que permite estimar el angulo en cualquier fotografia.
    """
    tinta = (binaria < 128).astype(np.float32)
    if tinta.size == 0:
        return 0.0
    columnas = tinta.sum(axis=0)
    return float(columnas.var())


def enderezar_italica(binaria: np.ndarray) -> tuple[np.ndarray, float]:
    """Estima la inclinacion propia del display y la corrige.

    Devuelve la imagen enderezada y el angulo aplicado. Se prueba un abanico de
    angulos y se elige el que mejor separa las columnas, en vez de fijar uno:
    distintos modelos de dispensador usan tipografias con distinta inclinacion.
    """
    mejor_angulo, mejor_nitidez, mejor_imagen = 0.0, _nitidez_de_columnas(binaria), binaria
    for grados in ANGULOS_ITALICA[1:]:
        candidata = _cizallar(binaria, grados)
        nitidez = _nitidez_de_columnas(candidata)
        if nitidez > mejor_nitidez:
            mejor_angulo, mejor_nitidez, mejor_imagen = grados, nitidez, candidata
    return mejor_imagen, mejor_angulo


class SevenSegmentReader:
    """Motor de OCR de 7 segmentos, sin dependencias externas."""

    name = "seven_segment"

    def read(self, binary: np.ndarray) -> OcrReading:
        """Lee el visor completo dígito a dígito.

        La confianza es el promedio de la de cada carácter, y se anula por
        completo si el texto no forma un número: media confianza sobre algo
        que no es un precio sigue sin ser un precio.
        """
        binary = _deskew(binary)
        binary, _ = enderezar_italica(binary)
        characters = _segment_characters(binary)
        if not characters:
            return OcrReading("", None, 0.0, self.name)

        text = ""
        confidences: list[float] = []
        for c in characters:
            if _is_decimal_point(c):
                text += "."
                confidences.append(0.8)
                continue
            digit, conf = _classify_digit(c)
            if digit is None:
                text += "?"
                confidences.append(0.0)
            else:
                text += digit
                confidences.append(conf)

        value = _text_to_value(text)
        confidence = float(np.mean(confidences)) if confidences else 0.0

        if value is None:
            # El separador es lo que mas falla. Si los digitos estan completos,
            # se recoloca por posicion antes de dar la lectura por perdida.
            recolocado, cambio = colocar_punto_por_posicion(text)
            if cambio:
                deducido = _text_to_value(recolocado)
                if deducido is not None:
                    # Se penaliza la confianza: el punto se dedujo, no se leyo.
                    return OcrReading(recolocado, deducido, confidence * 0.85, self.name)

        if value is None:
            confidence = 0.0
        return OcrReading(text, value, confidence, self.name)


class TesseractReader:
    """Motor alterno de lectura, disponible solo si está instalado.

    Motor alterno usando el binario `tesseract` (si está instalado, p.ej.
    dentro del contenedor Docker). Ver Dockerfile: apt-get install tesseract-ocr.
    """

    name = "tesseract"


    def __init__(self) -> None:
        self.binary_path = shutil.which("tesseract")
        self.disponible = self.binary_path is not None

    def read(self, binary: np.ndarray) -> OcrReading:
        """Lee el visor con el motor externo, si está instalado.

        Devuelve una lectura vacía cuando no lo está, en vez de fallar: es
        una segunda opinión opcional, no un requisito.
        """
        if not self.disponible:
            return OcrReading("", None, 0.0, self.name)
        with tempfile.TemporaryDirectory() as tmp:
            img_path = Path(tmp) / "crop.png"
            cv2.imwrite(str(img_path), binary)
            try:
                output = subprocess.run(  # noqa: S603  # argumentos propios, sin entrada externa
                    [
                        self.binary_path, str(img_path), "stdout",
                        "--psm", "7",
                        "-c", "tessedit_char_whitelist=0123456789.",
                    ],
                    capture_output=True, text=True, timeout=10,
                )
                text = output.stdout.strip()
            except Exception:
                return OcrReading("", None, 0.0, self.name)
        value = _text_to_value(text)
        return OcrReading(text, value, 0.6 if value is not None else 0.0, self.name)


def _text_to_value(text: str) -> float | None:
    limpio = text.replace(" ", "")
    if "?" in limpio or limpio.count(".") > 1:
        return None
    try:
        value = float(limpio)
    except ValueError:
        return None
    return value


# --- Colocacion del separador decimal ---------------------------------------------
# Un precio de combustible en quetzales por galon siempre lleva dos decimales.
# Esa regularidad del dominio permite recolocar el punto por posicion en vez de
# depender de que el reconocedor distinga una mancha de pocos pixeles, que es
# donde mas falla: se ha visto leer 4609 donde dice 40.09, con confianza
# suficiente para casi pasar la validacion.
#
# Solo se aplica cuando el numero de digitos es el esperado. Si no lo es, el
# problema no es el punto sino la lectura, y colocarlo daria un precio con
# aspecto correcto y valor inventado.
DIGITOS_ESPERADOS = 4
DECIMALES = 2


def colocar_punto_por_posicion(texto: str) -> tuple[str, bool]:
    """Reconstruye el separador decimal a partir del numero de digitos.

    Devuelve el texto resultante y si hizo falta recolocarlo. Un texto que ya
    trae el punto en su sitio se deja intacto.
    """
    digitos = [c for c in texto if c.isdigit()]
    if len(digitos) != DIGITOS_ESPERADOS:
        return texto, False
    esperado = "".join(digitos[:-DECIMALES]) + "." + "".join(digitos[-DECIMALES:])
    return (esperado, True) if texto != esperado else (texto, False)


def read_price(binary: np.ndarray, usar_tesseract_si_disponible: bool = True) -> OcrReading:
    """Lee un precio del visor con el mejor motor disponible.

    Punto de entrada único: intenta 7-segmentos y, si está disponible,
    compara con tesseract, quedándose con la lectura de mayor confianza.
    """
    lector_7seg = SevenSegmentReader()
    best = lector_7seg.read(binary)

    if usar_tesseract_si_disponible:
        lector_tess = TesseractReader()
        if lector_tess.disponible:
            alt = lector_tess.read(binary)
            if alt.value is not None and alt.confidence > best.confidence:
                best = alt
    return best
