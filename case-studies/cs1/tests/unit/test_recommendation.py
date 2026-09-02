from __future__ import annotations

import pandas as pd

from fuel_price_gt.data.features import MODEL_FEATURES
from fuel_price_gt.serving.recommendation import recommend_refuel


class _RisingPriceModel:
    def predict(self, x: pd.DataFrame) -> list[float]:
        return [35.50]


def test_recommends_refuel_when_price_forecast_rises(monkeypatch) -> None:
    import fuel_price_gt.serving.recommendation as modulo

    monkeypatch.setattr(modulo, "load_model", lambda *a, **k: {"model": _RisingPriceModel(), "features": MODEL_FEATURES})
    fila = {"date": "2026-08-16", "fuel_type": "regular", "price_gtq_per_gallon": 35.0, "source": "real"}
    fila.update({feature: 1.0 for feature in MODEL_FEATURES})
    result = recommend_refuel(pd.DataFrame([fila]), hour=18)
    assert result.refuel_now is True
    assert result.trend == "up"
    assert "Hora pico" in result.hour_context
