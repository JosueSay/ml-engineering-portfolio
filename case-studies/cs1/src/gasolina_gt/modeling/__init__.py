"""Entrenamiento con validación temporal estricta.

La partición respeta el orden del tiempo: entrenar con datos posteriores a
los de prueba inflaría las métricas sin que el modelo sirva para predecir.
"""

from .training import cargar_modelo, entrenar_modelo, entrenar_todos_los_horizontes

__all__ = ["cargar_modelo", "entrenar_modelo", "entrenar_todos_los_horizontes"]
