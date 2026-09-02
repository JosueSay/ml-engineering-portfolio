"""Entrenamiento temporal de modelos de precios.

Cada horizonte se entrena y evalúa por separado.  La división nunca mezcla
fechas futuras en entrenamiento: las últimas ``test_size_semanas`` observaciones
se reservan como test y la búsqueda de hiperparámetros usa ``TimeSeriesSplit``.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from xgboost import XGBRegressor

from ..config import load_config, resolve_path
from ..data.features import MODEL_FEATURES
from ..db import create_schema, record_trained_model, session_scope


@dataclass
class TrainingResult:
    """Qué produjo una corrida de entrenamiento.

    Guarda los hiperparámetros elegidos junto al artefacto: sin ellos no se
    puede reproducir el modelo ni explicar por qué se comporta como lo hace.
    """
    fuel: str
    horizon: int
    training_rows: int
    test_rows: int
    model_path: str
    best_params: dict[str, Any]


def artifact_path(fuel: str, horizon: int, config: dict | None = None) -> Path:
    """Ubicación del artefacto de un combustible y horizonte.

    El nombre se arma en un solo sitio: estaba repetido en quien guarda y en
    quien lee, y dos literales que tienen que coincidir acaban por no hacerlo.
    """
    cfg = config or load_config()
    destination = resolve_path(cfg["paths"]["models_trained"])
    return destination / f"xgboost_{fuel}_h{horizon}.joblib"


def package_version() -> str:
    """Versión instalada del paquete, o `desconocida` si se corre sin instalar."""
    try:
        return version("fuel-price-gt")
    except PackageNotFoundError:
        return "unknown"


def dataset_fingerprint(data: pd.DataFrame) -> str:
    """Huella del conjunto con el que se entrenó.

    Es lo que permite responder, ante una predicción rara, si el modelo se
    entrenó con los datos que uno cree. Sin ella el linaje se corta aquí.
    """
    content = data.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def record_in_manifest(entry: dict[str, Any], config: dict | None = None) -> Path:
    """Anota un modelo entrenado en el manifiesto versionado.

    El manifiesto es texto y sí entra al control de versiones; los pesos no.
    Así queda registro de qué se entrenó, con qué datos y con qué parámetros,
    sin guardar binarios en el repositorio.
    """
    cfg = config or load_config()
    path = resolve_path(cfg["paths"]["models"]) / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"models": []}
    key = (entry["fuel"], entry["horizon"])
    manifest["models"] = [
        m for m in manifest["models"]
        if (m["fuel"], m["horizon"]) != key
    ]
    manifest["models"].append(entry)
    manifest["models"].sort(key=lambda m: (m["fuel"], m["horizon"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _data_for_horizon(
    gold: pd.DataFrame, fuel: str, horizon: int, config: dict | None = None
) -> pd.DataFrame:
    target = f"target_price_h{horizon}"
    requeridas = ["date", "price_gtq_per_gallon", target, *MODEL_FEATURES]
    missing = set(requeridas) - set(gold.columns)
    if missing:
        raise ValueError(f"Dataset Gold no tiene columnas requeridas: {sorted(missing)}")
    data = gold[gold["fuel_type"] == fuel].copy()
    data = data.dropna(subset=[target, *MODEL_FEATURES]).sort_values("date").reset_index(drop=True)
    minimum = (config or load_config())["modeling"]["min_training_rows"]
    if len(data) < minimum:
        raise ValueError(
            f"No hay suficientes filas completas para entrenar: {len(data)} de {minimum} necesarias."
        )
    return data


def train_model(
    gold: pd.DataFrame,
    horizon: int,
    fuel: str | None = None,
    config: dict | None = None,
) -> tuple[dict[str, Any], TrainingResult]:
    """Entrena XGBoost y devuelve el artefacto junto con sus metadatos."""
    cfg = config or load_config()
    fuel = fuel or cfg["business"]["main_fuel"]
    data = _data_for_horizon(gold, fuel, horizon, cfg)
    n_test = int(cfg["modeling"]["test_size_weeks"])
    margin = int(cfg["modeling"]["min_training_margin_weeks"])
    if len(data) <= n_test + margin:
        raise ValueError(
            f"Tras reservar {n_test} semanas de prueba quedan {len(data) - n_test} filas, "
            f"por debajo del margen mínimo de {margin}."
        )

    train, test = data.iloc[:-n_test], data.iloc[-n_test:]
    x_train, y_train = train[MODEL_FEATURES], train[f"target_price_h{horizon}"]
    params = cfg["modeling"]["xgboost_hyperparameters"]
    # Reduce los folds cuando se usa una serie corta, preservando siempre orden temporal.
    n_splits = min(int(cfg["modeling"]["cv_splits"]), max(2, len(train) // 8))
    model = XGBRegressor(
        objective="reg:absoluteerror",
        random_state=int(cfg["modeling"]["seed"]),
        n_jobs=1,
    )
    search = RandomizedSearchCV(
        model,
        param_distributions=params,
        n_iter=min(int(cfg["modeling"]["search_iterations"]), 25),
        scoring="neg_mean_absolute_error",
        cv=TimeSeriesSplit(n_splits=n_splits),
        random_state=int(cfg["modeling"]["seed"]),
        n_jobs=1,
        refit=True,
    )
    search.fit(x_train, y_train)
    artifact = {
        "model": search.best_estimator_,
        "features": MODEL_FEATURES,
        "fuel": fuel,
        "horizon": horizon,
        "last_training_date": str(train["date"].max()),
        "test": test,
        "best_params": search.best_params_,
    }
    path = artifact_path(fuel, horizon, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, path)

    # El manifiesto es un archivo de texto versionable; la base cierra el
    # linaje. Se escribe en los dos porque responden preguntas distintas: el
    # manifiesto dice que se entreno sin abrir nada, la base permite ir desde
    # una prediccion hasta la fotografia que la sostiene.
    # El esquema se asegura aqui porque entrenar no deberia fallar solo porque
    # nadie inicializo la base antes. Es idempotente: si ya esta, no hace nada.
    create_schema()
    with session_scope() as sesion:
        record_trained_model(
            sesion,
            fuel_type=fuel,
            horizon_weeks=horizon,
            algorithm="xgboost",
            dataset_fingerprint=dataset_fingerprint(data),
            hyperparameters=search.best_params_,
            artifact_path=str(path),
            package_version=package_version(),
        )

    record_in_manifest(
        {
            "fuel": fuel,
            "horizon": horizon,
            "artifact": path.name,
            "algorithm": "xgboost",
            "dataset_fingerprint": dataset_fingerprint(data),
            "training_rows": len(train),
            "test_rows": len(test),
            "last_data_date": str(train["date"].max()),
            "hyperparameters": search.best_params_,
            "package_version": package_version(),
        },
        cfg,
    )
    result = TrainingResult(
        fuel=fuel,
        horizon=horizon,
        training_rows=len(train),
        test_rows=len(test),
        model_path=str(path),
        best_params=search.best_params_,
    )
    return artifact, result


def load_model(fuel: str, horizon: int, config: dict | None = None) -> dict[str, Any]:
    """Recupera un modelo ya entrenado del almacén de artefactos."""
    path = artifact_path(fuel, horizon, config)
    if not path.exists():
        raise FileNotFoundError(f"No existe el modelo {path}. Ejecute primero `fuel-price-gt train`.")
    return joblib.load(path)


def train_all_horizons(
    gold: pd.DataFrame, fuel: str | None = None, config: dict | None = None
) -> list[tuple[dict[str, Any], TrainingResult]]:
    """Entrena un modelo por cada horizonte configurado.

    Son modelos distintos y no uno solo consultado a varias distancias:
    predecir a una semana y a cuatro son problemas con dinámicas diferentes,
    y forzarlos en un mismo modelo empeora los dos.
    """
    cfg = config or load_config()
    return [train_model(gold, h, fuel, cfg) for h in cfg["business"]["horizon_weeks"]]
