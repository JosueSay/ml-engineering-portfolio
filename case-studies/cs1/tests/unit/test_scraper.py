from __future__ import annotations

from unittest.mock import Mock

from fuel_price_gt.config import load_config
from fuel_price_gt.scraping.price_scraper import get_reference_price


def test_scraper_falls_back_to_fixture_without_network(monkeypatch) -> None:
    import fuel_price_gt.scraping.price_scraper as modulo

    monkeypatch.setattr(modulo.requests, "get", Mock(side_effect=OSError("sin red")))
    result = get_reference_price("gasoline", load_config())
    assert result.is_offline_fixture is True
    assert result.price_gtq_per_gallon > 0
