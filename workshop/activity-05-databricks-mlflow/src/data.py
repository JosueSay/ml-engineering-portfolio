"""Modulo de datos para el pipeline de prediccion de demanda."""

from __future__ import annotations

import numpy as np
import pandas as pd

WARMUP_DAYS = 7

FEATURE_COLUMNS = [
    "date",
    "average_temperature",
    "rainfall",
    "weekend",
    "holiday",
    "price_per_kg",
    "promo",
    "previous_days_demand",
    "competitor_price_per_kg",
    "marketing_intensity",
]
TARGET_COLUMN = "demand"


def generate_demand_dataset(
    n_rows: int = 3000,
    base_demand: float = 1000.0,
    competitor_price_effect: float = -50.0,
    marketing_effect: float = 80.0,
    holiday_effect: float = 150.0,
    rainfall_effect: float = -3.0,
    annual_inflation: float = 0.03,
    noise_std: float = 50.0,
    end_date: str = "2025-12-31",
    seed: int = 42,
) -> pd.DataFrame:
    """Genera datos sinteticos realistas de demanda diaria y factores economicos.

    Args:
        n_rows: Cantidad de observaciones diarias a generar.
        base_demand: Demanda media de referencia.
        competitor_price_effect: Impacto cuando el competidor tiene menor precio.
        marketing_effect: Impacto de campañas de marketing.
        holiday_effect: Aumento de demanda en dias festivos.
        rainfall_effect: Variacion de demanda por precipitaciones.
        annual_inflation: Tasa de inflacion anual.
        noise_std: Desviacion del componente aleatorio.
        end_date: Fecha final de la serie temporal.
        seed: Semilla de reproducibilidad.

    Returns:
        pd.DataFrame con variables predictoras y columna objetivo 'demand'.
    """
    total = n_rows + WARMUP_DAYS
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp(end_date), periods=total, freq="D")
    month = dates.month.to_numpy()

    df = pd.DataFrame({
        "date": dates,
        "average_temperature": rng.uniform(10, 35, total),
        "rainfall": rng.exponential(5, total),
        "weekend": (dates.dayofweek >= 5).astype(int),
        "holiday": rng.choice([0, 1], total, p=[0.97, 0.03]),
    })

    elapsed_years = (dates - dates[0]).days.to_numpy() / 365.25
    df["inflation_multiplier"] = 1 + annual_inflation * elapsed_years

    # Estacionalidad bianual
    df["harvest_effect"] = np.cos(2 * np.pi * (month - 3) / 6)
    df["price_per_kg"] = rng.uniform(0.5, 3, total) - df["harvest_effect"] * 0.25
    df["competitor_price_per_kg"] = rng.uniform(0.5, 3, total)

    df["promo"] = np.where(np.isin(month, [4, 10]), 1, rng.choice([0, 1], total, p=[0.85, 0.15]))

    df["stock_available"] = np.clip(2 - np.log(df["price_per_kg"].shift(3) + 1), 0.7, 1)
    high_stock_share = (df["stock_available"] > 0.95).astype(float).rolling(7, min_periods=1).mean()
    df["marketing_intensity"] = np.clip(
        0.15 + 0.7 * high_stock_share + rng.normal(0, 0.05, total), 0, 1
    )

    df["price_effect"] = -50 * df["price_per_kg"]
    df["seasonality_effect"] = 50 * df["harvest_effect"]
    df["promo_effect"] = 200 * df["promo"]
    df["weekend_effect"] = 300 * df["weekend"]
    df["holiday_effect"] = holiday_effect * df["holiday"]
    df["rainfall_effect"] = rainfall_effect * df["rainfall"]
    df["competitor_price_effect"] = competitor_price_effect * (
        df["competitor_price_per_kg"] < df["price_per_kg"]
    )
    df["marketing_effect"] = marketing_effect * df["marketing_intensity"]
    df["noise"] = rng.normal(0, noise_std, total)

    effects = [
        "price_effect",
        "seasonality_effect",
        "promo_effect",
        "weekend_effect",
        "holiday_effect",
        "rainfall_effect",
        "competitor_price_effect",
        "marketing_effect",
    ]
    signal = (base_demand + df[effects].sum(axis=1)) * df["inflation_multiplier"]
    df[TARGET_COLUMN] = (signal + df["noise"]).clip(lower=0)
    df["previous_days_demand"] = df[TARGET_COLUMN].shift(1)

    df = df.iloc[WARMUP_DAYS:].reset_index(drop=True)
    return df[FEATURE_COLUMNS + [TARGET_COLUMN]]
