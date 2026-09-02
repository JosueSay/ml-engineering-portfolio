"""Acceso a la base de datos desde la lógica del pipeline.

La lógica de negocio habla con estas funciones y no con el motor: así cambiar
de motor es cambiar la cadena de conexión, y las pruebas pueden trabajar contra
una base en memoria sin tocar nada más.

Todas las escrituras son idempotentes por naturaleza del dato. Volver a
procesar una fotografía ya vista no la duplica, porque su identidad es la huella
del archivo y no su nombre ni el momento en que llegó.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import (
    METHOD_OCR,
    REGION_CALIBRATED,
    ExtractionRun,
    GoldRow,
    Image,
    ImageCrop,
    PriceReading,
    SilverPrice,
    TrainedModel,
)


def config_fingerprint(config: dict[str, Any]) -> str:
    """Huella de la configuración con la que corrió una etapa.

    Permite distinguir dos corridas sobre la misma imagen que dieron resultados
    distintos porque cambió un umbral, no porque cambiara el código.
    """
    serializada = json.dumps(config, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(serializada.encode("utf-8")).hexdigest()


# --- Bronze ---------------------------------------------------------------------

def get_or_create_image(
    session: Session,
    *,
    sha256: str,
    original_name: str,
    width: int | None = None,
    height: int | None = None,
    captured_at: datetime | None = None,
    source_uri: str | None = None,
    brand: str | None = None,
    station: str | None = None,
    blurred_faces: int = 0,
) -> Image:
    """Devuelve la fotografía por su huella, creándola si es la primera vez.

    La huella es la identidad. El mismo archivo con otro nombre, o llegado por
    otra vía, es la misma fotografía y no debe duplicarse: si lo hiciera, la
    serie contaría dos veces el mismo precio.
    """
    existente = session.scalar(select(Image).where(Image.sha256 == sha256))
    if existente is not None:
        # Los metadatos pueden mejorar entre pasadas: una segunda ingesta puede
        # traer la marca o la estación que la primera no conocía.
        for campo, valor in (
            ("source_uri", source_uri),
            ("brand", brand),
            ("station", station),
            ("captured_at", captured_at),
        ):
            if valor is not None and getattr(existente, campo) is None:
                setattr(existente, campo, valor)
        return existente

    imagen = Image(
        sha256=sha256,
        original_name=original_name,
        width=width,
        height=height,
        captured_at=captured_at,
        source_uri=source_uri,
        brand=brand,
        station=station,
        blurred_faces=blurred_faces,
    )
    session.add(imagen)
    session.flush()
    return imagen


def upsert_crop(
    session: Session,
    *,
    image: Image,
    region: str,
    bbox: dict[str, int],
    path: str,
    detection_method: str = REGION_CALIBRATED,
) -> ImageCrop:
    """Registra el recorte de una región, o actualiza el que ya había.

    Solo se guarda uno por imagen y región: el último recorte es el que
    corresponde a la calibración vigente, y conservar los anteriores confundiría
    al revisar la evidencia.
    """
    existente = session.scalar(
        select(ImageCrop).where(ImageCrop.image_id == image.id, ImageCrop.region == region)
    )
    if existente is not None:
        existente.bbox = bbox
        existente.path = path
        existente.detection_method = detection_method
        return existente

    crop = ImageCrop(
        image_id=image.id,
        region=region,
        bbox=bbox,
        path=path,
        detection_method=detection_method,
    )
    session.add(crop)
    session.flush()
    return crop


def already_extracted(
    session: Session,
    *,
    sha256: str,
    package_version: str,
    config_hash: str,
) -> bool:
    """Dice si esa fotografia ya se proceso con este codigo y esta configuracion.

    Volver a leer una imagen cuesta segundos por fotografia, y con el historico
    completo son horas. Si ni el codigo ni los parametros han cambiado, el
    resultado seria identico al que ya esta guardado, asi que no hay nada que
    ganar repitiendolo.

    La comprobacion es por las tres cosas a la vez: basta que cambie un umbral
    de la configuracion para que la lectura pueda dar otro resultado, y entonces
    si hay que rehacerla.
    """
    imagen = session.scalar(select(Image).where(Image.sha256 == sha256))
    if imagen is None:
        return False
    corrida = session.scalar(
        select(ExtractionRun).where(
            ExtractionRun.image_id == imagen.id,
            ExtractionRun.package_version == package_version,
            ExtractionRun.config_hash == config_hash,
        )
    )
    return corrida is not None


def save_extraction(
    session: Session,
    *,
    record: Any,
    package_version: str,
    config_hash: str,
    raw_payload: dict[str, Any] | None = None,
) -> ExtractionRun:
    """Persiste una pasada de extracción completa sobre una fotografía.

    Guarda la imagen, sus recortes, la corrida y todas las lecturas, válidas e
    inválidas. Las inválidas se conservan con su motivo porque saber cuántas
    fallaron y por qué es lo que permite mejorar la extracción.

    Esta es la capa Bronze: **aquí no se corrige ni se rellena nada**. Es fiel
    a lo que dio la imagen.
    """
    imagen = get_or_create_image(
        session,
        sha256=record.sha256,
        original_name=record.file,
        width=record.width,
        height=record.height,
        captured_at=datetime.fromisoformat(record.captured_at) if record.captured_at else None,
        blurred_faces=record.blurred_faces,
    )

    motores = {r.ocr_engine for r in record.readings if r.ocr_engine != "n/a"}
    run = ExtractionRun(
        image_id=imagen.id,
        package_version=package_version,
        ocr_engine=",".join(sorted(motores)) or "n/a",
        config_hash=config_hash,
        raw_payload=raw_payload,
    )
    session.add(run)
    session.flush()

    for lectura in record.readings:
        crop = None
        if lectura.crop_path and lectura.bbox:
            crop = upsert_crop(
                session,
                image=imagen,
                region=lectura.fuel_type,
                bbox=lectura.bbox,
                path=lectura.crop_path,
                detection_method=lectura.detection_method or REGION_CALIBRATED,
            )
        session.add(
            PriceReading(
                extraction_run_id=run.id,
                image_crop_id=crop.id if crop else None,
                fuel_type=lectura.fuel_type,
                price_gtq_per_gallon=lectura.price_gtq_per_gallon,
                confidence=lectura.confidence,
                raw_text=lectura.raw_text,
                ocr_engine=lectura.ocr_engine,
                is_valid=lectura.is_valid,
                rejection_reason=lectura.invalid_reason,
                method=METHOD_OCR,
            )
        )
    session.flush()
    return run


# --- Silver ---------------------------------------------------------------------

def upsert_silver_price(
    session: Session,
    *,
    observed_on: date,
    fuel_type: str,
    price_gtq_per_gallon: float,
    method: str = METHOD_OCR,
    price_reading_id: int | None = None,
    brand: str | None = None,
) -> SilverPrice:
    """Registra un precio limpio para un día, combustible y marca."""
    existente = session.scalar(
        select(SilverPrice).where(
            SilverPrice.observed_on == observed_on,
            SilverPrice.fuel_type == fuel_type,
            SilverPrice.brand == brand,
        )
    )
    if existente is not None:
        existente.price_gtq_per_gallon = price_gtq_per_gallon
        existente.method = method
        existente.price_reading_id = price_reading_id
        return existente

    precio = SilverPrice(
        observed_on=observed_on,
        fuel_type=fuel_type,
        price_gtq_per_gallon=price_gtq_per_gallon,
        method=method,
        price_reading_id=price_reading_id,
        brand=brand,
    )
    session.add(precio)
    session.flush()
    return precio


def valid_readings(session: Session) -> list[PriceReading]:
    """Lecturas que pasaron la validación, con su imagen ya cargada."""
    return list(session.scalars(select(PriceReading).where(PriceReading.is_valid)))


# --- Gold -----------------------------------------------------------------------

def replace_gold(session: Session, rows: list[dict[str, Any]]) -> int:
    """Sustituye el conjunto de modelado por uno nuevo.

    Se reemplaza en vez de acumular porque el conjunto es derivado: se
    reconstruye entero a partir de Silver cada vez que cambian los datos o las
    variables, y mezclar dos versiones daría una serie que no corresponde a
    ninguna configuración concreta.
    """
    session.execute(delete(GoldRow))
    session.add_all([GoldRow(**fila) for fila in rows])
    session.flush()
    return len(rows)


# --- Modelos --------------------------------------------------------------------

def record_trained_model(
    session: Session,
    *,
    fuel_type: str,
    horizon_weeks: int,
    algorithm: str,
    dataset_fingerprint: str,
    hyperparameters: dict[str, Any],
    artifact_path: str,
    package_version: str = "unknown",
    metrics: dict[str, Any] | None = None,
) -> TrainedModel:
    """Anota un modelo entrenado con la huella del conjunto que lo produjo.

    Cierra la cadena de custodia: sin esta huella, el linaje termina en el
    conjunto de datos y no llega hasta la predicción.
    """
    existente = session.scalar(
        select(TrainedModel).where(
            TrainedModel.fuel_type == fuel_type,
            TrainedModel.horizon_weeks == horizon_weeks,
            TrainedModel.dataset_fingerprint == dataset_fingerprint,
        )
    )
    if existente is not None:
        existente.hyperparameters = hyperparameters
        existente.artifact_path = artifact_path
        existente.metrics = metrics
        return existente

    modelo = TrainedModel(
        fuel_type=fuel_type,
        horizon_weeks=horizon_weeks,
        algorithm=algorithm,
        dataset_fingerprint=dataset_fingerprint,
        hyperparameters=hyperparameters,
        artifact_path=artifact_path,
        package_version=package_version,
        metrics=metrics,
    )
    session.add(modelo)
    session.flush()
    return modelo
