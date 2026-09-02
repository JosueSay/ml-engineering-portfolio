"""Regla de negocio que convierte un pronóstico en una recomendación clara."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from ..config import load_config
from ..data.features import MODEL_FEATURES
from ..modeling.training import load_model


@dataclass
class Recommendation:
    """Consejo de carga con el razonamiento que lo sostiene.

    Se devuelve el porqué junto al qué: una recomendación sin justificación
    no es accionable para quien decide si llena el tanque hoy o espera.
    """
    refuel_now: bool
    decision: str
    reason: str
    fuel: str
    horizon_weeks: int
    current_price_gtq_per_gallon: float
    estimated_price_gtq_per_gallon: float
    estimated_difference_gtq: float
    trend: str
    data_date: str
    hour_context: str
    warning: str | None


def recommend_refuel(
    gold: pd.DataFrame,
    fuel: str | None = None,
    horizon: int = 1,
    hour: int | None = None,
    config: dict | None = None,
) -> Recommendation:
    """Devuelve ``recargar_ahora`` según el cambio estimado del precio.

    La hora aporta contexto operativo (horas de tráfico), no se usa como una
    causa del precio: los datos disponibles son semanales y no sostienen una
    inferencia de variación intradía.
    """
    cfg = config or load_config()
    fuel = fuel or cfg["business"]["main_fuel"]
    hour = datetime.now().hour if hour is None else hour
    if not 0 <= hour <= 23:
        raise ValueError("La hora debe estar entre 0 y 23.")
    artifact = load_model(fuel, horizon, cfg)
    rows = gold[gold["fuel_type"] == fuel].dropna(subset=MODEL_FEATURES).sort_values("date")
    if rows.empty:
        raise ValueError(f"No hay features listas para recomendar {fuel}.")
    last_row = rows.iloc[-1]
    current = float(last_row["price_gtq_per_gallon"])
    # Una serie extraída como ``Series`` queda dtype=object al transponerla;
    # se reconstruye explícitamente como fila numérica para XGBoost.
    x_ultima = pd.DataFrame([last_row[artifact["features"]].astype(float).to_dict()])
    pred = float(artifact["model"].predict(x_ultima)[0])
    # No se despliega un modelo que perdió contra persistencia en su test
    # temporal. En tal caso la predicción operativa segura es el baseline.
    model_beats_baseline = True
    if "test" in artifact:
        test = artifact["test"]
        target = f"target_price_h{horizon}"
        y_test = test[target].to_numpy(dtype=float)
        pred_test = artifact["model"].predict(test[artifact["features"]])
        mae_model = np.abs(y_test - pred_test).mean()
        mae_baseline = np.abs(y_test - test["price_gtq_per_gallon"].to_numpy(dtype=float)).mean()
        model_beats_baseline = bool(mae_model < mae_baseline)
        if not model_beats_baseline:
            pred = current
    difference = pred - current
    margin = float(cfg["recommendation"]["decision_margin_gtq"])
    if difference > margin:
        decision, recargar, trend = "RECARGAR AHORA", True, "up"
        reason = "Se estima un alza superior al margen de decisión; cargar ahora evita pagar más después."
    elif difference < -margin:
        decision, recargar, trend = "WAIT", False, "down"
        reason = "Se estima una baja superior al margen de decisión; si el nivel de combustible lo permite, espere."
    else:
        decision, recargar, trend = "NEUTRAL", False, "stable"
        reason = "El cambio esperado está dentro del margen de decisión; no hay ahorro estimado relevante."
    pico = hour in cfg["recommendation"]["peak_hours"]
    context = "Hora pico: si puede, prefiera una hora no pico para reducir tiempo de espera." if pico else "Hora no pico: contexto operativo favorable para cargar."
    source = str(last_row.get("source", "unknown"))
    warnings = []
    if source != "real":
        warnings.append("El historial disponible es sintético/calibrado; confirme con precios reales antes de una decisión de alto impacto.")
    if not model_beats_baseline:
        warnings.append("XGBoost no superó al baseline en el último test temporal; se aplicó la predicción conservadora de persistencia.")
    warning = " ".join(warnings) or None
    return Recommendation(
        refuel_now=recargar, decision=decision, reason=reason, fuel=fuel,
        horizon_weeks=horizon, current_price_gtq_per_gallon=round(current, 2),
        estimated_price_gtq_per_gallon=round(pred, 2), estimated_difference_gtq=round(difference, 2),
        trend=trend, data_date=str(pd.Timestamp(last_row["date"]).date()),
        hour_context=context, warning=warning,
    )


def recommendation_as_dict(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """La recomendación como diccionario, para serializarla en la API."""
    return asdict(recommend_refuel(*args, **kwargs))
