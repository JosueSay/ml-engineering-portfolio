"""Carga de configuración centralizada del proyecto (config/config.yaml)."""
from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Any

import yaml


def _detectar_project_root() -> Path:
    """Ubica la raíz del proyecto (donde vive config/config.yaml).

    En un checkout editable, src/gasolina_gt/config.py cuelga directamente
    de la raíz (parents[2]). Una vez el paquete se instala de forma no
    editable (como en la imagen de Docker), el archivo termina bajo
    site-packages y esa suposición ya no aplica, así que se recurre al
    directorio de trabajo actual (WORKDIR en el contenedor)."""
    override = os.environ.get("GASOLINA_GT_ROOT")
    if override:
        return Path(override)
    candidato = Path(__file__).resolve().parents[2]
    if (candidato / "config" / "config.yaml").exists():
        return candidato
    return Path.cwd()


PROJECT_ROOT = _detectar_project_root()
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


@functools.lru_cache(maxsize=1)
def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Lee config/config.yaml una sola vez (cacheado) y devuelve un dict."""
    cfg_path = Path(path) if path else CONFIG_PATH
    with open(cfg_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve_path(relative: str) -> Path:
    """Convierte una ruta relativa del config (o cualquier string) en absoluta
    respecto a la raíz del proyecto."""
    p = Path(relative)
    return p if p.is_absolute() else PROJECT_ROOT / p
