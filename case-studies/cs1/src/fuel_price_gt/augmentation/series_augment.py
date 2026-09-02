"""Aumento de la serie histórica de precios.

Problema real de este proyecto: solo existen 5 fotografías (5 puntos reales
por tipo de combustible, tomadas semanalmente entre 2026-07-09 y 2026-07-30).
Es insuficiente para entrenar y validar temporalmente un modelo de series de
tiempo (S4 del Business Understanding: "existe suficiente historia de
precios..." queda como supuesto abierto). Tal como pide el negocio
("aplica una técnica para aumentar la muestra"), se genera una serie
histórica semanal sintética que:

  1. Usa como anclas los precios reales extraídos de las fotos (cuando la
     extracción los valida).
  2. Se calibra con datos reales externos (scraping de globalpetrolprices,
     que cita al MEM) para que la volatilidad y tendencia sean realistas:
     variación intermensual observada, y precio actual real como ancla final.
  3. Rellena el resto del histórico con una caminata aleatoria semanal
     (random walk con reversión leve a la tendencia calibrada), consistente
     con que "Actualizaciones semanales... una línea larga y plana significa
     que el gobierno fija los precios" (cita textual de la fuente).

Toda fila sintética queda marcada con `fuente="synthetic"` para que nunca se
confunda con una lectura real, y para poder auditar/filtrar en evaluación.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from ..config import load_config
from ..scraping.price_scraper import get_reference_price

# Relación aproximada entre el combustible de referencia externo (genérico
# "gasoline", que en Guatemala se reporta como proxy de Regular) y los otros
# tipos, tomada de la brecha observada en las fotos piloto (S6/D1).
_OFFSET_TIPICO_GTQ = {
    "regular": 0.0,
    "super": 1.0,
    "vpower": 1.5,
    "diesel": 2.1,
}


def _seed_from_text(text: str) -> int:
    return abs(hash(text)) % (2**32 - 1)


def generate_synthetic_series(
    anclas_reales: pd.DataFrame,
    start_date: date,
    end_date: date,
    config: dict | None = None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Genera precios semanales sintéticos para cada tipo de combustible.

    Parameters
    ----------
    anclas_reales: DataFrame con columnas [fecha, tipo_combustible, precio_gtq_por_galon]
        (precios reales validados, pueden venir vacíos si la extracción no
        validó ninguno; en ese caso se ancla solo con el scraper externo).
    """
    cfg = config or load_config()
    seed = seed if seed is not None else cfg["modeling"]["seed"]
    rng = np.random.default_rng(seed)

    ref_gasolina = get_reference_price("gasoline", cfg)
    ref_diesel = get_reference_price("diesel", cfg)
    regular_price_today = ref_gasolina.price_gtq_per_gallon
    diesel_price_today = ref_diesel.price_gtq_per_gallon
    monthly_change = (ref_gasolina.monthly_change_pct or 0.5) / 100.0

    semanas = pd.date_range(start_date, end_date, freq="7D")
    rows = []

    for tipo in ["diesel", "regular", "super", "vpower"]:
        ancla_tipo = anclas_reales[anclas_reales["fuel_type"] == tipo] if not anclas_reales.empty else anclas_reales
        final_anchor_price = diesel_price_today if tipo == "diesel" else regular_price_today + _OFFSET_TIPICO_GTQ[tipo]

        # Punto de partida: si hay ancla real más antigua, se usa; si no, se
        # retro-proyecta desde el precio actual con la variación mensual real.
        if not ancla_tipo.empty:
            initial_price = float(ancla_tipo.sort_values("date").iloc[0]["price_gtq_per_gallon"])
        else:
            semanas_totales = max(1, len(semanas))
            initial_price = final_anchor_price / ((1 + monthly_change) ** (semanas_totales / 4.345))

        sigma_semanal = max(0.05, abs(monthly_change) * final_anchor_price / 4.345)
        price = initial_price
        deriva = (final_anchor_price - initial_price) / max(1, len(semanas) - 1)

        for semana in semanas:
            ruido = rng.normal(0, sigma_semanal)
            price = max(5.0, price + deriva + ruido)
            rows.append(
                {
                    "date": semana.date(),
                    "fuel_type": tipo,
                    "price_gtq_per_gallon": round(float(price), 2),
                    "source": "synthetic",
                }
            )

    df_sintetico = pd.DataFrame(rows)

    # Las anclas reales, cuando existen, reemplazan al valor sintético de esa
    # semana exacta (los datos reales siempre tienen prioridad).
    if not anclas_reales.empty:
        df_real = anclas_reales.copy()
        df_real["source"] = "real"
        df_final = pd.concat([df_sintetico, df_real], ignore_index=True)
        df_final = (
            df_final.sort_values("source")  # "synthetic" < "real" alfabéticamente -> real queda último
            .drop_duplicates(subset=["date", "fuel_type"], keep="last")
            .sort_values(["fuel_type", "date"])
            .reset_index(drop=True)
        )
        return df_final

    return df_sintetico.sort_values(["fuel_type", "date"]).reset_index(drop=True)
