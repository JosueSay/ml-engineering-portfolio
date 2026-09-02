"""Persistencia y linaje.

La base de datos es la fuente de verdad; los archivos tabulares que producen
las etapas son exportaciones. La diferencia importa: un CSV no puede responder
de qué fotografía salió un precio, y esa pregunta es el eje del caso.
"""
from .lineage import Lineage, lineage_coverage, trace_gold_row, trace_price
from .models import (
    Base,
    ExtractionRun,
    GoldRow,
    Image,
    ImageCrop,
    PriceReading,
    SilverPrice,
    TrainedModel,
)
from .repositories import (
    already_extracted,
    config_fingerprint,
    get_or_create_image,
    record_trained_model,
    replace_gold,
    save_extraction,
    upsert_crop,
    upsert_silver_price,
    valid_readings,
)
from .session import create_schema, database_url, get_engine, session_scope

__all__ = [
    "Base",
    "already_extracted",
    "ExtractionRun",
    "GoldRow",
    "Image",
    "ImageCrop",
    "Lineage",
    "PriceReading",
    "SilverPrice",
    "TrainedModel",
    "config_fingerprint",
    "create_schema",
    "database_url",
    "get_engine",
    "get_or_create_image",
    "lineage_coverage",
    "record_trained_model",
    "replace_gold",
    "save_extraction",
    "session_scope",
    "trace_gold_row",
    "trace_price",
    "upsert_crop",
    "upsert_silver_price",
    "valid_readings",
]
