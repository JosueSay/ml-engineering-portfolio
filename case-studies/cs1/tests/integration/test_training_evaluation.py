from __future__ import annotations

import json
from copy import deepcopy

import pandas as pd

from gasolina_gt.config import load_config
from gasolina_gt.data.features import construir_features
from gasolina_gt.evaluation import evaluar_artefacto
from gasolina_gt.modeling.training import entrenar_modelo


def test_entrenamiento_temporal_y_evaluacion(tmp_path) -> None:
    fechas = pd.date_range("2025-01-05", periods=44, freq="7D")
    serie = pd.DataFrame(
        {
            "fecha": fechas, "tipo_combustible": "regular",
            "precio_gtq_por_galon": [30 + i * 0.08 for i in range(len(fechas))], "fuente": "real",
        }
    )
    # Se parte de la configuracion real y solo se ajusta lo que la prueba
    # necesita. Construirla entera a mano la volvia fragil: cualquier clave
    # nueva del proyecto rompia la prueba sin que nada estuviera mal.
    cfg = deepcopy(load_config())
    cfg["negocio"]["horizontes_semanas"] = [1]
    cfg["modelado"].update(
        {
            "semilla": 7,
            "cv_splits": 2,
            "n_iter_busqueda": 1,
            "hiperparametros_xgboost": {
                "n_estimators": [10], "max_depth": [2], "learning_rate": [0.1],
                "subsample": [1.0], "colsample_bytree": [1.0], "reg_lambda": [1.0],
            },
        }
    )
    cfg["paths"]["models"] = str(tmp_path / "models")
    cfg["paths"]["models_trained"] = str(tmp_path / "models" / "trained")
    gold = construir_features(serie, cfg)
    artefacto, meta = entrenar_modelo(gold, 1, "regular", cfg)
    evaluacion = evaluar_artefacto(artefacto, cfg)
    assert meta.filas_test == 6
    assert (tmp_path / "models" / "trained" / "xgboost_regular_h1.joblib").exists()
    # El manifiesto deja constancia de con que datos se entreno.
    manifiesto = json.loads((tmp_path / "models" / "manifest.json").read_text(encoding="utf-8"))
    assert manifiesto["modelos"][0]["huella_dataset"]
    assert evaluacion.mae_modelo >= 0
