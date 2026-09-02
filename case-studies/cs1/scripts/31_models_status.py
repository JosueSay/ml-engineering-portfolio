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

from gasolina_gt.config import load_config, resolve_path


def _tamano_legible(bytes_: int) -> str:
    """Convierte un tamaño en bytes a la unidad que lo hace legible."""
    valor = float(bytes_)
    for unidad in ("B", "KB", "MB", "GB"):
        if valor < 1024 or unidad == "GB":
            return f"{valor:.0f} {unidad}" if unidad == "B" else f"{valor:.1f} {unidad}"
        valor /= 1024
    return f"{valor:.1f} GB"


def _listar(directorio: Path, titulo: str, nota: str) -> int:
    """Imprime el contenido de un almacén y devuelve cuántos artefactos tiene."""
    print(f"\n{titulo}")
    print(f"  {nota}")
    if not directorio.exists():
        print("  (la carpeta no existe)")
        return 0

    archivos = sorted(p for p in directorio.rglob("*") if p.is_file() and p.name != ".gitkeep")
    if not archivos:
        print("  vacio")
        return 0

    total = 0
    for archivo in archivos:
        tamano = archivo.stat().st_size
        total += tamano
        print(f"  {archivo.relative_to(directorio)!s:48} {_tamano_legible(tamano):>10}")
    print(f"  {'total':48} {_tamano_legible(total):>10}")
    return len(archivos)


def main() -> int:
    """Informa del estado de los dos almacenes y del manifiesto."""
    cfg = load_config()

    _listar(
        resolve_path(cfg["paths"]["models_vendor"]),
        "Pesos de terceros",
        "desechables: se vuelven a descargar. Limpiar con: make clean-vendor",
    )
    _listar(
        resolve_path(cfg["paths"]["models_trained"]),
        "Artefactos propios",
        "producto del entrenamiento. Limpiar con: make clean-trained",
    )

    ruta_manifiesto = resolve_path(cfg["paths"]["models"]) / "manifest.json"
    print("\nManifiesto")
    print(f"  {ruta_manifiesto.name}: la parte que si entra al control de versiones")
    if not ruta_manifiesto.exists():
        print("  no existe todavia; se escribe al entrenar")
        return 0

    manifiesto = json.loads(ruta_manifiesto.read_text(encoding="utf-8"))
    modelos = manifiesto.get("modelos", [])
    if not modelos:
        print("  sin entradas")
        return 0

    print(f"\n  {'combustible':14} {'h':>3}  {'filas':>6}  {'ultimo dato':12}  huella del conjunto")
    for m in modelos:
        print(
            f"  {m['combustible']:14} {m['horizonte']:>3}  {m['filas_entrenamiento']:>6}  "
            f"{m['fecha_ultimo_dato'][:10]:12}  {m['huella_dataset'][:16]}..."
        )
    print(f"\n  {len(modelos)} modelo(s) registrado(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
