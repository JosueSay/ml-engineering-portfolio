"""Estado del almacén de modelos: qué hay, qué pesa y con qué datos se entrenó.

Los dos almacenes tienen ciclos de vida opuestos y por eso se informan por
separado: los pesos de terceros se pueden borrar sin pérdida porque se vuelven
a descargar, mientras que un artefacto propio borrado obliga a reentrenar.

El manifiesto es la parte que sí entra al control de versiones. Guarda con qué
conjunto y con qué parámetros se entrenó cada modelo, de modo que exista
registro sin necesidad de versionar binarios.
"""
from __future__ import annotations

import json
from pathlib import Path

from fuel_price_gt.config import load_config, resolve_path


def _human_size(bytes_: int) -> str:
    """Convierte un tamaño en bytes a la unidad que lo hace legible."""
    value = float(bytes_)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def _list_store(directory: Path, title: str, note: str) -> int:
    """Imprime el contenido de un almacén y devuelve cuántos artefactos tiene."""
    print(f"\n{title}")
    print(f"  {note}")
    if not directory.exists():
        print("  (la carpeta no existe)")
        return 0

    files = sorted(p for p in directory.rglob("*") if p.is_file() and p.name != ".gitkeep")
    if not files:
        print("  vacio")
        return 0

    total = 0
    for file in files:
        size = file.stat().st_size
        total += size
        print(f"  {file.relative_to(directory)!s:48} {_human_size(size):>10}")
    print(f"  {'total':48} {_human_size(total):>10}")
    return len(files)


def main() -> int:
    """Informa del estado de los dos almacenes y del manifiesto."""
    cfg = load_config()

    _list_store(
        resolve_path(cfg["paths"]["models_vendor"]),
        "Pesos de terceros",
        "desechables: se vuelven a descargar. Limpiar con: make clean-vendor",
    )
    _list_store(
        resolve_path(cfg["paths"]["models_trained"]),
        "Artefactos propios",
        "producto del entrenamiento. Limpiar con: make clean-trained",
    )

    manifest_path = resolve_path(cfg["paths"]["models"]) / "manifest.json"
    print("\nManifiesto")
    print(f"  {manifest_path.name}: la parte que si entra al control de versiones")
    if not manifest_path.exists():
        print("  no existe todavia; se escribe al entrenar")
        return 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    models = manifest.get("models", [])
    if not models:
        print("  sin entradas")
        return 0

    print(f"\n  {'fuel':14} {'h':>3}  {'rows':>6}  {'ultimo dato':12}  huella del conjunto")
    for m in models:
        print(
            f"  {m['fuel']:14} {m['horizon']:>3}  {m['training_rows']:>6}  "
            f"{m['last_data_date'][:10]:12}  {m['dataset_fingerprint'][:16]}..."
        )
    print(f"\n  {len(models)} modelo(s) registrado(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
