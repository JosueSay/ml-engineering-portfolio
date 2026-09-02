from __future__ import annotations

import json
from copy import deepcopy

import pandas as pd

from fuel_price_gt.config import load_config
from fuel_price_gt.data.features import build_features
from fuel_price_gt.evaluation import evaluate_artifact
from fuel_price_gt.modeling.training import train_model


def test_temporal_training_and_evaluation(tmp_path) -> None:
    dates = pd.date_range("2025-01-05", periods=44, freq="7D")
    series = pd.DataFrame(
        {
            "date": dates, "fuel_type": "regular",
            "price_gtq_per_gallon": [30 + i * 0.08 for i in range(len(dates))], "source": "real",
        }
    )
    # Se parte de la configuracion real y solo se ajusta lo que la prueba
    # necesita. Construirla entera a mano la volvia fragil: cualquier clave
    # nueva del proyecto rompia la prueba sin que nada estuviera mal.
    cfg = deepcopy(load_config())
    cfg["business"]["horizon_weeks"] = [1]
    cfg["modeling"].update(
        {
            "seed": 7,
            "cv_splits": 2,
            "search_iterations": 1,
            "xgboost_hyperparameters": {
                "n_estimators": [10], "max_depth": [2], "learning_rate": [0.1],
                "subsample": [1.0], "colsample_bytree": [1.0], "reg_lambda": [1.0],
            },
        }
    )
    cfg["paths"]["models"] = str(tmp_path / "models")
    cfg["paths"]["models_trained"] = str(tmp_path / "models" / "trained")
    gold = build_features(series, cfg)
    artifact, meta = train_model(gold, 1, "regular", cfg)
    evaluation = evaluate_artifact(artifact, cfg)
    assert meta.test_rows == 6
    assert (tmp_path / "models" / "trained" / "xgboost_regular_h1.joblib").exists()
    # El manifiesto deja constancia de con que datos se entreno.
    manifest = json.loads((tmp_path / "models" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["models"][0]["dataset_fingerprint"]
    assert evaluation.mae_model >= 0
