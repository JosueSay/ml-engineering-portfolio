"""Recuperación de precios que no se pudieron leer.

Con fotografías tomadas en la calle siempre habrá lecturas que no salgan, y ese
es el estado normal, no una avería. Lo que decide la calidad del caso no es leer
el cien por cien sino qué se hace con lo que falta.

Hay dos maneras de recuperar un valor, y son muy distintas entre sí:

**Reconstrucción aritmética.** La fotografía suele traer más de un dato: el
volumen cargado y el total pagado. Con esos dos el precio unitario sale por
división, sin inventar nada. Es un valor tan real como el leído, solo que
obtenido por otra vía.

    p = total pagado / galones cargados

**Relleno estadístico.** Cuando no hay ninguna redundancia que explotar, se
estima a partir de la propia serie. Aquí sí se está poniendo un número donde no
había medida, y por eso la marca importa: quien use ese dato tiene que poder
saber que es una estimación.

La regla que atraviesa todo el módulo: **cada valor recuperado se marca con el
método que lo produjo**. Una fila rellenada que no se distingue de una medida es
una mentira con formato de dato.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from ..db.models import (
    METHOD_ARITHMETIC,
    METHOD_INTERPOLATED,
    METHOD_MEAN,
    METHOD_MEDIAN,
    METHOD_OCR,
)

logger = logging.getLogger(__name__)

# Un galón son 3.785411784 litros. La conversión hace falta porque el
# dispensador puede marcar el volumen en litros mientras el precio se publica
# por galón, y mezclarlos daría un precio casi cuatro veces menor.
LITROS_POR_GALON = 3.785411784


@dataclass
class RecoveredPrice:
    """Un precio recuperado, con la constancia de cómo se obtuvo."""

    price_gtq_per_gallon: float
    method: str
    note: str = ""


def recover_from_total(
    total_paid_gtq: float | None,
    volume: float | None,
    *,
    unit: str = "gallon",
    valid_range: tuple[float, float] = (10.0, 80.0),
) -> RecoveredPrice | None:
    """Reconstruye el precio unitario a partir del total y el volumen.

    Devuelve `None` si falta alguno de los dos, si el volumen es cero, o si el
    resultado cae fuera del rango plausible. Esa última comprobación no sobra:
    una lectura equivocada del total produce una división perfectamente válida
    con un precio absurdo, y sin la cota entraría en la serie como buena.
    """
    if total_paid_gtq is None or volume is None or volume <= 0 or total_paid_gtq <= 0:
        return None

    galones = volume if unit == "gallon" else volume / LITROS_POR_GALON
    if galones <= 0:
        return None

    precio = total_paid_gtq / galones
    lo, hi = valid_range
    if not (lo <= precio <= hi):
        logger.warning(
            "Precio reconstruido fuera de rango (%.2f); se descarta en vez de aceptarlo",
            precio,
        )
        return None

    return RecoveredPrice(
        price_gtq_per_gallon=round(precio, 2),
        method=METHOD_ARITHMETIC,
        note=f"{total_paid_gtq} GTQ / {round(galones, 3)} gal",
    )


def fill_missing(
    series: pd.DataFrame,
    *,
    strategy: str = "interpolate",
    value_column: str = "price_gtq_per_gallon",
    group_column: str = "fuel_type",
    date_column: str = "date",
    method_column: str = "method",
) -> pd.DataFrame:
    """Rellena los huecos de la serie y deja constancia de cuáles se rellenaron.

    Las estrategias no son intercambiables y la elección depende de cómo estén
    repartidos los huecos, cosa que solo se ve con datos reales:

    - `interpolate` estima entre dos observaciones y es lo natural en una serie
      de precios, que se mueve poco entre semanas. No puede rellenar los
      extremos, porque no hay nada al otro lado.
    - `median` resiste bien los valores extremos y sirve cuando los huecos son
      largos o caen en los bordes.
    - `mean` solo es razonable si la serie no tiene tendencia, cosa rara en
      precios de combustible.

    Se aplica por combustible: mezclar diésel con súper para rellenar un hueco
    daría un valor que no corresponde a ninguno de los dos.
    """
    if series.empty:
        return series

    estrategias = {
        "interpolate": METHOD_INTERPOLATED,
        "median": METHOD_MEDIAN,
        "mean": METHOD_MEAN,
    }
    if strategy not in estrategias:
        raise ValueError(
            f"Estrategia de relleno desconocida: {strategy!r}. "
            f"Disponibles: {', '.join(sorted(estrategias))}"
        )

    resultado = series.sort_values([group_column, date_column]).copy()
    if method_column not in resultado.columns:
        resultado[method_column] = METHOD_OCR

    faltaba = resultado[value_column].isna()
    if not faltaba.any():
        return resultado

    for grupo, indices in resultado.groupby(group_column).groups.items():
        bloque = resultado.loc[indices, value_column]
        if bloque.notna().sum() == 0:
            logger.warning(
                "El combustible %s no tiene ni un valor medido: no se rellena, "
                "porque no habría de dónde estimarlo",
                grupo,
            )
            continue

        if strategy == "interpolate":
            relleno = bloque.interpolate(method="linear", limit_direction="both")
        elif strategy == "median":
            relleno = bloque.fillna(bloque.median())
        else:
            relleno = bloque.fillna(bloque.mean())
        resultado.loc[indices, value_column] = relleno

    # Solo se marcan las filas que de verdad se rellenaron, no todas las del
    # grupo: perder de vista cuáles eran medidas haría inútil la distinción.
    ahora_tiene = resultado[value_column].notna()
    rellenadas = faltaba & ahora_tiene
    resultado.loc[rellenadas, method_column] = estrategias[strategy]

    logger.info(
        "Relleno por %s: %d de %d huecos cubiertos",
        strategy,
        int(rellenadas.sum()),
        int(faltaba.sum()),
    )
    return resultado


def recovery_summary(series: pd.DataFrame, method_column: str = "method") -> dict[str, int]:
    """Cuenta cuántos valores vienen de cada método.

    Es lo que hay que mirar antes de fiarse de un resultado: un conjunto donde
    la mayoría de las filas están estimadas no sostiene las mismas conclusiones
    que uno medido, aunque las métricas del modelo salgan igual de bien.
    """
    if series.empty or method_column not in series.columns:
        return {}
    return {str(k): int(v) for k, v in series[method_column].value_counts().items()}
