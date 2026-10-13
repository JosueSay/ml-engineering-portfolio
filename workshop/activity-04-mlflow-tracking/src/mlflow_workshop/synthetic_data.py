"""Generador mejorado de datos sinteticos de demanda de manzanas.

Parte del generador del tutorial de MLflow (``tutorial_data.py``) y corrige los
defectos documentados en ``docs/02_synthetic-data-review.md``. Conserva las
mismas columnas de salida para que cualquier codigo del tutorial siga sirviendo.
"""

import numpy as np
import pandas as pd

# Dias previos que se generan y se descartan, para que los rezagos (precio a 3
# dias, ventana de marketing a 7, demanda del dia anterior) nazcan con valor
# real en vez de rellenarse.
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

# Columnas intermedias: cuanto aporta cada factor a la demanda de ese dia.
COMPONENT_COLUMNS = [
    "inflation_multiplier",
    "harvest_effect",
    "stock_available",
    "price_effect",
    "seasonality_effect",
    "promo_effect",
    "weekend_effect",
    "holiday_effect",
    "rainfall_effect",
    "competitor_price_effect",
    "marketing_effect",
    "noise",
]


def generate_apple_sales_data(
    n_rows: int = 5000,
    base_demand: float = 1000.0,
    competitor_price_effect: float = -50.0,
    marketing_effect: float = 80.0,
    holiday_effect: float = 150.0,
    rainfall_effect: float = -3.0,
    annual_inflation: float = 0.03,
    noise_std: float = 50.0,
    end_date: str = "2024-12-31",
    seed: int = 9999,
    keep_components: bool = False,
) -> pd.DataFrame:
    """Genera ventas diarias de manzanas con sus variables explicativas.

    Args:
        n_rows: Cantidad de dias a generar.
        base_demand: Demanda base diaria antes de aplicar cualquier efecto.
        competitor_price_effect: Cambio en la demanda los dias en que la
            competencia vende mas barato.
        marketing_effect: Unidades de demanda que aporta una intensidad de
            marketing de 1.0.
        holiday_effect: Unidades de demanda que aporta un dia festivo.
        rainfall_effect: Cambio en la demanda por cada milimetro de lluvia.
        annual_inflation: Crecimiento anual del nivel de demanda.
        noise_std: Desviacion estandar del ruido gaussiano.
        end_date: Ultimo dia de la serie. Fijarlo hace que el resultado no
            dependa del dia en que se ejecuta.
        seed: Semilla del generador aleatorio.
        keep_components: Si es True, conserva las columnas intermedias con el
            aporte de cada factor, utiles para validar un modelo contra la verdad.

    Returns:
        DataFrame con una fila por dia, las columnas de ``FEATURE_COLUMNS`` y el
        objetivo ``demand``. ``average_temperature`` no influye en la demanda:
        es una variable de control que un buen modelo deberia ignorar.
    """
    if n_rows < 1:
        raise ValueError("n_rows debe ser al menos 1")
    if noise_std < 0:
        raise ValueError("noise_std no puede ser negativo")

    total = n_rows + WARMUP_DAYS
    # Generador local: no altera el estado global de numpy ni depende de el.
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

    # Crecimiento continuo por dias transcurridos, sin escalon cada 1 de enero.
    elapsed_years = (dates - dates[0]).days.to_numpy() / 365.25
    df["inflation_multiplier"] = 1 + annual_inflation * elapsed_years

    # Dos cosechas al ano, con maximos en marzo y septiembre. Un coseno de
    # periodo 6 meses; la suma de dos senos desfasados medio ciclo se anula.
    df["harvest_effect"] = np.cos(2 * np.pi * (month - 3) / 6)

    # En cosecha hay mas oferta y el precio baja.
    df["price_per_kg"] = rng.uniform(0.5, 3, total) - df["harvest_effect"] * 0.25
    df["competitor_price_per_kg"] = rng.uniform(0.5, 3, total)

    # Promocion fija el mes siguiente a cada maximo de cosecha, y ocasional el resto.
    df["promo"] = np.where(np.isin(month, [4, 10]), 1, rng.choice([0, 1], total, p=[0.85, 0.15]))

    # Inventario segun el precio de hace 3 dias, y marketing segun la fraccion
    # de dias con inventario alto en la ultima semana.
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
    # La inflacion escala el nivel de demanda, no el ruido.
    signal = (base_demand + df[effects].sum(axis=1)) * df["inflation_multiplier"]
    df[TARGET_COLUMN] = (signal + df["noise"]).clip(lower=0)

    # El rezago sale de la demanda final, ya con todos los efectos aplicados.
    df["previous_days_demand"] = df[TARGET_COLUMN].shift(1)

    df = df.iloc[WARMUP_DAYS:].reset_index(drop=True)
    columns = FEATURE_COLUMNS + (COMPONENT_COLUMNS if keep_components else []) + [TARGET_COLUMN]
    return df[columns]
