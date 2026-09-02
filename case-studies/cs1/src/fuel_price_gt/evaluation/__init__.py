"""Métricas y compuerta de calidad.

La compuerta no informa, decide: si el error supera el umbral, si el modelo
no mejora a la referencia simple o si la señal de tendencia es peor que
aleatoria, la corrida falla.
"""

from .metrics import EvaluationResult, evaluate_artifact, save_report

__all__ = ["EvaluationResult", "evaluate_artifact", "save_report"]
