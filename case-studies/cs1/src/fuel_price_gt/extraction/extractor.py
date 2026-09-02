"""Orquestador de extracción: imagen de tótem -> pares (tipo_combustible, precio).

Implementa la interfaz de extracción pedida por el negocio: "el sistema debe
poder recibir una imagen, procesarla y devolver un formato estructurado
(tipo de combustible -> precio)". Aplica también las reglas de validación
que exige el documento de negocio (R6/R7): nivel de confianza mínimo y rango
de precio plausible; ante la duda, descarta (null) en vez de inventar.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from ..config import load_config, resolve_path
from .calibration import PanelCalibration
from .digit_ocr import read_price
from .heic_loader import LoadedImage, list_images, load_image
from .preprocess import locate_display
from .privacy import apply_privacy_filter

logger = logging.getLogger(__name__)


@dataclass
class FuelReading:
    """Un precio leído, o el motivo por el que no se pudo leer.

    Las lecturas inválidas se conservan con su motivo en vez de descartarse:
    saber cuántas fallaron y por qué es lo que permite mejorar la extracción.
    """
    fuel_type: str
    price_gtq_per_gallon: float | None
    confidence: float
    ocr_engine: str
    raw_text: str
    is_valid: bool
    invalid_reason: str | None


@dataclass
class ExtractionRecord:
    """Todo lo obtenido de una fotografía, válido o no.

    Es la unidad de la capa cruda: fidelidad al origen, sin corregir nada.
    """
    file: str
    captured_at: str | None
    blurred_faces: int
    readings: list[FuelReading]


class PriceExtractor:
    """Encadena las etapas de extracción y valida lo que sale.

    Implementa la interfaz que pide el negocio: recibe una imagen y devuelve
    pares de tipo de combustible y precio. Ante la duda escribe nulo con su
    motivo en vez de inventar un valor; un precio inventado contamina la
    serie y nadie se entera.
    """
    def __init__(self, config: dict | None = None):
        self.cfg = config or load_config()
        self.calibracion = PanelCalibration()
        ext_cfg = self.cfg["extraction"]
        self.fuel_order: list[str] = ext_cfg["fuel_order"]
        self.valid_range = tuple(ext_cfg["valid_price_range_gtq"])
        self.min_confidence = float(ext_cfg["min_confidence"])

    def extract_from_image(self, image: LoadedImage) -> ExtractionRecord:
        """Procesa una fotografía y devuelve sus cuatro lecturas."""
        privacy = apply_privacy_filter(image.array)
        arr = privacy.image
        name = image.path.name

        readings: list[FuelReading] = []
        for fuel in self.fuel_order:
            box = self.calibracion.absolute_box(name, fuel, image.width, image.height)
            if box is None:
                readings.append(
                    FuelReading(fuel, None, 0.0, "n/a", "", False, "panel_out_of_frame")
                )
                continue

            x0, y0, x1, y1 = box
            panel = arr[y0:y1, x0:x1]
            crop = locate_display(panel)
            reading = read_price(crop.binary_gray_image)

            is_valid, reason = self._validate(reading.value, reading.confidence)
            readings.append(
                FuelReading(
                    fuel_type=fuel,
                    price_gtq_per_gallon=reading.value if is_valid else None,
                    confidence=round(reading.confidence, 3),
                    ocr_engine=reading.engine,
                    raw_text=reading.text,
                    is_valid=is_valid,
                    invalid_reason=reason,
                )
            )

        return ExtractionRecord(
            file=name,
            captured_at=image.captured_at.isoformat() if image.captured_at else None,
            blurred_faces=privacy.blurred_faces,
            readings=readings,
        )

    def _validate(self, value: float | None, confidence: float) -> tuple[bool, str | None]:
        if value is None:
            return False, "ocr_failed"
        if confidence < self.min_confidence:
            return False, f"low_confidence({confidence:.2f})"
        lo, hi = self.valid_range
        if not (lo <= value <= hi):
            return False, f"fuera_de_rango_plausible({value})"
        return True, None

    def process_directory(self, directory: Path | str | None = None) -> list[ExtractionRecord]:
        """Procesa todas las fotografías de un directorio.

        Una imagen que no se puede abrir se registra y se salta: un archivo
        corrupto no debe detener el procesamiento de los demás.
        """
        directory = Path(directory) if directory else resolve_path(self.cfg["paths"]["raw"])
        records = []
        for path in list_images(directory):
            try:
                image = load_image(path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("No se pudo cargar %s: %s", path, exc)
                continue
            records.append(self.extract_from_image(image))
        return records

    def save_bronze(self, records: list[ExtractionRecord]) -> Path:
        """Escribe la capa cruda, un archivo por corrida.

        No se sobreescribe la anterior: cada corrida queda como evidencia de
        qué leyó esa versión del código sobre ese conjunto de fotografías.
        """
        bronze_dir = resolve_path(self.cfg["paths"]["bronze"])
        bronze_dir.mkdir(parents=True, exist_ok=True)
        output = bronze_dir / f"extraction_{datetime.now():%Y%m%dT%H%M%S}.json"
        payload = [asdict(r) for r in records]
        with open(output, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        logger.info("Bronze guardado en %s (%d imágenes)", output, len(records))
        return output
