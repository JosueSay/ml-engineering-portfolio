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
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import cv2

from ..config import load_config, resolve_path
from ..db.models import REGION_CALIBRATED, REGION_DETECTED
from .calibration import PanelCalibration
from .digit_ocr import read_price
from .display_detector import detect_display
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
    # Evidencia: de qué porción de píxeles salió el valor.
    crop_path: str | None = None
    bbox: dict[str, int] | None = None
    detection_method: str | None = None


@dataclass
class ExtractionRecord:
    """Todo lo obtenido de una fotografía, válido o no.

    Es la unidad de la capa cruda: fidelidad al origen, sin corregir nada.
    """
    file: str
    sha256: str
    captured_at: str | None
    blurred_faces: int
    width: int
    height: int
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
        self.calibration = PanelCalibration()
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
            box = self.calibration.absolute_box(name, fuel, image.width, image.height)
            if box is None:
                readings.append(
                    FuelReading(fuel, None, 0.0, "n/a", "", False, "panel_out_of_frame")
                )
                continue

            x0, y0, x1, y1 = box
            panel = arr[y0:y1, x0:x1]

            # Primero se busca el visor por su aspecto. Si en ese trozo de
            # fotografia no hay ninguno, no se intenta leer: un reconocedor
            # sobre carcasa lisa devuelve numeros inventados que entran en la
            # serie sin que nada los detecte.
            deteccion = detect_display(panel)
            if not deteccion.found:
                readings.append(
                    FuelReading(
                        fuel, None, 0.0, "n/a", "", False, "display_not_found",
                        crop_path=str(self._save_crop(image.sha256, fuel, panel) or ""),
                        bbox={"x0": x0, "y0": y0, "x1": x1, "y1": y1},
                        detection_method=REGION_CALIBRATED,
                    )
                )
                continue

            crop = locate_display(deteccion.image)
            reading = read_price(crop.binary_gray_image)

            crop_path = self._save_crop(image.sha256, fuel, deteccion.image)
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
                    crop_path=str(crop_path) if crop_path else None,
                    bbox={"x0": x0, "y0": y0, "x1": x1, "y1": y1},
                    detection_method=REGION_DETECTED,
                )
            )

        return ExtractionRecord(
            file=name,
            sha256=image.sha256,
            captured_at=image.captured_at.isoformat() if image.captured_at else None,
            blurred_faces=privacy.blurred_faces,
            width=image.width,
            height=image.height,
            readings=readings,
        )

    def _save_crop(self, sha256: str, fuel: str, crop_image) -> Path | None:
        """Guarda el recorte de un panel y devuelve su ruta.

        El recorte es la evidencia de qué se leyó: ante una lectura sospechosa
        se puede abrir exactamente esa porción de píxeles. Se nombra por la
        huella de la imagen y no por su nombre de archivo, porque el nombre
        puede repetirse entre lotes y la huella no.

        Un fallo al escribir no detiene la extracción: se pierde la evidencia
        de esa lectura, no la lectura.
        """
        destino = resolve_path(self.cfg["paths"]["interim"])
        destino.mkdir(parents=True, exist_ok=True)
        ruta = destino / f"{sha256[:16]}_{fuel}.png"
        try:
            cv2.imwrite(str(ruta), cv2.cvtColor(crop_image, cv2.COLOR_RGB2BGR))
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo guardar el recorte %s: %s", ruta.name, exc)
            return None
        return ruta

    def _validate(self, value: float | None, confidence: float) -> tuple[bool, str | None]:
        if value is None:
            return False, "ocr_failed"
        if confidence < self.min_confidence:
            return False, f"low_confidence({confidence:.2f})"
        lo, hi = self.valid_range
        if not (lo <= value <= hi):
            return False, f"out_of_plausible_range({value})"
        return True, None

    def process_directory(
        self,
        directory: Path | str | None = None,
        *,
        skip_if: Callable[[str], bool] | None = None,
    ) -> tuple[list[ExtractionRecord], int]:
        """Procesa las fotografías de un directorio y dice cuántas se saltó.

        `skip_if` recibe la huella de cada imagen y decide si ya está procesada.
        Leer una fotografía cuesta segundos, y con un histórico de varios años
        son horas: repetir el trabajo cuando ni el código ni la configuración
        han cambiado no aporta nada.

        La huella se calcula igualmente, porque es lo que identifica la imagen,
        pero el reconocimiento —que es la parte cara— se evita.

        Una imagen que no se puede abrir se registra y se salta: un archivo
        corrupto no debe detener el procesamiento de los demás.
        """
        directory = Path(directory) if directory else resolve_path(self.cfg["paths"]["raw"])
        records: list[ExtractionRecord] = []
        omitidas = 0
        for path in list_images(directory):
            try:
                image = load_image(path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("No se pudo cargar %s: %s", path, exc)
                continue
            if skip_if is not None and skip_if(image.sha256):
                omitidas += 1
                logger.debug("Ya procesada, se omite: %s", path.name)
                continue
            records.append(self.extract_from_image(image))
        if omitidas:
            logger.info("Omitidas %d fotografias ya procesadas sin cambios", omitidas)
        return records, omitidas

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
