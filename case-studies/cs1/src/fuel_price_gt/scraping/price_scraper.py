"""Scraper del precio real de referencia de gasolina/diésel en Guatemala.

Fuente: globalpetrolprices.com, que a su vez cita como fuente oficial al
Ministerio de Energía y Minas (MEM) de Guatemala y se actualiza semanalmente
(mismo criterio de frecuencia que D2 en el Business Understanding). Se usa
en la etapa de *testing* para contrastar contra las predicciones/recomendación
del modelo con un precio real, no fabricado.

Si no hay red disponible (p. ej. corriendo pruebas offline/CI), se cae a un
fixture local (`tests/fixtures/reference_price_offline.json`) para que la
suite de tests siga siendo determinista.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime

import requests

from ..config import load_config, resolve_path

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; fuel-price-gt-bot/1.0)"}


@dataclass
class ReferencePrice:
    """Precio publicado por una fuente externa, con su procedencia.

    Saber si el dato vino de la consulta en vivo o del respaldo local es
    parte del dato: una comparación contra un valor de respaldo antiguo no
    tiene el mismo peso que una contra el precio del día.
    """
    fuel: str
    price_gtq_per_gallon: float
    price_gtq_per_liter: float
    monthly_change_pct: float | None
    source: str
    fetched_at: str
    is_offline_fixture: bool


def _parse_price_table(html: str) -> tuple[float, float]:
    """Extrae (GTQ/litro, GTQ/galón) de la tabla superior de la página."""
    m_litro = re.search(r"GTQ.*?align=\"center\">([\d.]+)</td>\s*<td[^>]*align=\"center\">([\d.]+)</td>", html, re.S)
    if not m_litro:
        raise ValueError("No se pudo parsear la tabla de precios de globalpetrolprices")
    litro, galon = float(m_litro.group(1)), float(m_litro.group(2))
    return litro, galon


def _parse_monthly_change(html: str) -> float | None:
    m = re.search(r"Hace un mes.*?align=\"center\">([\d.]+)</td>", html, re.S)
    if not m:
        return None
    return float(m.group(1))


def _get_online(fuel: str, cfg: dict) -> ReferencePrice:
    scraping_cfg = cfg["scraping"]
    url = scraping_cfg["urls"][fuel]
    resp = requests.get(url, headers=_HEADERS, timeout=scraping_cfg["timeout_seconds"])
    resp.raise_for_status()
    litro, galon = _parse_price_table(resp.text)
    hace_un_mes = _parse_monthly_change(resp.text)
    change = None
    if hace_un_mes and hace_un_mes > 0:
        change = round((litro - hace_un_mes) / hace_un_mes * 100, 2)
    return ReferencePrice(
        fuel=fuel,
        price_gtq_per_gallon=galon,
        price_gtq_per_liter=litro,
        monthly_change_pct=change,
        source=url,
        fetched_at=datetime.now(UTC).isoformat(),
        is_offline_fixture=False,
    )


def _get_offline(fuel: str, cfg: dict) -> ReferencePrice:
    fixture_path = resolve_path(cfg["scraping"]["offline_fixture"])
    with open(fixture_path, encoding="utf-8") as fh:
        data = json.load(fh)
    entry = data[fuel]
    return ReferencePrice(
        fuel=fuel,
        price_gtq_per_gallon=entry["price_gtq_per_gallon"],
        price_gtq_per_liter=entry["price_gtq_per_liter"],
        monthly_change_pct=entry.get("monthly_change_pct"),
        source="offline_fixture",
        fetched_at=datetime.now(UTC).isoformat(),
        is_offline_fixture=True,
    )


def get_reference_price(fuel: str = "gasoline", config: dict | None = None) -> ReferencePrice:
    """Precio de referencia externo, con respaldo local si no hay red.

    Nunca falla por un problema de conexión: cae al respaldo y lo declara.
    Que el pipeline entero se caiga porque una fuente externa no responde
    sería un acoplamiento innecesario.
    """
    """Punto de entrada único. `combustible` es "gasoline" (proxy de Regular)
    o "diesel". Intenta scrapear en vivo; si falla por cualquier motivo de
    red, cae de forma transparente al fixture offline."""
    cfg = config or load_config()
    try:
        return _get_online(fuel, cfg)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Scraping en vivo falló (%s); usando fixture offline.", exc)
        return _get_offline(fuel, cfg)
