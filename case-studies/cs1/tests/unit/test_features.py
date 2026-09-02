from __future__ import annotations

import pandas as pd

from fuel_price_gt.data.features import MODEL_FEATURES, build_features


def test_features_use_only_past_data_and_create_targets() -> None:
    series = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-04", periods=10, freq="7D"),
            "fuel_type": "regular",
            "price_gtq_per_gallon": range(30, 40),
            "source": "real",
        }
    )
    cfg = {"business": {"horizon_weeks": [1, 2, 4]}, "modeling": {"trend_threshold_gtq": 0.15}}
    result = build_features(series, cfg)
    assert set(MODEL_FEATURES).issubset(result.columns)
    assert result.loc[4, "lag_1"] == 33
    assert result.loc[0, "target_price_h1"] == 31
    assert pd.isna(result.loc[len(result) - 1, "target_price_h1"])
