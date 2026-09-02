"""Modelo de datos: la cadena de custodia de cada precio.

El eje del caso no es el modelo predictivo sino la trazabilidad. Cada valor que
llega al conjunto de modelado tiene que poder seguirse hacia atrás hasta el
recorte y la fotografía de los que salió, con qué versión del código y con qué
configuración. Sin eso, ante una predicción mala no se puede saber si falló el
modelo o si falló la lectura de la imagen, que son dos problemas distintos con
dos soluciones distintas.

Por eso el modelo es relacional: el linaje es literalmente una cadena de claves
foráneas.

    Image  ->  ImageCrop  ->  ExtractionRun  ->  PriceReading
                                                      |
                                                 SilverPrice
                                                      |
                                                 GoldRow

Lo que no tiene forma fija —el resultado crudo de la extracción, los
hiperparámetros, las variables de modelado— se guarda en columnas de documento
dentro de la misma tabla, en vez de en otro motor.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Clase base declarativa de todas las tablas."""


# --- Cómo se obtuvo un valor -----------------------------------------------------
# Recorre toda la cadena. Distinguir una medida de un valor reconstruido o
# rellenado no es un detalle: una fila imputada que no se distingue de una
# medida es una mentira con formato de dato.
METHOD_OCR = "ocr"
METHOD_ARITHMETIC = "arithmetic"
METHOD_MEAN = "mean_imputed"
METHOD_MEDIAN = "median_imputed"
METHOD_INTERPOLATED = "interpolated"
METHOD_SYNTHETIC = "synthetic"

# Cómo se ubicó la región del panel dentro de la fotografía.
REGION_DETECTED = "detected"
REGION_CALIBRATED = "calibrated"


class Image(Base):
    """Una fotografía tal como llegó, sin editar.

    La huella `sha256` es la identidad: sirve a la vez para deduplicar, para
    saber si un archivo ya se procesó y como llave de caché de la descarga. Dos
    copias del mismo archivo con distinto nombre son la misma imagen.
    """

    __tablename__ = "image"

    id: Mapped[int] = mapped_column(primary_key=True)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    source_uri: Mapped[str | None] = mapped_column(String(1024), default=None)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    brand: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    station: Mapped[str | None] = mapped_column(String(128), default=None)
    width: Mapped[int | None] = mapped_column(Integer, default=None)
    height: Mapped[int | None] = mapped_column(Integer, default=None)
    blurred_faces: Mapped[int] = mapped_column(Integer, default=0)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    crops: Mapped[list[ImageCrop]] = relationship(back_populates="image", cascade="all, delete-orphan")
    extraction_runs: Mapped[list[ExtractionRun]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Image(id={self.id!r}, name={self.original_name!r})"


class ImageCrop(Base):
    """La porción de píxeles de la que se leyó un precio.

    No es solo un ahorro de cómputo: es la evidencia. Ante una lectura
    sospechosa se puede abrir exactamente el recorte que la produjo.

    `detection_method` dice si la región se encontró por sus características o
    si se cayó al encuadre calibrado. Sin ese dato no se puede separar un fallo
    de localización de un fallo de lectura al analizar los rechazos.
    """

    __tablename__ = "image_crop"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("image.id"), index=True)
    region: Mapped[str] = mapped_column(String(32))
    bbox: Mapped[dict[str, Any]] = mapped_column(JSON)
    path: Mapped[str] = mapped_column(String(1024))
    detection_method: Mapped[str] = mapped_column(String(16), default=REGION_CALIBRATED)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    image: Mapped[Image] = relationship(back_populates="crops")
    readings: Mapped[list[PriceReading]] = relationship(back_populates="crop")

    __table_args__ = (UniqueConstraint("image_id", "region", name="uq_crop_image_region"),)

    def __repr__(self) -> str:
        return f"ImageCrop(id={self.id!r}, region={self.region!r})"


class ExtractionRun(Base):
    """Una pasada de extracción sobre una fotografía.

    Guarda con qué versión del paquete, con qué motor y con qué configuración
    se leyó. Es lo que permite comparar dos corridas sobre la misma imagen y
    saber qué cambió entre ellas.
    """

    __tablename__ = "extraction_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("image.id"), index=True)
    package_version: Mapped[str] = mapped_column(String(32))
    ocr_engine: Mapped[str] = mapped_column(String(32))
    config_hash: Mapped[str] = mapped_column(String(64))
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    executed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    image: Mapped[Image] = relationship(back_populates="extraction_runs")
    readings: Mapped[list[PriceReading]] = relationship(
        back_populates="extraction_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"ExtractionRun(id={self.id!r}, image_id={self.image_id!r})"


class PriceReading(Base):
    """Un precio leído, o el motivo por el que no se pudo leer.

    Las lecturas inválidas se conservan con su motivo en vez de descartarse:
    saber cuántas fallaron y por qué es lo que permite mejorar la extracción.
    Esta es la capa Bronze, y aquí **nunca** se rellena ni se corrige nada: es
    fiel a lo que dio la imagen.
    """

    __tablename__ = "price_reading"

    id: Mapped[int] = mapped_column(primary_key=True)
    extraction_run_id: Mapped[int] = mapped_column(ForeignKey("extraction_run.id"), index=True)
    image_crop_id: Mapped[int | None] = mapped_column(ForeignKey("image_crop.id"), default=None)
    fuel_type: Mapped[str] = mapped_column(String(16), index=True)
    price_gtq_per_gallon: Mapped[float | None] = mapped_column(Float, default=None)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    raw_text: Mapped[str] = mapped_column(String(64), default="")
    # Que motor produjo esta lectura en concreto. La corrida guarda el conjunto
    # de motores usados, pero dentro de una misma fotografia cada panel puede
    # haberse resuelto con uno distinto: se queda el de mayor confianza.
    ocr_engine: Mapped[str] = mapped_column(String(32), default="n/a")
    is_valid: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(64), default=None)
    method: Mapped[str] = mapped_column(String(24), default=METHOD_OCR)

    extraction_run: Mapped[ExtractionRun] = relationship(back_populates="readings")
    crop: Mapped[ImageCrop | None] = relationship(back_populates="readings")
    silver_prices: Mapped[list[SilverPrice]] = relationship(back_populates="reading")

    def __repr__(self) -> str:
        return f"PriceReading(id={self.id!r}, fuel={self.fuel_type!r}, price={self.price_gtq_per_gallon!r})"


class SilverPrice(Base):
    """Un precio limpio, ya fechado y listo para la serie.

    Aquí sí puede haber valores que no salieron de una lectura directa: la
    reconstrucción aritmética a partir del total pagado y el volumen cargado
    produce filas legítimas. El campo `method` dice siempre cuál es cuál.
    """

    __tablename__ = "silver_price"

    id: Mapped[int] = mapped_column(primary_key=True)
    observed_on: Mapped[date] = mapped_column(Date, index=True)
    fuel_type: Mapped[str] = mapped_column(String(16), index=True)
    price_gtq_per_gallon: Mapped[float] = mapped_column(Float)
    price_reading_id: Mapped[int | None] = mapped_column(ForeignKey("price_reading.id"), default=None)
    method: Mapped[str] = mapped_column(String(24), default=METHOD_OCR)
    brand: Mapped[str | None] = mapped_column(String(64), default=None, index=True)

    reading: Mapped[PriceReading | None] = relationship(back_populates="silver_prices")
    gold_rows: Mapped[list[GoldRow]] = relationship(back_populates="silver_price")

    __table_args__ = (
        UniqueConstraint("observed_on", "fuel_type", "brand", name="uq_silver_day_fuel_brand"),
    )

    def __repr__(self) -> str:
        return f"SilverPrice(on={self.observed_on!r}, fuel={self.fuel_type!r})"


class GoldRow(Base):
    """Una fila del conjunto de modelado, con su procedencia.

    `source` distingue lo medido de lo generado, y `silver_price_id` enlaza con
    el precio del que salió cuando existe. Una fila sintética no tiene enlace, y
    eso mismo la identifica.
    """

    __tablename__ = "gold_row"

    id: Mapped[int] = mapped_column(primary_key=True)
    observed_on: Mapped[date] = mapped_column(Date, index=True)
    fuel_type: Mapped[str] = mapped_column(String(16), index=True)
    price_gtq_per_gallon: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, Any]] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(16), index=True)
    method: Mapped[str] = mapped_column(String(24), default=METHOD_OCR)
    silver_price_id: Mapped[int | None] = mapped_column(ForeignKey("silver_price.id"), default=None)

    silver_price: Mapped[SilverPrice | None] = relationship(back_populates="gold_rows")

    __table_args__ = (UniqueConstraint("observed_on", "fuel_type", name="uq_gold_day_fuel"),)

    def __repr__(self) -> str:
        return f"GoldRow(on={self.observed_on!r}, fuel={self.fuel_type!r}, source={self.source!r})"


class TrainedModel(Base):
    """Un modelo entrenado, con la huella del conjunto que lo produjo.

    Cierra la cadena: sin esta huella el linaje se corta en el conjunto de datos
    y no llega hasta la predicción.
    """

    __tablename__ = "trained_model"

    id: Mapped[int] = mapped_column(primary_key=True)
    fuel_type: Mapped[str] = mapped_column(String(16), index=True)
    horizon_weeks: Mapped[int] = mapped_column(Integer)
    algorithm: Mapped[str] = mapped_column(String(32))
    dataset_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    hyperparameters: Mapped[dict[str, Any]] = mapped_column(JSON)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    artifact_path: Mapped[str] = mapped_column(String(1024))
    package_version: Mapped[str] = mapped_column(String(32), default="unknown")
    trained_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("fuel_type", "horizon_weeks", "dataset_fingerprint", name="uq_model_run"),
    )

    def __repr__(self) -> str:
        return f"TrainedModel(fuel={self.fuel_type!r}, h={self.horizon_weeks!r})"
