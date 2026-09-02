"""Construcción de las capas de datos, de la extracción al conjunto final.

Pipeline de datos: Bronze (extracción cruda) -> Silver (tabla limpia) ->
Gold (dataset con historia sintética + features, listo para modelar).

Sigue la arquitectura de capas mencionada en el Business Understanding
("arquitectura Bronze/Silver/Gold", recurso clave N2).
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import pandas as pd

from ..augmentation.series_augment import generate_synthetic_series
from ..config import load_config, resolve_path
from ..extraction.extractor import PriceExtractor
from .features import build_features

logger = logging.getLogger(__name__)


def build_silver(config: dict | None = None) -> pd.DataFrame:
    """Construye la capa Silver a partir de la extracción.

    Ejecuta la extracción sobre datos/ y devuelve solo las lecturas
    válidas (que pasaron el umbral de confianza y el rango plausible) como
    tabla limpia: fecha (real, EXIF), tipo_combustible, precio.
    """
    cfg = config or load_config()
    extractor = PriceExtractor(cfg)
    records = extractor.process_directory()
    extractor.save_bronze(records)

    rows = []
    for r in records:
        if r.captured_at is None:
            continue
        date = datetime.fromisoformat(r.captured_at).date()
        for reading in r.readings:
            if reading.is_valid:
                rows.append(
                    {
                        "date": date,
                        "fuel_type": reading.fuel_type,
                        "price_gtq_per_gallon": reading.price_gtq_per_gallon,
                        "confidence": reading.confidence,
                        "source_file": r.file,
                    }
                )
    df = pd.DataFrame(rows, columns=["date", "fuel_type", "price_gtq_per_gallon", "confidence", "source_file"])

    silver_dir = resolve_path(cfg["paths"]["silver"])
    silver_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(silver_dir / cfg["files"]["silver"], index=False)
    logger.info("Silver: %d lecturas reales válidas de %d imágenes", len(df), len(records))
    return df


def build_gold(
    df_silver: pd.DataFrame | None = None,
    config: dict | None = None,
    end_date: date | None = None,
) -> pd.DataFrame:
    """Construye la capa Gold, lista para modelar.

    Combina anclas reales + serie sintética calibrada, y agrega las
    features de modelado (lags, medias móviles, calendario).
    """
    cfg = config or load_config()
    df_silver = df_silver if df_silver is not None else build_silver(cfg)

    end_date = end_date or date.today()
    if not df_silver.empty:
        start_date = min(df_silver["date"]) - timedelta(weeks=8)
    else:
        start_date = end_date - timedelta(weeks=cfg["modeling"]["synthetic_history_weeks"])

    series = generate_synthetic_series(df_silver, start_date, end_date, cfg)
    gold = build_features(series, cfg)

    gold_dir = resolve_path(cfg["paths"]["gold"])
    gold_dir.mkdir(parents=True, exist_ok=True)
    gold.to_csv(gold_dir / cfg["files"]["gold"], index=False)
    logger.info("Gold: %d filas (%d reales, %d sintéticas)", len(gold), (gold["source"] == "real").sum(), (gold["source"] == "synthetic").sum())
    return gold


def load_gold_if_exists(config: dict | None = None) -> pd.DataFrame | None:
    """Lee el conjunto de modelado ya construido, o `None` si no está.

    Permite entrenar sin repetir la extracción, que es la etapa cara: leer
    todas las fotografías de nuevo para probar un hiperparámetro no aporta
    nada.
    """
    cfg = config or load_config()
    path = resolve_path(cfg["paths"]["gold"]) / cfg["files"]["gold"]
    if not path.exists():
        return None
    return pd.read_csv(path, parse_dates=["date"])
