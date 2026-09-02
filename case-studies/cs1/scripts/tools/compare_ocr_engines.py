"""Compara motores de reconocimiento sobre los mismos recortes.

Existe para que "mejorar el reconocimiento" sea una afirmación medible y no una
impresión. Cualquier candidato —el clasificador propio, un motor externo o un
modelo entrenado— se juzga con el mismo criterio y sobre los mismos datos.

Mide tres cosas, y la tercera es la que suele olvidarse:

1. Aciertos sobre recortes que sí contienen dígitos.
2. Aciertos ignorando el separador decimal, que se puede recolocar por
   posición y por tanto no exige cambiar de reconocedor.
3. **Invenciones**: cuántas veces devuelve un número sobre un recorte que no
   contiene ningún visor. Un motor que puntúa alto inventando es peor que uno
   que se calla, porque sus errores entran en la serie sin que nadie los vea.
"""
from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2

from fuel_price_gt.config import load_config, resolve_path
from fuel_price_gt.extraction.digit_ocr import SevenSegmentReader, TesseractReader
from fuel_price_gt.extraction.preprocess import locate_display

TOLERANCIA_GTQ = 0.005


@dataclass
class Resultado:
    """Cómo se comportó un motor sobre el conjunto de referencia."""

    motor: str
    aciertos: int = 0
    lecturas: int = 0
    total: int = 0
    acierto_digitos: int = 0
    invenciones: int = 0
    negativos: int = 0
    detalle: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.detalle is None:
            self.detalle = []

    @property
    def exactitud(self) -> float:
        """Porcentaje de recortes leídos con el valor correcto."""
        return 100 * self.aciertos / self.total if self.total else 0.0

    @property
    def digitos_correctos(self) -> float:
        """Porcentaje de recortes cuyos dígitos son correctos, ignorando el punto.

        Separa dos fallos que se confunden en el valor final: leer mal un dígito
        y colocar mal el separador decimal. El segundo se arregla por posición,
        porque un precio en quetzales por galón siempre lleva dos decimales; el
        primero exige otro reconocedor.
        """
        return 100 * self.acierto_digitos / self.total if self.total else 0.0

    @property
    def tasa_invencion(self) -> float:
        """Porcentaje de recortes sin visor donde el motor devolvió un número."""
        return 100 * self.invenciones / self.negativos if self.negativos else 0.0


def _motores() -> dict[str, object]:
    """Motores disponibles en esta máquina."""
    disponibles: dict[str, object] = {"seven_segment": SevenSegmentReader()}
    if shutil.which("tesseract"):
        disponibles["tesseract"] = TesseractReader()
    return disponibles


def _leer(motor: object, ruta: Path) -> tuple[float | None, str]:
    """Pasa un recorte por el preprocesado y el motor indicado."""
    imagen = cv2.imread(str(ruta))
    if imagen is None:
        return None, ""
    crop = locate_display(cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB))
    lectura = motor.read(crop.binary_gray_image)  # type: ignore[attr-defined]
    return lectura.value, lectura.text


def main() -> int:
    """Ejecuta la comparación y devuelve 1 si no hay recortes que medir."""
    cfg = load_config()
    verdad = json.loads(
        (resolve_path("tests/fixtures/ocr_ground_truth.json")).read_text(encoding="utf-8")
    )
    interim = resolve_path(cfg["paths"]["interim"])

    esperados = verdad["readings"]
    negativos = verdad["no_display"]
    if not any((interim / e["crop"]).exists() for e in esperados):
        print(
            f"No hay recortes en {interim}. Ejecutar antes: make extract",
            file=sys.stderr,
        )
        return 1

    motores = _motores()
    if "tesseract" not in motores:
        print("  aviso: tesseract no esta instalado; solo se mide el motor propio")

    resultados: list[Resultado] = []
    for nombre, motor in motores.items():
        r = Resultado(motor=nombre)

        for caso in esperados:
            ruta = interim / caso["crop"]
            if not ruta.exists():
                continue
            r.total += 1
            valor, texto = _leer(motor, ruta)
            esperado_digitos = f"{caso['expected']:.2f}".replace(".", "")
            leidos = "".join(c for c in texto if c.isdigit())

            marca = "-"
            if valor is not None:
                r.lecturas += 1
                if abs(valor - caso["expected"]) <= TOLERANCIA_GTQ:
                    r.aciertos += 1
                    marca = "ok"
                else:
                    marca = f"{valor}"

            nota_digitos = ""
            if leidos == esperado_digitos:
                r.acierto_digitos += 1
                nota_digitos = "  digitos ok, falla el punto"

            completo = "" if caso["digits_complete"] else "  (cortado)"
            r.detalle.append(
                f"    {caso['crop']:34} espera {caso['expected']:>6}  leyo {marca:>10}"
                f"  texto '{texto}'{completo}{nota_digitos}"
            )

        for nombre_negativo in negativos:
            ruta = interim / nombre_negativo
            if not ruta.exists():
                continue
            r.negativos += 1
            valor, _ = _leer(motor, ruta)
            if valor is not None:
                r.invenciones += 1

        resultados.append(r)

    print()
    print("Comparacion de motores de reconocimiento")
    print(f"  tolerancia: {TOLERANCIA_GTQ} GTQ")
    print()
    print(f"  {'motor':16} {'valor ok':>9} {'digitos ok':>11} {'leyo':>8} {'invencion':>12}")
    for r in resultados:
        print(
            f"  {r.motor:16} {r.exactitud:>8.1f}% {r.digitos_correctos:>10.1f}% "
            f"{r.lecturas:>4}/{r.total:<3} {r.tasa_invencion:>9.1f}% ({r.invenciones}/{r.negativos})"
        )

    for r in resultados:
        print()
        print(f"  {r.motor}")
        for linea in r.detalle:
            print(linea)

    print()
    print("  'invencion' es el porcentaje de recortes sin visor donde el motor")
    print("  devolvio un numero. Cuanto mas bajo, mejor: son errores que entran")
    print("  en la serie sin que nada los detecte.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
