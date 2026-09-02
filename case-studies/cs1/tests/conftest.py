"""Configuración común de las pruebas.

Lo que resuelve, y no es menor: sin esto las pruebas escriben en la base de
datos real del proyecto. Una corrida de pruebas dejaría modelos y filas
inventadas mezclados con los datos de verdad, y nadie sabría cuáles son cuáles.

Además hace que las pruebas no dependan de que alguien haya inicializado la
base antes. En una máquina donde ya existía, el fallo quedaba oculto; en una
limpia —como la de integración continua— salta.
"""
from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(scope="session", autouse=True)
def base_de_pruebas(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """Redirige la base a un archivo temporal durante toda la sesión.

    Se aplica a todas las pruebas sin que tengan que pedirlo: el aislamiento no
    puede depender de que cada una se acuerde de solicitarlo.

    La caché del motor se limpia a ambos lados porque se resuelve una sola vez
    por proceso: sin limpiarla, la redirección llegaría tarde o se quedaría
    puesta después.
    """
    from fuel_price_gt.db.session import create_schema, get_engine

    ruta = tmp_path_factory.mktemp("db") / "pruebas.db"
    anterior = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{ruta}"

    get_engine.cache_clear()
    create_schema()
    try:
        yield
    finally:
        get_engine.cache_clear()
        if anterior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = anterior
