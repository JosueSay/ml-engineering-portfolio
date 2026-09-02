"""Etapa de extracción: de las fotografías a la capa cruda.

Se ejecuta como script y no como parte del paquete porque es una etapa de
orquestación, no una función que alguien vaya a importar.
"""
from __future__ import annotations

import json
import logging
import sys

from fuel_price_gt.config import load_config
from fuel_price_gt.extraction.extractor import PriceExtractor


def main() -> int:
    """Ejecuta la extracción y reporta cuánto se pudo leer.

    El recuento de lecturas válidas frente al total es la señal de salud de
    la extracción: si cae, el problema está en las fotografías o en la
    calibración, no en el modelo.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = load_config()
    extractor = PriceExtractor(cfg)

    records = extractor.process_directory()
    if not records:
        print("ERROR: no se pudo cargar ninguna imagen de datos/", file=sys.stderr)
        return 1

    path = extractor.save_bronze(records)
    readings = [reading for r in records for reading in r.readings]
    validas = [reading for reading in readings if reading.is_valid]

    print(
        json.dumps(
            {
                "images_processed": len(records),
                "total_readings": len(readings),
                "valid_readings": len(validas),
                "bronze": str(path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
