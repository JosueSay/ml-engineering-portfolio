from __future__ import annotations

from datetime import date

import pandas as pd

from fuel_price_gt.data.pipeline import resolve_cutoff


def _silver(*fechas: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": [date.fromisoformat(f) for f in fechas],
            "fuel_type": ["regular"] * len(fechas),
            "price_gtq_per_gallon": [40.0] * len(fechas),
        }
    )


def test_explicit_argument_wins_over_everything() -> None:
    cfg = {"modeling": {"data_cutoff": "2026-01-01"}}

    assert resolve_cutoff(_silver("2026-08-01"), cfg, date(2026, 5, 5)) == date(2026, 5, 5)


def test_declared_cutoff_wins_over_the_data() -> None:
    """Una fecha declarada fija el conjunto aunque lleguen datos posteriores."""
    cfg = {"modeling": {"data_cutoff": "2026-06-30"}}

    assert resolve_cutoff(_silver("2026-08-01"), cfg) == date(2026, 6, 30)


def test_falls_back_to_the_last_observation() -> None:
    """Sin fecha declarada, el corte sale de los datos y es reproducible."""
    cfg = {"modeling": {}}

    assert resolve_cutoff(_silver("2026-07-01", "2026-08-15"), cfg) == date(2026, 8, 15)


def test_warns_when_it_has_to_use_today(caplog) -> None:
    """El unico caso que rompe la reproducibilidad tiene que avisar."""
    cfg = {"modeling": {}}

    resultado = resolve_cutoff(_silver(), cfg)

    assert resultado == date.today()
    assert any("reproducible" in r.message for r in caplog.records), (
        "usar la fecha de hoy no puede pasar en silencio"
    )
