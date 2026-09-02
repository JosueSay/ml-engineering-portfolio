"""Construccion y calibracion del pipeline de modelado."""

import numpy as np
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def crear_preprocesador():
    """Crea el ColumnTransformer con ramas numerica y categorica."""
    numeric_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])

    categorical_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore')),
    ])

    return ColumnTransformer(transformers=[
        ('num', numeric_pipeline, make_column_selector(dtype_include=np.number)),
        ('cat', categorical_pipeline, make_column_selector(dtype_include=object)),
    ])


def crear_pipeline_modelo(preprocessor, modelo_clase=LinearRegression, **modelo_params):
    """Crea pipeline con preprocesamiento + modelo especificado."""
    return Pipeline(steps=[
        ('preprocesamiento', preprocessor),
        ('modelo', modelo_clase(**modelo_params))
    ])


def calibrar_modelo(pipeline, X_train, y_train, param_grid, cv=5):
    """Ejecuta GridSearchCV y retorna resultados."""
    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=cv,
        scoring='r2',
        n_jobs=-1
    )
    grid_search.fit(X_train, y_train)
    return grid_search


def evaluar_modelo(modelo, X_train, y_train, X_test, y_test):
    """Retorna metricas en dict {train, test} con r2, mae, rmse."""
    y_train_pred = modelo.predict(X_train)
    y_test_pred = modelo.predict(X_test)

    return {
        'train': {
            'r2': r2_score(y_train, y_train_pred),
            'mae': mean_absolute_error(y_train, y_train_pred),
            'rmse': np.sqrt(mean_squared_error(y_train, y_train_pred))
        },
        'test': {
            'r2': r2_score(y_test, y_test_pred),
            'mae': mean_absolute_error(y_test, y_test_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_test_pred))
        }
    }
