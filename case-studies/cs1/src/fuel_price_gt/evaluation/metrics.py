"""Métricas de evaluación y reporte auditable frente al baseline naive."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, mean_absolute_error

from ..config import load_config, resolve_path


@dataclass
class EvaluationResult:
    """Métricas de un modelo frente a la referencia simple.

    El error por sí solo no dice si el modelo sirve: hay que compararlo con
    lo que se obtiene repitiendo el último precio conocido. Un modelo que no
    supera esa referencia no aporta nada, por bajo que sea su error.
    """
    fuel: str
    horizon: int
    mae_model: float
    mae_baseline: float
    improvement_vs_baseline_pct: float
    mape_model_pct: float
    wape_model_pct: float
    f1_trend_model: float
    f1_trend_baseline: float
    beats_baseline: bool
    meets_mae: bool
    meets_f1: bool
    data_source: str


def _trend(prediction: np.ndarray, current: np.ndarray, threshold: float) -> np.ndarray:
    delta = prediction - current
    return np.select([delta > threshold, delta < -threshold], ["up", "down"], default="stable")


def evaluate_artifact(artifact: dict[str, Any], config: dict | None = None) -> EvaluationResult:
    """Evalúa un modelo entrenado sobre su ventana de prueba."""
    cfg = config or load_config()
    test = artifact["test"].copy()
    target = f"target_price_h{artifact['horizon']}"
    y = test[target].to_numpy(dtype=float)
    current = test["price_gtq_per_gallon"].to_numpy(dtype=float)
    pred = artifact["model"].predict(test[artifact["features"]])
    baseline = current  # persistencia: el último precio conocido al instante t.
    mae = float(mean_absolute_error(y, pred))
    mae_base = float(mean_absolute_error(y, baseline))
    mejora = 0.0 if mae_base == 0 else (mae_base - mae) / mae_base * 100
    mape = float(np.mean(np.abs((y - pred) / y)) * 100)
    wape = float(np.abs(y - pred).sum() / np.abs(y).sum() * 100)
    threshold = float(cfg["modeling"]["trend_threshold_gtq"])
    y_trend = _trend(y, current, threshold)
    f1 = float(f1_score(y_trend, _trend(pred, current, threshold), average="macro", zero_division=0))
    # Baseline de tendencia: proyectar el último cambio observado una semana.
    simple_trend = current + test["recent_trend"].to_numpy(dtype=float)
    f1_base = float(f1_score(y_trend, _trend(simple_trend, current, threshold), average="macro", zero_division=0))
    source = "mixed" if (test.get("source") == "real").any() and (test.get("source") == "synthetic").any() else str(test.get("source", pd.Series(["unknown"])).iloc[0])
    ev = cfg["evaluation"]
    return EvaluationResult(
        fuel=artifact["fuel"], horizon=int(artifact["horizon"]),
        mae_model=round(mae, 4), mae_baseline=round(mae_base, 4), improvement_vs_baseline_pct=round(mejora, 2),
        mape_model_pct=round(mape, 3), wape_model_pct=round(wape, 3),
        f1_trend_model=round(f1, 4), f1_trend_baseline=round(f1_base, 4),
        beats_baseline=mae < mae_base, meets_mae=mae <= float(ev["mae_threshold_gtq"]),
        meets_f1=f1 >= float(ev["f1_trend_threshold"]), data_source=source,
    )


def save_report(results: list[EvaluationResult], config: dict | None = None) -> Path:
    """Escribe el reporte de evaluación y devuelve su ruta."""
    cfg = config or load_config()
    reports = resolve_path(cfg["paths"]["reports"])
    reports.mkdir(parents=True, exist_ok=True)
    path = reports / cfg["files"]["evaluation"]
    pd.DataFrame([asdict(r) for r in results]).to_csv(path, index=False)
    return path
