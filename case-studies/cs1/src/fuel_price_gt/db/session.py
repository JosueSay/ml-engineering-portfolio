"""Conexión a la base de datos.

El motor embebido por defecto es un archivo, así que no hace falta levantar
ningún servicio para trabajar: el pipeline corre igual en una máquina limpia,
en la integración continua y en un servidor modesto.

La cadena de conexión sale de `DATABASE_URL`. Cambiar a un motor servidor es
cambiar esa variable y nada más, porque el resto del código habla con
repositorios y no con el motor.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from ..config import PROJECT_ROOT, env
from .models import Base

_DEFAULT_URL = "sqlite+pysqlite:///data/fuel-prices.db"


def database_url() -> str:
    """Cadena de conexión, con la ruta del archivo resuelta a absoluta.

    Una ruta relativa dentro de la cadena se interpretaría respecto del
    directorio desde el que se ejecuta, y entonces el mismo comando lanzado
    desde dos sitios distintos trabajaría contra dos bases distintas sin avisar.
    """
    url = env("DATABASE_URL", _DEFAULT_URL) or _DEFAULT_URL
    prefijo, sep, resto = url.partition(":///")
    if not sep or resto.startswith("/") or ":memory:" in resto:
        return url
    return f"{prefijo}:///{(PROJECT_ROOT / resto).resolve()}"


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Motor de conexión, creado una sola vez por proceso."""
    url = database_url()
    if url.startswith("sqlite"):
        destino = url.partition(":///")[2]
        if destino and destino != ":memory:":
            Path(destino).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url, future=True)

    if url.startswith("sqlite"):
        # El motor embebido no aplica las claves foráneas salvo que se le pida
        # en cada conexión. Sin esto, el linaje se puede romper en silencio:
        # una lectura podría apuntar a una imagen que ya no existe.
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record):  # noqa: ANN001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_schema() -> None:
    """Crea las tablas que falten. Es idempotente."""
    Base.metadata.create_all(get_engine())


@contextmanager
def session_scope() -> Iterator[Session]:
    """Sesión con confirmación al salir y vuelta atrás si algo falla.

    Un fallo a mitad de la escritura de una corrida dejaría un linaje
    incompleto, que es peor que no tener corrida: parecería que se procesó todo
    cuando no fue así.
    """
    fabrica = sessionmaker(bind=get_engine(), expire_on_commit=False)
    sesion = fabrica()
    try:
        yield sesion
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()
