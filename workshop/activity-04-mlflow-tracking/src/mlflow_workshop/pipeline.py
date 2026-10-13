"""Pipeline de scikit-learn para predecir la demanda de manzanas."""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

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
    """Deriva del dataframe crudo las variables que el modelo necesita.

    Convierte la fecha en mes (estacionalidad) y anos transcurridos
    (tendencia), y compara el precio propio con el de la competencia. La fecha
    de referencia se aprende en ``fit``, asi el conjunto de prueba se mide
    contra el inicio del entrenamiento y no contra su propio inicio.

    La fecha aprendida se guarda como texto ISO y no como ``pandas.Timestamp``:
    skops, el formato con que MLflow serializa el pipeline, no reconstruye ese tipo.
    """

    def __init__(self, date_column="date"):
        self.date_column = date_column

    def fit(self, X, y=None):
        self.reference_date_ = pd.to_datetime(X[self.date_column]).min().isoformat()
        return self

    def transform(self, X):
        X = X.copy()
        dates = pd.to_datetime(X[self.date_column])
        X["month"] = dates.dt.month
        X["elapsed_years"] = (dates - pd.Timestamp(self.reference_date_)).dt.days / 365.25
        X["competitor_is_cheaper"] = (
            X["competitor_price_per_kg"] < X["price_per_kg"]
        ).astype(int)
        return X.drop(columns=[self.date_column])


def split_by_time(df, target, test_size=0.2):
    """Separa una serie ordenada por fecha: el ultimo tramo queda para prueba.

    Una particion aleatoria mezclaria dias futuros en el entrenamiento, y con
    una variable como la demanda del dia anterior eso filtra el objetivo.
    """
    cut = int(len(df) * (1 - test_size))
    X, y = df.drop(columns=[target]), df[target]
    return X.iloc[:cut], X.iloc[cut:], y.iloc[:cut], y.iloc[cut:]


def build_preprocessor():
    """Crea el ColumnTransformer con ramas numerica, binaria y categorica."""
    return ColumnTransformer(transformers=[
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("bin", "passthrough", BINARY_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])


def build_pipeline(model=None):
    """Crea el pipeline completo: variables derivadas + preprocesamiento + modelo."""
    return Pipeline(steps=[
        ("features", DemandFeatures()),
        ("preprocess", build_preprocessor()),
        ("model", model if model is not None else Ridge()),
    ])


def regression_metrics(y_true, y_pred, prefix=""):
    """Retorna rmse, mae y r2 en un dict listo para ``mlflow.log_metrics``."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return {
        f"{prefix}rmse": float(root_mean_squared_error(y_true, y_pred)),
        f"{prefix}mae": float(mean_absolute_error(y_true, y_pred)),
        f"{prefix}r2": float(r2_score(y_true, y_pred)),
    }
