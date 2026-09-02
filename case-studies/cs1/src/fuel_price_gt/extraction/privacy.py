"""Filtro de privacidad sobre las fotos de tótem/dispensor.

El Business Understanding es explícito: "el sistema no debe almacenar placas
de vehículos ni rostros de personas que aparezcan de fondo en la fotografía
de la gasolinera". Este módulo aplica un desenfoque best-effort sobre caras
detectadas antes de que cualquier imagen se persista en `datos_procesados/`.

Nota: `opencv-python-headless` no siempre trae empaquetados los clasificadores
Haar; si no están disponibles en el entorno, se degrada de forma segura
(no se cae el pipeline) y se deja constancia en el resultado.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class PrivacyResult:
    """Imagen ya tratada, con cuántas caras se difuminaron.

    `filtro_disponible` en falso significa que la instalación de la
    biblioteca de visión no traía el detector, no que la fotografía no
    tuviera caras. La diferencia importa para saber si una corrida cumplió
    de verdad el requisito de privacidad.
    """
    image: np.ndarray
    blurred_faces: int
    filter_available: bool


def _load_face_detector():
    if not hasattr(cv2, "CascadeClassifier"):
        # Build de OpenCV sin módulo objdetect (p.ej. algunas ruedas
        # headless mínimas). Se degrada sin romper el pipeline.
        return None
    try:
        path = f"{cv2.data.haarcascades}haarcascade_frontalface_default.xml"
        clasificador = cv2.CascadeClassifier(path)
    except Exception:
        return None
    if clasificador.empty():
        return None
    return clasificador


_DETECTOR = _load_face_detector()


def apply_privacy_filter(rgb_image: np.ndarray) -> PrivacyResult:
    """Difumina las caras que aparezcan de fondo antes de procesar.

    El requisito es no almacenar rostros de personas ajenas al negocio que
    aparezcan por casualidad en la fotografía de la gasolinera. Se aplica
    antes que nada para que ninguna etapa posterior llegue a ver la imagen
    sin tratar.
    """
    if _DETECTOR is None:
        return PrivacyResult(rgb_image, 0, filter_available=False)

    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    faces = _DETECTOR.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    output = rgb_image.copy()
    for (x, y, w, h) in faces:
        region = output[y : y + h, x : x + w]
        output[y : y + h, x : x + w] = cv2.GaussianBlur(region, (51, 51), 0)

    return PrivacyResult(output, len(faces), filter_available=True)
