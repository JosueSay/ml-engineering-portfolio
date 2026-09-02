"""Entrenamiento con validación temporal estricta.

La partición respeta el orden del tiempo: entrenar con datos posteriores a
los de prueba inflaría las métricas sin que el modelo sirva para predecir.
"""

from .training import load_model, train_all_horizons, train_model

__all__ = ["load_model", "train_model", "train_all_horizons"]
