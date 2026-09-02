"""API HTTP opcional para consultar la recomendación más reciente."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from .. import __version__
from ..data.pipeline import load_gold_if_exists
from .recommendation import recommendation_as_dict

# La version se toma del paquete y no se escribe aqui: repetida, se queda atras
# sin que nada avise, y quien consulta el servicio ve un numero que no es.
app = FastAPI(title="Fuel Price GT", version=__version__)


@app.get("/health")
def health() -> dict[str, str]:
    """Comprueba que el servicio está en pie.

    No toca el modelo ni los datos a propósito: responde si el proceso
    levanta, que es lo que necesita saber un orquestador para decidir si
    enrutar tráfico.
    """
    return {"status": "ok"}


@app.get("/recomendacion")
def recommendation(
    fuel: str = Query("regular"), horizon: int = Query(1, ge=1), hour: int | None = Query(None, ge=0, le=23)
) -> dict:
    """Devuelve la recomendación de carga para un combustible y horizonte.

    Lee el modelo ya entrenado del almacén de artefactos; no entrena nada al
    vuelo. Entrenar dentro de una petición haría impredecible su tiempo de
    respuesta.
    """
    gold = load_gold_if_exists()
    if gold is None:
        raise HTTPException(503, "No existe dataset Gold; ejecute fuel-price-gt build-data.")
    try:
        return recommendation_as_dict(gold, fuel, horizon, hour)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(503, str(exc)) from exc
