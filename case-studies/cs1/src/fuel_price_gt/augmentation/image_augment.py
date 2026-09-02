"""Aumento de datos de imagen para la etapa de extracción por visión.

Con solo 5 fotografías piloto no hay margen para medir cuán robusto es el
extractor ante variaciones de iluminación, ángulo o ruido de cámara — algo
que el propio Business Understanding anticipa como riesgo (R6: "Falla de
lectura por resplandor del sol, paneles LED parpadeantes o mala calidad de
imagen"). Este módulo genera variantes sintéticas de cada imagen real
(rotación leve, brillo/contraste, ruido gaussiano y jitter de perspectiva)
para ampliar la muestra usada en las pruebas de robustez del extractor
(ver tests/integration/test_extraccion_robustez.py).
"""
from __future__ import annotations

import cv2
import numpy as np


def _rotate(img: np.ndarray, grados: float) -> np.ndarray:
    h, w = img.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), grados, 1.0)
    return cv2.warpAffine(img, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)


def _brightness_contrast(img: np.ndarray, brillo: float, contraste: float) -> np.ndarray:
    out = img.astype(np.float32) * contraste + (brillo - 1.0) * 128
    return np.clip(out, 0, 255).astype(np.uint8)


def _gaussian_noise(img: np.ndarray, sigma: float, rng: np.random.Generator) -> np.ndarray:
    ruido = rng.normal(0, sigma, img.shape)
    return np.clip(img.astype(np.float32) + ruido, 0, 255).astype(np.uint8)


def _perspective_jitter(img: np.ndarray, max_px: int, rng: np.random.Generator) -> np.ndarray:
    h, w = img.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = src + rng.uniform(-max_px, max_px, src.shape).astype(np.float32)
    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)


def generate_variants(rgb_image: np.ndarray, n: int, config: dict, seed: int = 0) -> list[np.ndarray]:
    """Genera variantes de una imagen para ampliar el conjunto.

    Genera `n` variantes aumentadas de una imagen (recorte de panel o
    imagen completa), combinando rotación, brillo/contraste, ruido y
    perspectiva según los rangos definidos en config/config.yaml.
    """
    aug_cfg = config["augmentation"]
    rng = np.random.default_rng(seed)
    variantes = []
    for _ in range(n):
        out = rgb_image.copy()
        grados = rng.uniform(-aug_cfg["max_rotation_degrees"], aug_cfg["max_rotation_degrees"])
        out = _rotate(out, grados)
        brillo = rng.uniform(*aug_cfg["brightness_range"])
        contraste = rng.uniform(*aug_cfg["contrast_range"])
        out = _brightness_contrast(out, brillo, contraste)
        out = _gaussian_noise(out, aug_cfg["gaussian_noise_sigma"], rng)
        out = _perspective_jitter(out, aug_cfg["perspective_jitter_px"], rng)
        variantes.append(out)
    return variantes
