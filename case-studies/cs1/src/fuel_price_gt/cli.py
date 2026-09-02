"""Interfaz de línea de comandos del proyecto."""
from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict

from .data.pipeline import build_gold, build_silver, load_gold_if_exists
from .db import create_schema
from .evaluation import evaluate_artifact, save_report
from .modeling import train_all_horizons
from .serving import recommend_refuel


def _gold() -> object:
    gold = load_gold_if_exists()
    return gold if gold is not None else build_gold()


def main() -> None:
    """Punto de entrada de la línea de comandos.

    Cada subcomando es una etapa del pipeline y se puede ejecutar por
    separado: encadenarlas todas en un solo comando obligaría a repetir
    trabajo ya hecho cada vez que falla la última.
    """
    parser = argparse.ArgumentParser(prog="fuel-price-gt", description="Predicción de precios de combustible en Guatemala")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-data", help="Ejecuta Bronze → Silver → Gold")
    p_train = sub.add_parser("train", help="Entrena y evalúa horizontes configurados")
    p_train.add_argument("--fuel", default=None)
    p_rec = sub.add_parser("recommend", help="Da la recomendación de carga")
    p_rec.add_argument("--fuel", default=None)
    p_rec.add_argument("--horizon", type=int, default=1, choices=(1, 2, 4))
    p_rec.add_argument("--hour", type=int, default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # El punto de entrada garantiza sus precondiciones. Sin esto, cada consulta
    # tendria que defenderse por su cuenta de que la base no exista todavia, y
    # bastaria una sin proteger para que la distribucion recien instalada
    # fallara con un error de SQL en vez de decir que aun no hay datos.
    create_schema()

    if args.command == "build-data":
        silver = build_silver()
        gold = build_gold(silver)
        print(json.dumps({"silver_rows": len(silver), "gold_rows": len(gold), "gold_sources": gold["source"].value_counts().to_dict()}, ensure_ascii=False))
        return
    if args.command == "train":
        results = train_all_horizons(_gold(), args.fuel)
        evaluations = [evaluate_artifact(artifact) for artifact, _ in results]
        path = save_report(evaluations)
        print(json.dumps({"models": [asdict(meta) for _, meta in results], "evaluation": [asdict(x) for x in evaluations], "report": str(path)}, ensure_ascii=False, indent=2))
        return
    print(json.dumps(asdict(recommend_refuel(_gold(), args.fuel, args.horizon, args.hour)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
