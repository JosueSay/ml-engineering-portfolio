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


def calibration_path() -> Path:
    """Resuelve la ruta del archivo de calibración desde la configuración."""
    return resolve_path(load_config()["paths"]["calibration"])

FractionalBoundingBox = tuple[float, float, float, float]


class PanelCalibration:
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
        path = path or calibration_path()
        with open(path, encoding="utf-8") as fh:
            self._data = json.load(fh)
        self.profiles: dict[str, dict[str, FractionalBoundingBox | None]] = self._data["profiles"]
        self.assignment: dict[str, str] = self._data["assignment_by_file"]
        self.default_profile: str = self._data["default_profile_for_new_images"]

    def profile_for(self, file_name: str) -> str:
        """Perfil de encuadre asignado a una fotografía."""
        return self.assignment.get(file_name, self.default_profile)

    def boxes_for(self, file_name: str) -> dict[str, FractionalBoundingBox | None]:
        """Regiones de todos los combustibles, en fracciones del encuadre."""
        profile = self.profile_for(file_name)
        return self.profiles[profile]

    def absolute_box(
        self, file_name: str, fuel: str, width: int, height: int
    ) -> tuple[int, int, int, int] | None:
        """Región de un combustible en píxeles, para el tamaño dado.

        Devuelve `None` cuando ese panel no cabe en el encuadre, que es
        distinto de que la lectura falle: no hay nada que leer.
        """
        box = self.boxes_for(file_name).get(fuel)
        if box is None:
            return None
        x0, y0, x1, y1 = box
        return int(x0 * width), int(y0 * height), int(x1 * width), int(y1 * height)
