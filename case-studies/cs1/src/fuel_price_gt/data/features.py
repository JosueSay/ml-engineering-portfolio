"""Ingeniería de features para el dataset Gold.

Incluye variables de calendario (día de semana, fin de semana), rezagos y
medias móviles (autocorrelación de la serie de precios), y los horizontes
de predicción (1, 2 y 4 semanas, S2 del Business Understanding) como
columnas objetivo separadas — así se entrena un modelo por horizonte sin
usar información futura (requisito explícito: "evitar el uso de información
futura en el entrenamiento, validación temporal estricta, sin leakage").
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def build_features(series: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Añade a la serie las variables con las que aprende el modelo.

    Todas miran hacia atrás: rezagos, medias móviles y calendario. Ninguna
    usa información posterior a la fecha de la fila, porque eso inflaría las
    métricas con datos que en producción no existirían todavía.
    """
    horizons = config["business"]["horizon_weeks"]
    trend_threshold = config["modeling"]["trend_threshold_gtq"]

    partes = []
    for tipo, grupo in series.groupby("fuel_type"):
        g = grupo.sort_values("date").reset_index(drop=True).copy()
        g["date"] = pd.to_datetime(g["date"])

        g["day_of_week"] = g["date"].dt.dayofweek  # 0=lunes
        g["month"] = g["date"].dt.month
        g["is_weekend"] = (g["day_of_week"] >= 5).astype(int)
        g["week_of_year"] = g["date"].dt.isocalendar().week.astype(int)

        for lag in (1, 2, 3, 4):
            g[f"lag_{lag}"] = g["price_gtq_per_gallon"].shift(lag)
        g["rolling_mean_3"] = g["price_gtq_per_gallon"].shift(1).rolling(3).mean()
        g["rolling_std_3"] = g["price_gtq_per_gallon"].shift(1).rolling(3).std()
        g["recent_trend"] = g["lag_1"] - g["lag_2"]

        # Objetivos por horizonte: precio N semanas adelante, y su clase de
        # tendencia (alza/baja/estable) respecto al precio actual.
        for h in horizons:
            g[f"target_price_h{h}"] = g["price_gtq_per_gallon"].shift(-h)
            delta = g[f"target_price_h{h}"] - g["price_gtq_per_gallon"]
            g[f"target_trend_h{h}"] = np.select(
                [delta > trend_threshold, delta < -trend_threshold],
                ["up", "down"],
                default="stable",
            )

        g["fuel_type"] = tipo
        partes.append(g)

    result = pd.concat(partes, ignore_index=True)
    columnas_orden = [
        "date", "fuel_type", "price_gtq_per_gallon", "source",
        "day_of_week", "month", "is_weekend", "week_of_year",
        "lag_1", "lag_2", "lag_3", "lag_4",
        "rolling_mean_3", "rolling_std_3", "recent_trend",
    ] + [c for c in result.columns if c.startswith("target_")]
    return result[columnas_orden]


MODEL_FEATURES = [
    "day_of_week", "month", "is_weekend", "week_of_year",
    "lag_1", "lag_2", "lag_3", "lag_4",
    "rolling_mean_3", "rolling_std_3", "recent_trend",
]
