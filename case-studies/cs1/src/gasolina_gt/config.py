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


def _localizar_raiz() -> Path:
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

    for candidato in Path(__file__).resolve().parents:
        if (candidato / _MARCADOR).exists():
            return candidato

    actual = Path.cwd()
    for candidato in [actual, *actual.parents]:
        if (candidato / _MARCADOR).exists():
            return candidato
    return actual


def _cargar_env(raiz: Path) -> None:
    """Vuelca `.env` en el entorno del proceso, sin pisar lo que ya venga puesto.

    El orden importa: una variable definida de verdad en el entorno gana sobre
    el archivo. Es lo que permite que la integración continua o un contenedor
    sobreescriban un valor sin editar ningún archivo.

    Se lee a mano en vez de con una biblioteca porque el formato es una línea
    `CLAVE=valor` y no hace falta nada más; una dependencia extra en un paquete
    publicable se paga en cada instalación.
    """
    ruta = raiz / _ENV_FILE
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave = clave.strip()
        valor = valor.strip().strip('"').strip("'")
        if clave and clave not in os.environ:
            os.environ[clave] = valor


PROJECT_ROOT = _localizar_raiz()
_cargar_env(PROJECT_ROOT)

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


def env(nombre: str, defecto: str | None = None) -> str | None:
    """Lee una variable de entorno no sensible.

    Para credenciales no se usa esta función sino `read_secret`: aquí el valor
    acabaría en cualquier traza que imprima el entorno.
    """
    return os.environ.get(nombre, defecto)


def env_int(nombre: str, defecto: int) -> int:
    """Lee una variable de entorno numérica, como un puerto."""
    valor = os.environ.get(nombre)
    if valor is None or not valor.strip():
        return defecto
    try:
        return int(valor)
    except ValueError:
        return defecto


def read_secret(nombre_variable: str) -> str | None:
    """Lee una credencial del archivo al que apunta una variable `_FILE`.

    Devuelve `None` si la variable no está declarada o el archivo no existe.
    La ausencia de una credencial es un estado válido: quien la necesita cae a
    su alternativa local en vez de fallar, y así la integración continua sigue
    corriendo en ramas sin acceso.
    """
    ruta = os.environ.get(nombre_variable)
    if not ruta:
        return None
    archivo = resolve_path(ruta)
    if not archivo.is_file():
        return None
    contenido = archivo.read_text(encoding="utf-8").strip()
    return contenido or None


def secret_path(nombre_variable: str) -> Path | None:
    """Ruta al archivo de credencial, sin leer su contenido.

    Para las interfaces que piden el archivo y no el valor. Devuelve `None` si
    no está disponible, igual que `read_secret`.
    """
    ruta = os.environ.get(nombre_variable)
    if not ruta:
        return None
    archivo = resolve_path(ruta)
    return archivo if archivo.is_file() else None
