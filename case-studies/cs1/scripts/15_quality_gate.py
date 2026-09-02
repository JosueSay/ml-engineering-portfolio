"""Compuerta de calidad: decide si el modelo entrenado puede seguir adelante.

Devuelve un código de salida distinto de cero cuando no pasa, para que la
integración continua detenga la cadena en vez de publicar un modelo peor
que repetir el último precio conocido.
"""
from __future__ import annotations

import sys

import pandas as pd

from gasolina_gt.config import load_config, resolve_path

CRITERIOS = ("supera_baseline", "cumple_mae", "cumple_f1")
FUENTES_SIN_ANCLAS_REALES = ("sintetico",)


def main() -> int:
    """Aplica la compuerta de calidad y decide si la corrida pasa."""
    cfg = load_config()
    ruta = resolve_path(cfg["paths"]["reports"]) / cfg["archivos"]["evaluacion"]
    if not ruta.exists():
        print(f"ERROR: no existe {ruta}. ¿Corrió la etapa de entrenamiento?", file=sys.stderr)
        return 1

    df = pd.read_csv(ruta)
    if df.empty:
        print(f"ERROR: {ruta} está vacío.", file=sys.stderr)
        return 1

    fallos: list[str] = []
    advertencias: list[str] = []
    print(f"Compuerta de calidad sobre {len(df)} horizonte(s) evaluado(s)\n")

    for _, fila in df.iterrows():
        etiqueta = f"{fila['combustible']} h={fila['horizonte']}"
        bloqueante = fila["fuente_datos"] not in FUENTES_SIN_ANCLAS_REALES
        modo = "bloqueante" if bloqueante else "informativo"

        print(
            f"  {etiqueta} [{modo}]: MAE={fila['mae_modelo']:.4f} "
            f"(baseline {fila['mae_baseline']:.4f}, mejora {fila['mejora_vs_baseline_pct']:+.2f}%) "
            f"F1_tendencia={fila['f1_tendencia_modelo']:.4f} fuente={fila['fuente_datos']}"
        )

        for criterio in CRITERIOS:
            if bool(fila[criterio]):
                continue
            mensaje = f"{etiqueta}: no cumple '{criterio}'"
            if bloqueante and criterio == "supera_baseline":
                fallos.append(mensaje)
            else:
                advertencias.append(mensaje)

    print()
    for advertencia in advertencias:
        print(f"  ADVERTENCIA {advertencia}")

    if fallos:
        print("\nCOMPUERTA DE CALIDAD: FALLIDA", file=sys.stderr)
        for fallo in fallos:
            print(f"  - {fallo}", file=sys.stderr)
        return 1

    if advertencias:
        print("\nCOMPUERTA DE CALIDAD: APROBADA CON ADVERTENCIAS")
        print("El dataset Gold no contiene anclas reales validadas, así que los")
        print("criterios de calidad se evalúan en modo informativo. La compuerta")
        print("pasará a ser bloqueante en cuanto la extracción produzca lecturas reales.")
        return 0

    print("\nCOMPUERTA DE CALIDAD: APROBADA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
