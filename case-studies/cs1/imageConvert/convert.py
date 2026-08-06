"""Conversor batch y recursivo de HEIC a JPG. Autonomo, sin dependencias de core/."""

import argparse
import json
import logging
from pathlib import Path

import pillow_heif
from PIL import Image

pillow_heif.register_heif_opener()

MANIFEST_DIR = Path(__file__).resolve().parent / "output"
HEIC_SUFFIXES = {".heic"}
JPEG_QUALITY = 90


def _setup_logger():
    logger = logging.getLogger("imageConvert")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)-7s %(name)s | %(message)s"))
    logger.addHandler(handler)
    return logger


logger = _setup_logger()


def find_heic_files(input_dir):
    """Recorre input_dir recursivamente y devuelve archivos .heic/.HEIC sin duplicados."""
    seen = set()
    files = []
    for path in input_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in HEIC_SUFFIXES:
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(path)
    return sorted(files)


def convert_one(heic_path, input_dir, output_dir):
    """Convierte un .heic a .jpg preservando la ruta relativa a input_dir."""
    relative = heic_path.resolve().relative_to(input_dir.resolve())
    jpg_path = (output_dir / relative).with_suffix(".jpg")

    if jpg_path.exists() and jpg_path.stat().st_mtime >= heic_path.stat().st_mtime:
        logger.info("Saltado (ya actualizado): %s", heic_path)
        return "skipped", str(heic_path), str(jpg_path)

    jpg_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(heic_path)
    image.convert("RGB").save(jpg_path, "JPEG", quality=JPEG_QUALITY)
    logger.info("Convertido: %s -> %s", heic_path, jpg_path)
    return "converted", str(heic_path), str(jpg_path)


def run(input_dir, output_dir, delete=False):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"--input no es un directorio valido: {input_dir}")

    heic_files = find_heic_files(input_dir)
    logger.info("Encontrados %d archivo(s) .heic en %s", len(heic_files), input_dir)

    manifest = {"converted": [], "skipped": [], "errors": []}

    for heic_path in heic_files:
        try:
            status, heic_str, jpg_str = convert_one(heic_path, input_dir, output_dir)
        except Exception as exc:
            logger.error("Error convirtiendo %s: %s", heic_path, exc)
            manifest["errors"].append({"heic": str(heic_path), "error": str(exc)})
            continue

        if status == "converted":
            manifest["converted"].append({"heic": heic_str, "jpg": jpg_str})
            if delete:
                heic_path.unlink()
                logger.info("Eliminado original: %s", heic_path)
        else:
            manifest["skipped"].append({"heic": heic_str, "jpg": jpg_str})

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = MANIFEST_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    logger.info(
        "Resumen: %d convertido(s), %d saltado(s), %d con error. Manifest: %s",
        len(manifest["converted"]),
        len(manifest["skipped"]),
        len(manifest["errors"]),
        manifest_path,
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Convierte imagenes HEIC a JPG de forma recursiva e idempotente."
    )
    parser.add_argument("--input", required=True, help="Directorio de entrada con archivos .heic")
    parser.add_argument("--output", required=True, help="Directorio de salida para los .jpg")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Elimina el .heic original tras una conversion exitosa",
    )
    args = parser.parse_args()

    run(args.input, args.output, delete=args.delete)


if __name__ == "__main__":
    main()
