"""Preparación de la imagen del panel antes de leer los dígitos.

Preprocesamiento OpenCV: localizar el visor LCD dentro de un panel y
dejarlo listo (binarizado, contraste realzado) para el OCR de dígitos.

Corresponde a la etapa "Preprocesamiento de imagen con OpenCV (contraste,
filtros morfológicos)" descrita en el Business Understanding, sección
Enfoque de modelado / Herramientas y técnicas.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class DisplayCrop:
    """Visor aislado del resto del panel.

    `encontrado_automaticamente` distingue si el visor se localizó por sus
    características o si se cayó al recorte calibrado. Sin ese dato no se
    puede separar un fallo de localización de un fallo de lectura al analizar
    los rechazos.
    """
    binary_gray_image: np.ndarray
    original_crop_image: np.ndarray
    auto_detected: bool


def locate_display(panel_rgb: np.ndarray) -> DisplayCrop:
    """Aísla el visor dentro del recorte del panel.

    Dentro del recorte (generoso) de un panel de precio, ubica el
    rectángulo retroiluminado del visor LCD (blanco/azulado, alto brillo,
    bajo-moderada saturación) mediante un umbral HSV + contornos.

    Si no se encuentra un candidato plausible, cae a una caja relativa fija
    (banda superior-centrada del panel) para nunca fallar duro — coherente
    con el riesgo R6 del negocio (falla de lectura por reflejos/parpadeo).
    """
    h, w = panel_rgb.shape[:2]
    hsv = cv2.cvtColor(panel_rgb, cv2.COLOR_RGB2HSV)
    banda_superior = hsv[: int(h * 0.72), :]

    mask = cv2.inRange(banda_superior, (0, 0, 140), (180, 120, 255))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 9), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    for c in cnts:
        x, y, cw, ch = cv2.boundingRect(c)
        if ch == 0:
            continue
        aspecto = cw / ch
        area = cw * ch
        if 1.5 < aspecto < 5.0 and area > 0.012 * w * h:
            if best is None or area > best[4]:
                best = (x, y, cw, ch, area)

    encontrado = best is not None
    if best is None:
        x, y = int(w * 0.10), int(h * 0.08)
        cw, ch = int(w * 0.80), int(h * 0.32)
    else:
        x, y, cw, ch, _ = best
        pad = int(0.15 * ch)
        x, y = max(0, x - pad), max(0, y - pad)
        cw, ch = min(w - x, cw + 2 * pad), min(h - y, ch + 2 * pad)

    crop = panel_rgb[y : y + ch, x : x + cw]
    crop = _crop_to_display_interior(crop)
    binary = _binarize_for_ocr(crop)
    return DisplayCrop(binary, crop, encontrado)


def _crop_to_display_interior(recorte_rgb: np.ndarray) -> np.ndarray:
    """Descarta el bisel y deja solo el área iluminada del visor.

    Segunda pasada: dentro del recorte (que puede incluir el bisel negro
    del visor por el margen añadido), ubica de nuevo la región retroiluminada
    y recorta exactamente a su caja, sin margen — así el bisel oscuro no
    contamina la segmentación de caracteres.
    """
    h, w = recorte_rgb.shape[:2]
    if h < 4 or w < 4:
        return recorte_rgb
    hsv = cv2.cvtColor(recorte_rgb, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, (0, 0, 140), (180, 120, 255))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return recorte_rgb
    x, y, cw, ch = cv2.boundingRect(max(cnts, key=cv2.contourArea))
    if cw * ch < 0.25 * w * h:
        return recorte_rgb
    margin = max(1, int(0.04 * ch))
    x0, y0 = max(0, x + margin), max(0, y + margin)
    x1, y1 = min(w, x + cw - margin), min(h, y + ch - margin)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return recorte_rgb
    return recorte_rgb[y0:y1, x0:x1]


def _binarize_for_ocr(recorte_rgb: np.ndarray) -> np.ndarray:
    if recorte_rgb.size == 0:
        return np.zeros((10, 10), dtype=np.uint8)
    gray = cv2.cvtColor(recorte_rgb, cv2.COLOR_RGB2GRAY)
    # Sobre-muestreo: los dígitos de 7 segmentos ganan mucho con más resolución.
    factor = max(1, int(300 / max(1, gray.shape[0])))
    if factor > 1:
        gray = cv2.resize(gray, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC)
    gray = cv2.bilateralFilter(gray, 7, 40, 40)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Los dígitos LCD suelen ser oscuros sobre fondo claro; si quedó invertido
    # (mayoría de píxeles oscuros), se voltea para estandarizar dígito=negro.
    if (binary == 0).mean() > 0.6:
        binary = 255 - binary
    return _remove_edge_blobs(binary)


def _remove_edge_blobs(binary: np.ndarray) -> np.ndarray:
    """Limpia los restos de bisel en las esquinas del recorte.

    El recorte del visor rara vez queda perfectamente rectangular (el
    tótem se fotografía con cierta inclinación), así que quedan triángulos
    de bisel/fondo oscuro en las esquinas. En vez de perseguir ese borde
    irregular, se ubica el componente BLANCO más grande (el fondo
    retroiluminado del visor), se calcula su envolvente convexa, y todo lo
    que quede fuera de esa envolvente se fuerza a blanco. Los dígitos (negros)
    quedan intactos porque son "huecos" dentro del componente blanco, no
    tocan el borde de la envolvente.
    """
    background = (binary > 128).astype(np.uint8)
    n, etiquetas, stats, _ = cv2.connectedComponentsWithStats(background, connectivity=4)
    if n <= 1:
        return binary
    idx_mayor = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    componente = (etiquetas == idx_mayor).astype(np.uint8)
    cnts, _ = cv2.findContours(componente, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return binary
    hull = cv2.convexHull(max(cnts, key=cv2.contourArea))
    mascara_hull = np.zeros_like(binary)
    cv2.fillConvexPoly(mascara_hull, hull, 255)  # type: ignore[arg-type]
    limpio = binary.copy()
    limpio[mascara_hull == 0] = 255
    return limpio
