"""Compuerta de calidad: decide si el modelo entrenado puede seguir adelante.

Devuelve un código de salida distinto de cero cuando no pasa, para que la
integración continua detenga la cadena en vez de publicar un modelo peor
que repetir el último precio conocido.
"""
from __future__ import annotations

import sys

import pandas as pd

from fuel_price_gt.config import load_config, resolve_path

CRITERIOS = ("beats_baseline", "meets_mae", "meets_f1")
FUENTES_SIN_ANCLAS_REALES = ("synthetic",)


def main() -> int:
    """Aplica la compuerta de calidad y decide si la corrida pasa."""
    cfg = load_config()
    path = resolve_path(cfg["paths"]["reports"]) / cfg["files"]["evaluation"]
    if not path.exists():
        print(f"ERROR: no existe {path}. ¿Corrió la etapa de entrenamiento?", file=sys.stderr)
        return 1

    df = pd.read_csv(path)
    if df.empty:
        print(f"ERROR: {path} está vacío.", file=sys.stderr)
        return 1

    fallos: list[str] = []
    warnings: list[str] = []
    print(f"Compuerta de calidad sobre {len(df)} horizonte(s) evaluado(s)\n")

    for _, fila in df.iterrows():
        etiqueta = f"{fila['fuel']} h={fila['horizon']}"
        bloqueante = fila["data_source"] not in FUENTES_SIN_ANCLAS_REALES
        modo = "blocking" if bloqueante else "informational"

        print(
            f"  {etiqueta} [{modo}]: MAE={fila['mae_model']:.4f} "
            f"(baseline {fila['mae_baseline']:.4f}, mejora {fila['improvement_vs_baseline_pct']:+.2f}%) "
            f"F1_tendencia={fila['f1_trend_model']:.4f} fuente={fila['data_source']}"
        )

        for criterio in CRITERIOS:
            if bool(fila[criterio]):
                continue
            message = f"{etiqueta}: no cumple '{criterio}'"
            if bloqueante and criterio == "beats_baseline":
                fallos.append(message)
            else:
                warnings.append(message)

    print()
    for warning in warnings:
        print(f"  ADVERTENCIA {warning}")

    if fallos:
        print("\nCOMPUERTA DE CALIDAD: FALLIDA", file=sys.stderr)
        for fallo in fallos:
            print(f"  - {fallo}", file=sys.stderr)
        return 1

    if warnings:
        print("\nCOMPUERTA DE CALIDAD: APROBADA CON ADVERTENCIAS")
        print("El dataset Gold no contiene anclas reales validadas, así que los")
        print("criterios de calidad se evalúan en modo informativo. La compuerta")
        print("pasará a ser bloqueante en cuanto la extracción produzca lecturas reales.")
        return 0

    print("\nCOMPUERTA DE CALIDAD: APROBADA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
