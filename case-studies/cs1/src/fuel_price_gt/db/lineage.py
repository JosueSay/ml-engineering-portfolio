"""Consulta de linaje: de un precio hacia atrás, hasta la fotografía.

Es la razón de ser del modelo relacional. Ante una predicción rara, la pregunta
no es "cuánto vale este precio" sino "de dónde salió": qué fotografía, qué
recorte, qué motor lo leyó, con qué confianza y con qué versión del código.

Sin poder contestar eso, un error del modelo y un error de lectura se ven
exactamente igual desde fuera.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import GoldRow, Image, ImageCrop, PriceReading, SilverPrice


@dataclass
class Lineage:
    """Recorrido completo de un valor, desde el conjunto hasta la fotografía.

    Los eslabones ausentes se declaran en `breaks` en vez de dejarse en blanco:
    una fila sintética no tiene fotografía detrás, y eso es una respuesta
    legítima, no un fallo de la consulta.
    """

    observed_on: date
    fuel_type: str
    price_gtq_per_gallon: float
    source: str
    method: str
    silver: dict[str, Any] | None = None
    reading: dict[str, Any] | None = None
    crop: dict[str, Any] | None = None
    image: dict[str, Any] | None = None
    extraction: dict[str, Any] | None = None
    breaks: list[str] = field(default_factory=list)

    @property
    def reaches_photograph(self) -> bool:
        """Si la cadena llega hasta una fotografía real."""
        return self.image is not None


def trace_gold_row(session: Session, row: GoldRow) -> Lineage:
    """Recorre hacia atrás la cadena de custodia de una fila del conjunto."""
    rastro = Lineage(
        observed_on=row.observed_on,
        fuel_type=row.fuel_type,
        price_gtq_per_gallon=row.price_gtq_per_gallon,
        source=row.source,
        method=row.method,
    )

    silver: SilverPrice | None = row.silver_price
    if silver is None:
        rastro.breaks.append(
            "sin precio de origen: la fila es sintetica o se genero sin ancla real"
        )
        return rastro

    rastro.silver = {
        "id": silver.id,
        "observed_on": silver.observed_on,
        "price_gtq_per_gallon": silver.price_gtq_per_gallon,
        "method": silver.method,
        "brand": silver.brand,
    }

    reading: PriceReading | None = silver.reading
    if reading is None:
        rastro.breaks.append(
            f"sin lectura de origen: el precio se obtuvo por '{silver.method}'"
        )
        return rastro

    rastro.reading = {
        "id": reading.id,
        "price_gtq_per_gallon": reading.price_gtq_per_gallon,
        "confidence": reading.confidence,
        "raw_text": reading.raw_text,
        "is_valid": reading.is_valid,
        "rejection_reason": reading.rejection_reason,
        "method": reading.method,
    }

    run = reading.extraction_run
    rastro.extraction = {
        "id": run.id,
        "package_version": run.package_version,
        "ocr_engine": run.ocr_engine,
        "config_hash": run.config_hash,
        "executed_at": run.executed_at,
    }

    crop: ImageCrop | None = reading.crop
    if crop is None:
        rastro.breaks.append("sin recorte asociado: no se puede revisar la evidencia visual")
    else:
        rastro.crop = {
            "id": crop.id,
            "region": crop.region,
            "bbox": crop.bbox,
            "path": crop.path,
            "detection_method": crop.detection_method,
        }

    image: Image = run.image
    rastro.image = {
        "id": image.id,
        "sha256": image.sha256,
        "original_name": image.original_name,
        "source_uri": image.source_uri,
        "captured_at": image.captured_at,
        "brand": image.brand,
        "station": image.station,
    }
    return rastro


def trace_price(session: Session, observed_on: date, fuel_type: str) -> Lineage | None:
    """Linaje del precio de un día y un combustible. `None` si no existe."""
    row = session.scalar(
        select(GoldRow).where(
            GoldRow.observed_on == observed_on,
            GoldRow.fuel_type == fuel_type,
        )
    )
    return trace_gold_row(session, row) if row else None


def lineage_coverage(session: Session) -> dict[str, Any]:
    """Cuánto del conjunto de modelado se puede rastrear hasta una fotografía.

    Es la medida de salud del caso: si la cobertura es cero, el modelo se
    entrena únicamente sobre datos generados, y conviene que eso se vea en un
    número y no solo en una advertencia.
    """
    filas = list(session.scalars(select(GoldRow)))
    if not filas:
        return {"gold_rows": 0, "traceable": 0, "coverage_pct": 0.0, "by_method": {}}

    rastreables = 0
    por_metodo: dict[str, int] = {}
    for fila in filas:
        por_metodo[fila.method] = por_metodo.get(fila.method, 0) + 1
        if trace_gold_row(session, fila).reaches_photograph:
            rastreables += 1

    return {
        "gold_rows": len(filas),
        "traceable": rastreables,
        "coverage_pct": round(100 * rastreables / len(filas), 2),
        "by_method": dict(sorted(por_metodo.items())),
    }
