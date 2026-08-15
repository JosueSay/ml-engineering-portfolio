"""
ML Pipeline - Linear Regression con calibracion de hiperparametros.

Uso:
    from ml_pipeline import (
        FeatureExtractor, RowFilter,
        crear_preprocesador, crear_pipeline_modelo, calibrar_modelo, evaluar_modelo,
        analizar_overfitting, mostrar_coeficientes, validacion_cruzada,
    )
"""

from .analysis import analizar_overfitting, mostrar_coeficientes, validacion_cruzada
from .pipeline import (
    calibrar_modelo,
    crear_pipeline_modelo,
    crear_preprocesador,
    evaluar_modelo,
)
from .transformers import FeatureExtractor, RowFilter

__version__ = "0.1.0"

__all__ = [
    "FeatureExtractor",
    "RowFilter",
    "crear_preprocesador",
    "crear_pipeline_modelo",
    "calibrar_modelo",
    "evaluar_modelo",
    "analizar_overfitting",
    "mostrar_coeficientes",
    "validacion_cruzada",
]
