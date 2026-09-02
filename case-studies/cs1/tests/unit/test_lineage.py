from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from fuel_price_gt.db.lineage import lineage_coverage, trace_price
from fuel_price_gt.db.models import (
    METHOD_ARITHMETIC,
    METHOD_MEDIAN,
    METHOD_OCR,
    REGION_DETECTED,
    Base,
    ExtractionRun,
    GoldRow,
    Image,
    ImageCrop,
    PriceReading,
    SilverPrice,
)


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, _record):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _cadena_completa(s: Session, day: date) -> None:
    """Arma una cadena de custodia entera, de la fotografía al conjunto."""
    image = Image(
        sha256="a" * 64,
        original_name="IMG_0001.HEIC",
        captured_at=datetime(day.year, day.month, day.day, 10, 30),
        brand="Shell",
        station="Roosevelt",
        width=4032,
        height=3024,
    )
    s.add(image)
    s.flush()

    crop = ImageCrop(
        image_id=image.id,
        region="regular",
        bbox={"x0": 100, "y0": 200, "x1": 300, "y1": 400},
        path="data/interim/IMG_0001_regular.png",
        detection_method=REGION_DETECTED,
    )
    run = ExtractionRun(
        image_id=image.id,
        package_version="0.1.0",
        ocr_engine="seven_segment",
        config_hash="c" * 64,
    )
    s.add_all([crop, run])
    s.flush()

    reading = PriceReading(
        extraction_run_id=run.id,
        image_crop_id=crop.id,
        fuel_type="regular",
        price_gtq_per_gallon=40.5,
        confidence=0.91,
        raw_text="40.50",
        is_valid=True,
        method=METHOD_OCR,
    )
    s.add(reading)
    s.flush()

    silver = SilverPrice(
        observed_on=day,
        fuel_type="regular",
        price_gtq_per_gallon=40.5,
        price_reading_id=reading.id,
        method=METHOD_OCR,
        brand="Shell",
    )
    s.add(silver)
    s.flush()

    s.add(
        GoldRow(
            observed_on=day,
            fuel_type="regular",
            price_gtq_per_gallon=40.5,
            features={"lag_1": 40.1},
            source="real",
            method=METHOD_OCR,
            silver_price_id=silver.id,
        )
    )
    s.commit()


def test_lineage_reaches_the_photograph(session: Session) -> None:
    day = date(2026, 8, 15)
    _cadena_completa(session, day)

    trace = trace_price(session, day, "regular")

    assert trace is not None
    assert trace.reaches_photograph
    assert not trace.breaks
    # La cadena entera queda disponible, no solo el extremo.
    assert trace.image["original_name"] == "IMG_0001.HEIC"
    assert trace.crop["path"].endswith("IMG_0001_regular.png")
    assert trace.crop["detection_method"] == REGION_DETECTED
    assert trace.reading["confidence"] == 0.91
    assert trace.extraction["ocr_engine"] == "seven_segment"


def test_synthetic_row_declares_the_break(session: Session) -> None:
    """Una fila generada no tiene fotografía detrás, y debe decirlo."""
    session.add(
        GoldRow(
            observed_on=date(2026, 8, 22),
            fuel_type="regular",
            price_gtq_per_gallon=41.0,
            features={"lag_1": 40.5},
            source="synthetic",
            method=METHOD_MEDIAN,
        )
    )
    session.commit()

    trace = trace_price(session, date(2026, 8, 22), "regular")

    assert trace is not None
    assert not trace.reaches_photograph
    assert trace.breaks, "una ruptura de la cadena tiene que quedar declarada"
    assert trace.method == METHOD_MEDIAN


def test_reconstructed_price_keeps_its_method(session: Session) -> None:
    """Un precio recuperado por aritmética llega hasta el conjunto marcado."""
    day = date(2026, 8, 29)
    silver = SilverPrice(
        observed_on=day,
        fuel_type="super",
        price_gtq_per_gallon=39.5,
        method=METHOD_ARITHMETIC,
    )
    session.add(silver)
    session.flush()
    session.add(
        GoldRow(
            observed_on=day,
            fuel_type="super",
            price_gtq_per_gallon=39.5,
            features={},
            source="real",
            method=METHOD_ARITHMETIC,
            silver_price_id=silver.id,
        )
    )
    session.commit()

    trace = trace_price(session, day, "super")

    assert trace is not None
    assert trace.method == METHOD_ARITHMETIC
    assert trace.silver["method"] == METHOD_ARITHMETIC
    # No hay lectura porque el valor no se leyó: se reconstruyó. Y se declara.
    assert trace.reading is None
    assert any("arithmetic" in b for b in trace.breaks)


def test_coverage_measures_how_much_is_traceable(session: Session) -> None:
    _cadena_completa(session, date(2026, 8, 15))
    session.add(
        GoldRow(
            observed_on=date(2026, 8, 22),
            fuel_type="regular",
            price_gtq_per_gallon=41.0,
            features={},
            source="synthetic",
            method=METHOD_MEDIAN,
        )
    )
    session.commit()

    coverage = lineage_coverage(session)

    assert coverage["gold_rows"] == 2
    assert coverage["traceable"] == 1
    assert coverage["coverage_pct"] == 50.0
    assert coverage["by_method"] == {METHOD_MEDIAN: 1, METHOD_OCR: 1}
