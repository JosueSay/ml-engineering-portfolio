"""Métricas y compuerta de calidad.

La compuerta no informa, decide: si el error supera el umbral, si el modelo
no mejora a la referencia simple o si la señal de tendencia es peor que
aleatoria, la corrida falla.
"""

from .metrics import ResultadoEvaluacion, evaluar_artefacto, guardar_reporte

__all__ = ["ResultadoEvaluacion", "evaluar_artefacto", "guardar_reporte"]
