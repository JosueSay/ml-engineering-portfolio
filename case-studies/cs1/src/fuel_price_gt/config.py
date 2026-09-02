"""Acceso a la configuración del proyecto, repartida en tres niveles.

El reparto no es decorativo: define qué se versiona y qué no.

    config/config.yaml   Parámetros de negocio y de modelo. Se versiona.
    .env                 Lo que cambia por máquina o entorno. No se versiona.
    keys/                Credenciales reales, en archivos. No se versionan.

De ahí la regla que sostiene el nivel tres: `.env` nunca contiene el valor de
una credencial, solo la ruta al archivo que la guarda. Las variables sensibles
terminan en `_FILE` y se leen con `read_secret`, no con `env`. Así una
credencial no aparece en un volcado de entorno ni en un log de arranque.
"""
from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Any

import yaml

_ENV_FILE = ".env"
_ROOT_VAR = "FUEL_PRICE_GT_ROOT"
_CONFIG_VAR = "FUEL_PRICE_GT_CONFIG"
_MARCADOR = Path("config") / "config.yaml"


def _locate_root() -> Path:
    """Ubica la raíz del proyecto, la carpeta que contiene `config/config.yaml`.

    Se busca hacia arriba desde este archivo en vez de contar niveles fijos:
    al instalar el paquete de forma no editable el módulo queda bajo el
    directorio de paquetes y cualquier conteo de niveles deja de valer. Si la
    búsqueda no encuentra nada, se cae al directorio de trabajo, que es lo
    correcto dentro de un contenedor.
    """
    override = os.environ.get(_ROOT_VAR)
    if override:
        return Path(override).expanduser().resolve()

    for candidate in Path(__file__).resolve().parents:
        if (candidate / _MARCADOR).exists():
            return candidate

    current = Path.cwd()
    for candidate in [current, *current.parents]:
        if (candidate / _MARCADOR).exists():
            return candidate
    return current


def _load_env(raiz: Path) -> None:
    """Vuelca `.env` en el entorno del proceso, sin pisar lo que ya venga puesto.

    El orden importa: una variable definida de verdad en el entorno gana sobre
    el archivo. Es lo que permite que la integración continua o un contenedor
    sobreescriban un valor sin editar ningún archivo.

    Se lee a mano en vez de con una biblioteca porque el formato es una línea
    `CLAVE=valor` y no hace falta nada más; una dependencia extra en un paquete
    publicable se paga en cada instalación.
    """
    path = raiz / _ENV_FILE
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


PROJECT_ROOT = _locate_root()
_load_env(PROJECT_ROOT)

CONFIG_PATH = Path(os.environ.get(_CONFIG_VAR) or PROJECT_ROOT / _MARCADOR)


@functools.lru_cache(maxsize=1)
def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Lee la configuración una sola vez y la deja cacheada."""
    with open(Path(path) if path else CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve_path(relative: str | Path) -> Path:
    """Convierte una ruta relativa de la configuración en absoluta."""
    p = Path(relative)
    return p if p.is_absolute() else PROJECT_ROOT / p


def env(name: str, defecto: str | None = None) -> str | None:
    """Lee una variable de entorno no sensible.

    Para credenciales no se usa esta función sino `read_secret`: aquí el valor
    acabaría en cualquier traza que imprima el entorno.
    """
    return os.environ.get(name, defecto)


def env_int(name: str, defecto: int) -> int:
    """Lee una variable de entorno numérica, como un puerto."""
    value = os.environ.get(name)
    if value is None or not value.strip():
        return defecto
    try:
        return int(value)
    except ValueError:
        return defecto


def read_secret(variable_name: str) -> str | None:
    """Lee una credencial del archivo al que apunta una variable `_FILE`.

    Devuelve `None` si la variable no está declarada o el archivo no existe.
    La ausencia de una credencial es un estado válido: quien la necesita cae a
    su alternativa local en vez de fallar, y así la integración continua sigue
    corriendo en ramas sin acceso.
    """
    path = os.environ.get(variable_name)
    if not path:
        return None
    file = resolve_path(path)
    if not file.is_file():
        return None
    content = file.read_text(encoding="utf-8").strip()
    return content or None


def secret_path(variable_name: str) -> Path | None:
    """Ruta al archivo de credencial, sin leer su contenido.

    Para las interfaces que piden el archivo y no el valor. Devuelve `None` si
    no está disponible, igual que `read_secret`.
    """
    path = os.environ.get(variable_name)
    if not path:
        return None
    file = resolve_path(path)
    return file if file.is_file() else None
