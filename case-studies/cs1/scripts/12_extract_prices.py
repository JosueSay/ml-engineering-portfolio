"""Etapa de extracción: de las fotografías a la capa cruda.

Escribe en dos sitios y no es redundancia. La base de datos es la fuente de
verdad, porque es la única que puede responder de qué fotografía y de qué
recorte salió cada precio. El archivo por corrida es una exportación: sirve
para revisar una pasada concreta sin abrir la base, y es lo que la integración
continua publica como artefacto.

Se ejecuta como script y no como parte del paquete porque es una etapa de
orquestación, no una función que alguien vaya a importar.
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict

from fuel_price_gt.config import load_config, resolve_path
from fuel_price_gt.db import (
    already_extracted,
    config_fingerprint,
    create_schema,
    save_extraction,
    session_scope,
)
from fuel_price_gt.extraction.extractor import PriceExtractor
from fuel_price_gt.extraction.heic_loader import file_fingerprint, list_images
from fuel_price_gt.modeling.training import package_version


def _huellas_en_disco(extractor: PriceExtractor) -> list[str]:
    """Huellas de las fotografias disponibles, sin llegar a reconocer nada.

    Calcular la huella exige leer el archivo, que es barato; lo caro es el
    reconocimiento. Separar las dos cosas permite saber que hay antes de
    decidir que procesar.
    """
    directorio = resolve_path(load_config()["paths"]["raw"])
    return [file_fingerprint(p) for p in list_images(directorio)]


def main() -> int:
    """Ejecuta la extracción, la persiste y reporta cuánto se pudo leer.

    El recuento de lecturas válidas frente al total es la señal de salud de la
    extracción: si cae, el problema está en las fotografías o en la
    calibración, no en el modelo.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = load_config()
    extractor = PriceExtractor(cfg)

    create_schema()
    huella_config = config_fingerprint(cfg)
    version = package_version()

    # Se consulta la base antes de leer: si una fotografia ya se proceso con
    # este mismo codigo y esta misma configuracion, el resultado seria identico.
    with session_scope() as sesion:
        procesadas = {
            sha
            for sha in _huellas_en_disco(extractor)
            if already_extracted(
                sesion, sha256=sha, package_version=version, config_hash=huella_config
            )
        }

    records, omitidas = extractor.process_directory(skip_if=lambda sha: sha in procesadas)
    if not records and not omitidas:
        print(
            "ERROR: no se pudo cargar ninguna imagen de data/raw. "
            "En un clon nuevo esa carpeta esta vacia a proposito: las "
            "fotografias no se versionan y hay que traerlas de la fuente.",
            file=sys.stderr,
        )
        return 1

    export_path = extractor.save_bronze(records) if records else None

    with session_scope() as sesion:
        for record in records:
            save_extraction(
                sesion,
                record=record,
                package_version=version,
                config_hash=huella_config,
                # El resultado tal cual, en columna de documento: si mañana la
                # extraccion devuelve un campo nuevo, queda guardado sin migrar
                # el esquema, y la evidencia cruda no se pierde.
                raw_payload=asdict(record),
            )

    readings = [lectura for r in records for lectura in r.readings]
    valid = [lectura for lectura in readings if lectura.is_valid]
    with_crop = [lectura for lectura in readings if lectura.crop_path]

    # Los motivos de rechazo agrupados dicen dónde está el problema: si domina
    # el encuadre, falla la calibración; si domina la lectura, falla el OCR.
    motivos: dict[str, int] = {}
    for lectura in readings:
        if not lectura.is_valid and lectura.invalid_reason:
            clave = lectura.invalid_reason.split("(")[0]
            motivos[clave] = motivos.get(clave, 0) + 1

    print(
        json.dumps(
            {
                "images_processed": len(records),
                "total_readings": len(readings),
                "valid_readings": len(valid),
                "crops_saved": len(with_crop),
                "skipped_cached": omitidas,
                "rejection_reasons": dict(sorted(motivos.items(), key=lambda kv: -kv[1])),
                "bronze_export": str(export_path) if export_path else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if not valid:
        print(
            "AVISO: ninguna lectura valida. El conjunto de modelado sera "
            "sintetico y la compuerta de calidad pasara a modo informativo.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
