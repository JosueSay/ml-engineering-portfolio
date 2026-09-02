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
from ..data.features import FEATURES_MODELO


@dataclass
class ResultadoEntrenamiento:
    """Qué produjo una corrida de entrenamiento.

    Guarda los hiperparámetros elegidos junto al artefacto: sin ellos no se
    puede reproducir el modelo ni explicar por qué se comporta como lo hace.
    """
    combustible: str
    horizonte: int
    filas_entrenamiento: int
    filas_test: int
    ruta_modelo: str
    mejores_parametros: dict[str, Any]


def ruta_artefacto(combustible: str, horizonte: int, config: dict | None = None) -> Path:
    """Ubicación del artefacto de un combustible y horizonte.

    El nombre se arma en un solo sitio: estaba repetido en quien guarda y en
    quien lee, y dos literales que tienen que coincidir acaban por no hacerlo.
    """
    cfg = config or load_config()
    destino = resolve_path(cfg["paths"]["models_trained"])
    return destino / f"xgboost_{combustible}_h{horizonte}.joblib"


def version_paquete() -> str:
    """Versión instalada del paquete, o `desconocida` si se corre sin instalar."""
    try:
        return version("gasolina-gt")
    except PackageNotFoundError:
        return "desconocida"


def huella_dataset(datos: pd.DataFrame) -> str:
    """Huella del conjunto con el que se entrenó.

    Es lo que permite responder, ante una predicción rara, si el modelo se
    entrenó con los datos que uno cree. Sin ella el linaje se corta aquí.
    """
    contenido = datos.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(contenido).hexdigest()


def registrar_en_manifiesto(entrada: dict[str, Any], config: dict | None = None) -> Path:
    """Anota un modelo entrenado en el manifiesto versionado.

    El manifiesto es texto y sí entra al control de versiones; los pesos no.
    Así queda registro de qué se entrenó, con qué datos y con qué parámetros,
    sin guardar binarios en el repositorio.
    """
    cfg = config or load_config()
    ruta = resolve_path(cfg["paths"]["models"]) / "manifest.json"
    manifiesto = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {"modelos": []}
    clave = (entrada["combustible"], entrada["horizonte"])
    manifiesto["modelos"] = [
        m for m in manifiesto["modelos"]
        if (m["combustible"], m["horizonte"]) != clave
    ]
    manifiesto["modelos"].append(entrada)
    manifiesto["modelos"].sort(key=lambda m: (m["combustible"], m["horizonte"]))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ruta


def _datos_para_horizonte(
    gold: pd.DataFrame, combustible: str, horizonte: int, config: dict | None = None
) -> pd.DataFrame:
    objetivo = f"objetivo_precio_h{horizonte}"
    requeridas = ["fecha", "precio_gtq_por_galon", objetivo, *FEATURES_MODELO]
    faltantes = set(requeridas) - set(gold.columns)
    if faltantes:
        raise ValueError(f"Dataset Gold no tiene columnas requeridas: {sorted(faltantes)}")
    datos = gold[gold["tipo_combustible"] == combustible].copy()
    datos = datos.dropna(subset=[objetivo, *FEATURES_MODELO]).sort_values("fecha").reset_index(drop=True)
    minimo = (config or load_config())["modelado"]["filas_minimas_entrenamiento"]
    if len(datos) < minimo:
        raise ValueError(
            f"No hay suficientes filas completas para entrenar: {len(datos)} de {minimo} necesarias."
        )
    return datos


def entrenar_modelo(
    gold: pd.DataFrame,
    horizonte: int,
    combustible: str | None = None,
    config: dict | None = None,
) -> tuple[dict[str, Any], ResultadoEntrenamiento]:
    """Entrena XGBoost y devuelve el artefacto junto con sus metadatos."""
    cfg = config or load_config()
    combustible = combustible or cfg["negocio"]["combustible_principal"]
    datos = _datos_para_horizonte(gold, combustible, horizonte, cfg)
    n_test = int(cfg["modelado"]["test_size_semanas"])
    margen = int(cfg["modelado"]["margen_minimo_entrenamiento_semanas"])
    if len(datos) <= n_test + margen:
        raise ValueError(
            f"Tras reservar {n_test} semanas de prueba quedan {len(datos) - n_test} filas, "
            f"por debajo del margen mínimo de {margen}."
        )

    train, test = datos.iloc[:-n_test], datos.iloc[-n_test:]
    x_train, y_train = train[FEATURES_MODELO], train[f"objetivo_precio_h{horizonte}"]
    params = cfg["modelado"]["hiperparametros_xgboost"]
    # Reduce los folds cuando se usa una serie corta, preservando siempre orden temporal.
    n_splits = min(int(cfg["modelado"]["cv_splits"]), max(2, len(train) // 8))
    modelo = XGBRegressor(
        objective="reg:absoluteerror",
        random_state=int(cfg["modelado"]["semilla"]),
        n_jobs=1,
    )
    busqueda = RandomizedSearchCV(
        modelo,
        param_distributions=params,
        n_iter=min(int(cfg["modelado"]["n_iter_busqueda"]), 25),
        scoring="neg_mean_absolute_error",
        cv=TimeSeriesSplit(n_splits=n_splits),
        random_state=int(cfg["modelado"]["semilla"]),
        n_jobs=1,
        refit=True,
    )
    busqueda.fit(x_train, y_train)
    artefacto = {
        "modelo": busqueda.best_estimator_,
        "features": FEATURES_MODELO,
        "combustible": combustible,
        "horizonte": horizonte,
        "fecha_entrenamiento_final": str(train["fecha"].max()),
        "test": test,
        "mejores_parametros": busqueda.best_params_,
    }
    ruta = ruta_artefacto(combustible, horizonte, cfg)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artefacto, ruta)

    registrar_en_manifiesto(
        {
            "combustible": combustible,
            "horizonte": horizonte,
            "artefacto": ruta.name,
            "algoritmo": "xgboost",
            "huella_dataset": huella_dataset(datos),
            "filas_entrenamiento": len(train),
            "filas_test": len(test),
            "fecha_ultimo_dato": str(train["fecha"].max()),
            "hiperparametros": busqueda.best_params_,
            "version_paquete": version_paquete(),
        },
        cfg,
    )
    resultado = ResultadoEntrenamiento(
        combustible=combustible,
        horizonte=horizonte,
        filas_entrenamiento=len(train),
        filas_test=len(test),
        ruta_modelo=str(ruta),
        mejores_parametros=busqueda.best_params_,
    )
    return artefacto, resultado


def cargar_modelo(combustible: str, horizonte: int, config: dict | None = None) -> dict[str, Any]:
    """Recupera un modelo ya entrenado del almacén de artefactos."""
    ruta = ruta_artefacto(combustible, horizonte, config)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el modelo {ruta}. Ejecute primero `gasolina-gt train`.")
    return joblib.load(ruta)


def entrenar_todos_los_horizontes(
    gold: pd.DataFrame, combustible: str | None = None, config: dict | None = None
) -> list[tuple[dict[str, Any], ResultadoEntrenamiento]]:
    """Entrena un modelo por cada horizonte configurado.

    Son modelos distintos y no uno solo consultado a varias distancias:
    predecir a una semana y a cuatro son problemas con dinámicas diferentes,
    y forzarlos en un mismo modelo empeora los dos.
    """
    cfg = config or load_config()
    return [entrenar_modelo(gold, h, combustible, cfg) for h in cfg["negocio"]["horizontes_semanas"]]
