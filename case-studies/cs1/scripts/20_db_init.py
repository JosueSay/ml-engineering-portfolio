"""Crea el esquema de la base de datos y muestra su estado.

Es idempotente: crea lo que falte y deja intacto lo que ya está, así que se
puede ejecutar en cada arranque sin comprobar antes si hace falta.

No borra nada. Vaciar la base es una operación aparte y deliberada, porque
perder el linaje significa perder la respuesta a por qué un precio vale lo que
vale.
"""
from __future__ import annotations

from sqlalchemy import func, inspect, select

from fuel_price_gt.db import (
    ExtractionRun,
    GoldRow,
    Image,
    ImageCrop,
    PriceReading,
    SilverPrice,
    TrainedModel,
    create_schema,
    database_url,
    get_engine,
    session_scope,
)

TABLAS = [
    ("image", Image, "fotografias ingeridas"),
    ("image_crop", ImageCrop, "recortes de la franja de precios"),
    ("extraction_run", ExtractionRun, "pasadas de extraccion"),
    ("price_reading", PriceReading, "lecturas, validas e invalidas"),
    ("silver_price", SilverPrice, "precios limpios y fechados"),
    ("gold_row", GoldRow, "filas del conjunto de modelado"),
    ("trained_model", TrainedModel, "modelos entrenados"),
]


def main() -> int:
    """Asegura el esquema e informa de cuántas filas hay en cada tabla."""
    print()
    print(f"Base de datos: {database_url()}")

    existentes = set(inspect(get_engine()).get_table_names())
    create_schema()
    creadas = set(inspect(get_engine()).get_table_names()) - existentes

    print(f"  tablas creadas ahora: {len(creadas)}" if creadas else "  el esquema ya estaba completo")
    print()

    with session_scope() as sesion:
        for nombre, modelo, descripcion in TABLAS:
            total = sesion.scalar(select(func.count()).select_from(modelo)) or 0
            marca = "nueva" if nombre in creadas else ""
            print(f"  {nombre:16} {total:>7}  {descripcion} {marca}")

        validas = sesion.scalar(
            select(func.count()).select_from(PriceReading).where(PriceReading.is_valid)
        ) or 0
        lecturas = sesion.scalar(select(func.count()).select_from(PriceReading)) or 0

    if lecturas:
        print()
        print(f"  lecturas validas: {validas} de {lecturas}")
        if validas == 0:
            print("  ninguna lectura valida: el conjunto de modelado sera sintetico")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
