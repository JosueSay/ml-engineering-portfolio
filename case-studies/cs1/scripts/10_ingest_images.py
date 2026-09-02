"""Etapa de ingesta: trae las fotografías de la fuente configurada al disco.

Es el paso que faltaba para que la integración continua deje de omitir las
etapas de datos. Hasta ahora tener la credencial no bastaba, porque nadie la
usaba para descargar nada; el flujo lo comprobaba y seguía omitiendo, en vez de
lanzar una extracción sobre una carpeta vacía.

No falla cuando la fuente remota no está disponible: cae a la carpeta local y lo
declara. Un clon nuevo sin credenciales tiene esa carpeta vacía, y entonces la
etapa siguiente es la que decide qué hacer con la ausencia de datos.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from fuel_price_gt.config import load_config, resolve_path
from fuel_price_gt.ingestion import get_source, ingest_images


def main() -> int:
    """Ejecuta la ingesta y reporta qué se trajo y qué ya estaba."""
    parser = argparse.ArgumentParser(description="Trae las fotografias de la fuente configurada")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximo de fotografias a descargar. Para probar contra una fuente grande",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Cuantas se procesan por lote, para acotar el uso de memoria",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = load_config()

    origen = get_source(cfg)
    reporte = ingest_images(cfg, source=origen, limit=args.limit, batch_size=args.batch_size)

    destino = resolve_path(cfg["paths"]["raw"])
    en_disco = sum(
        1
        for p in destino.rglob("*")
        if p.is_file() and p.suffix.lower() in {".heic", ".heif", ".jpg", ".jpeg", ".png"}
    )

    salida = reporte.as_dict()
    salida["images_on_disk"] = en_disco
    print(json.dumps(salida, ensure_ascii=False, indent=2))

    if en_disco == 0:
        print(
            "AVISO: no hay fotografias en disco. En un clon nuevo es lo esperado, "
            "porque no se versionan. Para traerlas hay que configurar la fuente "
            "remota; ver docs/05_operations.md",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
