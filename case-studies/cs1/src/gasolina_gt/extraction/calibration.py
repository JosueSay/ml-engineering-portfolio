"""Calibración de las regiones de panel de precio.

La ruta del archivo se declara en config/config.yaml (paths.calibracion), no
se arma aquí: es configuración, no una constante del código.

Contexto: con solo 5 fotos piloto del mismo dispensor Shell, entrenar un
detector de objetos (Vision Transformer / YOLO, como plantea el Business
Understanding) no es viable ni justificable. En su lugar se usa una
calibración manual validada visualmente sobre las 5 fotos (dos perfiles de
encuadre distintos), y se deja documentado el camino de escalamiento: cuando
existan más fotos (S8), esta calibración fija se reemplaza por un detector
entrenado. Ver decisiones abiertas D1/D3 y riesgo R1 del business understanding.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..config import load_config, resolve_path


def ruta_calibracion() -> Path:
    """Resuelve la ruta del archivo de calibración desde la configuración."""
    return resolve_path(load_config()["paths"]["calibracion"])

BoundingBoxFraccional = tuple[float, float, float, float]


class CalibracionPaneles:
    """Dice en qué parte del encuadre cae el panel de cada combustible.

    Las regiones se guardan como fracciones del tamaño de la imagen, no como
    píxeles, para que la misma calibración sirva a cualquier resolución.

    Cada fotografía se asigna a un perfil de encuadre; las que no estén
    asignadas usan el perfil por defecto. Es una solución de arranque válida
    mientras el conjunto es pequeño y homogéneo: con fotografías de varios
    años y encuadres distintos hay que detectar el panel en vez de suponer
    dónde está, y esta calibración pasa a ser el respaldo.
    """
    def __init__(self, path: Path | str | None = None):
        path = path or ruta_calibracion()
        with open(path, encoding="utf-8") as fh:
            self._data = json.load(fh)
        self.perfiles: dict[str, dict[str, BoundingBoxFraccional | None]] = self._data["perfiles"]
        self.asignacion: dict[str, str] = self._data["asignacion_por_archivo"]
        self.perfil_por_defecto: str = self._data["perfil_por_defecto_para_imagenes_nuevas"]

    def perfil_para(self, nombre_archivo: str) -> str:
        """Perfil de encuadre asignado a una fotografía."""
        return self.asignacion.get(nombre_archivo, self.perfil_por_defecto)

    def cajas_para(self, nombre_archivo: str) -> dict[str, BoundingBoxFraccional | None]:
        """Regiones de todos los combustibles, en fracciones del encuadre."""
        perfil = self.perfil_para(nombre_archivo)
        return self.perfiles[perfil]

    def caja_absoluta(
        self, nombre_archivo: str, combustible: str, ancho: int, alto: int
    ) -> tuple[int, int, int, int] | None:
        """Región de un combustible en píxeles, para el tamaño dado.

        Devuelve `None` cuando ese panel no cabe en el encuadre, que es
        distinto de que la lectura falle: no hay nada que leer.
        """
        caja = self.cajas_para(nombre_archivo).get(combustible)
        if caja is None:
            return None
        x0, y0, x1, y1 = caja
        return int(x0 * ancho), int(y0 * alto), int(x1 * ancho), int(y1 * alto)
