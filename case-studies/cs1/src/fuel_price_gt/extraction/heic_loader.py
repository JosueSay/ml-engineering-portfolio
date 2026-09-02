"""Carga de imágenes HEIC (formato nativo de iPhone) a arrays RGB + metadatos EXIF.

Los tótems/dispensores se fotografían con celular en formato HEIC. Este módulo
aísla la dependencia de `pillow-heif` y expone también la fecha/hora real de
captura (EXIF DateTimeOriginal), que es la señal de "día y hora" que el
negocio pide usar para la recomendación final.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pillow_heif
from PIL import Image
from PIL.ExifTags import TAGS

logger = logging.getLogger(__name__)


@dataclass
class LoadedImage:
    """Imagen en memoria junto con su fecha real de captura.

    La fecha sale de los metadatos del archivo, no de cuándo se procesó: es
    la que ancla cada precio en la serie temporal. Puede ser `None` si los
    metadatos se perdieron, y entonces esa lectura no puede fecharse.
    """
    path: Path
    array: np.ndarray          # HxWx3 uint8 RGB
    captured_at: datetime | None
    width: int
    height: int


def _extract_original_datetime(heif_file) -> datetime | None:
    exif_bytes = heif_file.info.get("exif")
    if not exif_bytes:
        return None
    try:
        img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
        img.info["exif"] = exif_bytes
        exifdata = img.getexif()
        exif_ifd = exifdata.get_ifd(0x8769)  # Exif IFD pointer
        raw = exif_ifd.get(36867) or exif_ifd.get(36868)  # DateTimeOriginal / Digitized
        if raw is None:
            for tag_id, value in exifdata.items():
                if TAGS.get(tag_id) == "DateTime":
                    raw = value
                    break
        if raw is None:
            return None
        return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None


def load_heic(path: Path | str) -> LoadedImage:
    """Carga un archivo .HEIC devolviendo el array RGB y la fecha/hora EXIF real."""
    path = Path(path)
    heif_file = pillow_heif.open_heif(path, convert_hdr_to_8bit=True)
    img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw").convert("RGB")
    arr = np.array(img)
    captured_at = _extract_original_datetime(heif_file)
    return LoadedImage(
        path=path,
        array=arr,
        captured_at=captured_at,
        width=arr.shape[1],
        height=arr.shape[0],
    )


def list_images(directory: Path | str) -> list[Path]:
    """Fotografías de un directorio, en orden estable.

    El orden fijo hace que dos corridas sobre el mismo directorio produzcan
    la capa cruda en la misma secuencia, que es lo que permite compararlas.
    """
    directory = Path(directory)
    exts = {".heic", ".HEIC", ".jpg", ".jpeg", ".JPG", ".JPEG", ".png", ".PNG"}
    return sorted(p for p in directory.iterdir() if p.suffix in exts)


def load_image(path: Path | str) -> LoadedImage:
    """Carga HEIC o cualquier formato soportado por Pillow, de forma transparente."""
    path = Path(path)
    if path.suffix.lower() == ".heic":
        return load_heic(path)
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    captured_at = None
    try:
        exifdata = img.getexif()
        exif_ifd = exifdata.get_ifd(0x8769)
        raw = exif_ifd.get(36867)
        if raw:
            captured_at = datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except Exception as exc:  # noqa: BLE001  # EXIF ausente o corrupto no debe abortar la carga
        logger.warning("Sin fecha EXIF utilizable en %s: %s", path.name, exc)
    return LoadedImage(path=path, array=arr, captured_at=captured_at, width=arr.shape[1], height=arr.shape[0])
