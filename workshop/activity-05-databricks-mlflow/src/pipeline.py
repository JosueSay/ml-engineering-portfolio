"""Pipeline de scikit-learn integrado con MLflow y Databricks.

Actividad 5: Adaptacion de pipeline de scikit-learn utilizando las funcionalidades
de MLflow (Tracking, Experiments, Model Registry y Signature), compatible tanto
de forma remota con Databricks como en ejecucion local.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature

# Importacion relativa o absoluta segun contexto de ejecucion
try:
    from .data import generate_demand_dataset
except ImportError:
    from data import generate_demand_dataset

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("activity05.pipeline")

NUMERIC_FEATURES = [
    "average_temperature",
    "rainfall",
    "price_per_kg",
    "competitor_price_per_kg",
    "marketing_intensity",
    "previous_days_demand",
    "elapsed_years",
]
BINARY_FEATURES = ["weekend", "holiday", "promo", "competitor_is_cheaper"]
CATEGORICAL_FEATURES = ["month"]


class DemandFeatures(BaseEstimator, TransformerMixin):
    """Transformador de scikit-learn para derivar caracteristicas temporales y de mercado.

    Calcula estacionalidad (mes), tendencia (anos transcurridos respecto a la fecha
    de inicio aprendida en fit) y la ventaja de precio del competidor.
    """

    def __init__(self, date_column: str = "date"):
        self.date_column = date_column
        self.reference_date_: str | None = None

    def fit(self, X: pd.DataFrame, y: Any = None) -> DemandFeatures:
        dates = pd.to_datetime(X[self.date_column])
        self.reference_date_ = dates.min().isoformat()
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        dates = pd.to_datetime(X[self.date_column])
        X["month"] = dates.dt.month
        ref = pd.Timestamp(self.reference_date_)
        X["elapsed_years"] = (dates - ref).dt.days / 365.25
        X["competitor_is_cheaper"] = (
            X["competitor_price_per_kg"] < X["price_per_kg"]
        ).astype(int)
        return X.drop(columns=[self.date_column])


def split_temporal_data(
    df: pd.DataFrame,
    target: str = "demand",
    test_size: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Divide la serie temporal respetando el orden cronologico."""
    cut = int(len(df) * (1 - test_size))
    X = df.drop(columns=[target])
    y = df[target]
    return X.iloc[:cut], X.iloc[cut:], y.iloc[:cut], y.iloc[cut:]


def build_preprocessor() -> ColumnTransformer:
    """Construye el preprocesador que atiende columnas numericas, binarias y categoricas."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("bin", "passthrough", BINARY_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )


def build_pipeline(alpha: float = 1.0) -> Pipeline:
    """Construye el Pipeline integral de scikit-learn."""
    return Pipeline(
        steps=[
            ("features", DemandFeatures()),
            ("preprocess", build_preprocessor()),
            ("regressor", Ridge(alpha=alpha, random_state=42)),
        ]
    )


def compute_metrics(y_true: np.ndarray | pd.Series, y_pred: np.ndarray, prefix: str = "") -> dict[str, float]:
    """Calcula RMSE, MAE y R2."""
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)
    mse = float(np.mean((y_true_arr - y_pred_arr) ** 2))
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_true_arr, y_pred_arr))
    r2 = float(r2_score(y_true_arr, y_pred_arr))
    return {
        f"{prefix}rmse": rmse,
        f"{prefix}mae": mae,
        f"{prefix}r2": r2,
    }


def create_evaluation_figure(y_test: pd.Series, y_pred: np.ndarray) -> plt.Figure:
    """Genera figura de diagnostico: reales vs predichos y grafico de residuos."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Grafico 1: Valores reales vs predichos
    ax1.scatter(y_test, y_pred, alpha=0.4, color="#0284c7", edgecolors="none")
    min_val = min(y_test.min(), y_pred.min())
    max_val = max(y_test.max(), y_pred.max())
    ax1.plot([min_val, max_val], [min_val, max_val], "r--", lw=1.5, label="Ideal")
    ax1.set_title("Valores Reales vs Predichos")
    ax1.set_xlabel("Demanda Real")
    ax1.set_ylabel("Demanda Predicha")
    ax1.legend()
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Grafico 2: Residuos
    residuals = y_test - y_pred
    ax2.scatter(y_pred, residuals, alpha=0.4, color="#ea580c", edgecolors="none")
    ax2.axhline(0, color="black", linestyle="--", lw=1.5)
    ax2.set_title("Grafico de Residuos")
    ax2.set_xlabel("Demanda Predicha")
    ax2.set_ylabel("Residuo (Real - Predicho)")
    ax2.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    return fig


def load_env_file() -> None:
    """Carga variables de entorno desde el archivo .env si existe."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and not os.getenv(key):
                        os.environ[key] = val


def configure_mlflow_tracking(
    tracking_uri: str | None = None,
    databricks_host: str | None = None,
    databricks_token: str | None = None,
) -> tuple[str, bool]:
    """Configura el destino del tracking de MLflow (Databricks o Local)."""
    # Cargar .env si existe
    load_env_file()

    # 1. Credenciales pasadas por argumento o variables de entorno
    host = databricks_host or os.getenv("DATABRICKS_HOST")
    token = databricks_token or os.getenv("DATABRICKS_TOKEN")

    if host:
        os.environ["DATABRICKS_HOST"] = host
    if token:
        os.environ["DATABRICKS_TOKEN"] = token

    if tracking_uri == "databricks" or (host and token):
        mlflow.set_tracking_uri("databricks")
        uri = mlflow.get_tracking_uri()
        logger.info("Conectado exitosamente a MLflow en Databricks: %s", host or "perfil default")
        return uri, True

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
        return tracking_uri, False

    # Fallback local usando SQLite en la carpeta de la actividad
    base_dir = Path(__file__).resolve().parent.parent
    local_db = base_dir / "mlflow.db"
    local_uri = f"sqlite:///{local_db}"
    mlflow.set_tracking_uri(local_uri)
    logger.info("Modo local: guardando ejecuciones en %s", local_uri)
    return local_uri, False


def run_pipeline_experiment(
    alpha: float = 1.0,
    n_rows: int = 3000,
    experiment_name: str | None = None,
    register_model: bool = False,
    tracking_uri: str | None = None,
    databricks_host: str | None = None,
    databricks_token: str | None = None,
) -> dict[str, Any]:
    """Ejecuta el ciclo de vida completo del pipeline con seguimiento en MLflow.

    Alineado a las etapas CRISP-DM:
    1. Preparacion de datos: generacion y separacion temporal.
    2. Modelado: ensamblado del Pipeline de scikit-learn y entrenamiento.
    3. Evaluacion: calculo de metricas en train y test, registro de curvas residuales.
    4. Despliegue: registro del modelo serializado con firma y en Model Registry.
    """
    current_uri, is_databricks = configure_mlflow_tracking(
        tracking_uri=tracking_uri,
        databricks_host=databricks_host,
        databricks_token=databricks_token,
    )

    # Definir nombre del experimento
    if not experiment_name:
        if is_databricks:
            # En Databricks los experimentos de usuario van en su ruta personal
            user = os.getenv("DATABRICKS_USER", "josuesay770@gmail.com")
            exp_name = f"/Users/{user}/activity-05-demand-pipeline"
        else:
            exp_name = "activity-05-demand-pipeline"
    else:
        exp_name = experiment_name

    mlflow.set_experiment(exp_name)
    logger.info("Experimento activo: %s", exp_name)

    # 1. Preparacion de datos (CRISP-DM)
    logger.info("Generando dataset de demanda (%d registros)...", n_rows)
    df = generate_demand_dataset(n_rows=n_rows)
    X_train, X_test, y_train, y_test = split_temporal_data(df, target="demand", test_size=0.2)

    # 2. Inicio de ejecucion de MLflow
    run_name = f"ridge_alpha_{alpha}_{'databricks' if is_databricks else 'local'}"
    with mlflow.start_run(run_name=run_name) as run:
        run_id = run.info.run_id
        logger.info("Ejecucion iniciada [Run ID: %s]", run_id)

        # Tags de auditoria y trazabilidad CRISP-DM
        mlflow.set_tags({
            "crisp_dm.phase": "Modeling & Evaluation",
            "project": "activity-05-databricks-mlflow",
            "team": "Grupo 7",
            "author": "Josue Say",
            "framework": "scikit-learn",
            "environment": "Databricks" if is_databricks else "Local",
            "model.family": "Linear / Ridge",
        })

        # Registro de parametros de entrada
        mlflow.log_params({
            "model_type": "Ridge",
            "alpha": alpha,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "total_features": X_train.shape[1],
            "numeric_scaler": "StandardScaler",
            "categorical_encoder": "OneHotEncoder",
            "custom_transformer": "DemandFeatures",
        })

        # 3. Modelado
        logger.info("Entrenando Pipeline de scikit-learn...")
        pipeline = build_pipeline(alpha=alpha)
        pipeline.fit(X_train, y_train)

        # 4. Evaluacion
        logger.info("Evaluando predicciones en conjuntos de Train y Test...")
        y_train_pred = pipeline.predict(X_train)
        y_test_pred = pipeline.predict(X_test)

        train_metrics = compute_metrics(y_train, y_train_pred, prefix="train_")
        test_metrics = compute_metrics(y_test, y_test_pred, prefix="test_")

        all_metrics = {**train_metrics, **test_metrics}
        mlflow.log_metrics(all_metrics)
        for k, v in all_metrics.items():
            logger.info("Métrica registrada - %s: %.4f", k, v)

        # Registro de artefactos graficos
        fig = create_evaluation_figure(y_test, y_test_pred)
        mlflow.log_figure(fig, "evaluation_residual_plot.png")
        plt.close(fig)
        logger.info("Grafico residual guardado como artefacto en MLflow")

        # 5. Despliegue y Registro de Modelo (CRISP-DM)
        # Inferencia de firma formal para garantizar contratos de datos
        sample_input = X_train.head(5)
        signature = infer_signature(sample_input, pipeline.predict(sample_input))

        reg_name = "sklearn_demand_prediction_pipeline" if register_model else None
        mlflow.sklearn.log_model(
            sk_model=pipeline,
            name="demand_pipeline_model",
            signature=signature,
            input_example=sample_input,
            serialization_format="cloudpickle",
            skops_trusted_types=[
                "__main__.DemandFeatures",
                "pipeline.DemandFeatures",
                "src.pipeline.DemandFeatures",
                "DemandFeatures",
            ],
            registered_model_name=reg_name,
        )
        logger.info("Modelo de Pipeline registrado con firma en MLflow")
        if reg_name:
            logger.info("Modelo registrado en Model Registry con nombre: '%s'", reg_name)

        summary = {
            "run_id": run_id,
            "experiment_name": exp_name,
            "tracking_uri": current_uri,
            "is_databricks": is_databricks,
            "metrics": all_metrics,
            "registered_model_name": reg_name,
        }
        return summary


def main() -> None:
    """Punto de entrada de linea de comandos."""
    parser = argparse.ArgumentParser(
        description="Adaptacion de Pipeline de scikit-learn con MLflow y Databricks"
    )
    parser.add_argument("--alpha", type=float, default=1.0, help="Parametro de regularizacion Ridge")
    parser.add_argument("--rows", type=int, default=3000, help="Numero de filas a simular")
    parser.add_argument("--databricks", action="store_true", help="Forzar conexion a Databricks MLflow")
    parser.add_argument("--host", type=str, default=None, help="URL del workspace de Databricks")
    parser.add_argument("--token", type=str, default=None, help="Token de acceso personal de Databricks")
    parser.add_argument("--experiment", type=str, default=None, help="Ruta o nombre del experimento")
    parser.add_argument("--register", action="store_true", help="Registrar modelo en el Model Registry")

    args = parser.parse_args()

    tracking_uri = "databricks" if args.databricks else None

    logger.info("=== Iniciando ejecucion de Pipeline con MLflow ===")
    result = run_pipeline_experiment(
        alpha=args.alpha,
        n_rows=args.rows,
        experiment_name=args.experiment,
        register_model=args.register,
        tracking_uri=tracking_uri,
        databricks_host=args.host,
        databricks_token=args.token,
    )

    print("\n" + "=" * 60)
    print("RESUMEN DE LA EJECUCION EXITOSA:")
    print("=" * 60)
    print(f"Run ID:            {result['run_id']}")
    print(f"Experimento:       {result['experiment_name']}")
    print(f"Backend Tracking:  {result['tracking_uri']}")
    print(f"Destino:           {'Databricks' if result['is_databricks'] else 'Local'}")
    print(f"Test RMSE:         {result['metrics']['test_rmse']:.4f}")
    print(f"Test MAE:          {result['metrics']['test_mae']:.4f}")
    print(f"Test R2:           {result['metrics']['test_r2']:.4f}")
    if result['registered_model_name']:
        print(f"Model Registry:    {result['registered_model_name']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
