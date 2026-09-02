"""Etapa de extracción: de las fotografías a la capa cruda.

Se ejecuta como script y no como parte del paquete porque es una etapa de
orquestación, no una función que alguien vaya a importar.
"""
from __future__ import annotations

import json
import logging
import sys

from gasolina_gt.config import load_config
from gasolina_gt.extraction.extractor import ExtractorPrecios


def main() -> int:
    """Ejecuta la extracción y reporta cuánto se pudo leer.

    El recuento de lecturas válidas frente al total es la señal de salud de
    la extracción: si cae, el problema está en las fotografías o en la
    calibración, no en el modelo.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = load_config()
    extractor = ExtractorPrecios(cfg)

    registros = extractor.procesar_directorio()
    if not registros:
        print("ERROR: no se pudo cargar ninguna imagen de datos/", file=sys.stderr)
        return 1

    ruta = extractor.guardar_bronze(registros)
    lecturas = [lectura for r in registros for lectura in r.lecturas]
    validas = [lectura for lectura in lecturas if lectura.valido]

    print(
        json.dumps(
            {
                "imagenes_procesadas": len(registros),
                "lecturas_totales": len(lecturas),
                "lecturas_validas": len(validas),
                "bronze": str(ruta),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
