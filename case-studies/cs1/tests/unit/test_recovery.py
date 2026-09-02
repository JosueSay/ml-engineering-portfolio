from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fuel_price_gt.data.recovery import (
    fill_missing,
    recover_from_total,
    recovery_summary,
)
from fuel_price_gt.db.models import (
    METHOD_ARITHMETIC,
    METHOD_INTERPOLATED,
    METHOD_MEDIAN,
    METHOD_OCR,
)

# --- Reconstruccion aritmetica ------------------------------------------------

def test_recovers_price_from_total_and_volume() -> None:
    """El caso que describe el enunciado: cinco galones por Q197.50."""
    recuperado = recover_from_total(197.50, 5.0)

    assert recuperado is not None
    assert recuperado.price_gtq_per_gallon == 39.50
    assert recuperado.method == METHOD_ARITHMETIC


def test_converts_litres_before_dividing() -> None:
    """Un volumen en litros no se puede dividir como si fueran galones.

    Sin la conversión el precio saldría casi cuatro veces menor, y dentro de un
    rango que parece plausible.
    """
    recuperado = recover_from_total(197.50, 18.927, unit="litre")

    assert recuperado is not None
    assert recuperado.price_gtq_per_gallon == pytest.approx(39.50, abs=0.02)


def test_rejects_reconstruction_outside_plausible_range() -> None:
    """Una división válida puede dar un precio absurdo, y hay que descartarlo."""
    assert recover_from_total(1975.0, 5.0) is None  # 395 GTQ por galon
    assert recover_from_total(5.0, 5.0) is None     # 1 GTQ por galon


@pytest.mark.parametrize(
    "total,volumen",
    [(None, 5.0), (197.5, None), (197.5, 0.0), (0.0, 5.0), (-10.0, 5.0)],
)
def test_returns_nothing_without_usable_inputs(total, volumen) -> None:
    assert recover_from_total(total, volumen) is None


# --- Relleno de faltantes ------------------------------------------------------

def _serie_con_hueco() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2026-08-01", "2026-08-08", "2026-08-15", "2026-08-22"]
            ),
            "fuel_type": ["regular"] * 4,
            "price_gtq_per_gallon": [40.0, np.nan, 42.0, 43.0],
            "method": [METHOD_OCR, None, METHOD_OCR, METHOD_OCR],
        }
    )


def test_interpolation_fills_the_gap_between_observations() -> None:
    resultado = fill_missing(_serie_con_hueco(), strategy="interpolate")

    assert resultado["price_gtq_per_gallon"].isna().sum() == 0
    assert resultado.iloc[1]["price_gtq_per_gallon"] == pytest.approx(41.0)


def test_filled_rows_are_marked_and_measured_ones_are_not() -> None:
    """La distincion entre medido y estimado es el punto de todo el modulo."""
    resultado = fill_missing(_serie_con_hueco(), strategy="interpolate")

    metodos = list(resultado["method"])
    assert metodos[1] == METHOD_INTERPOLATED, "la fila rellenada debe quedar marcada"
    assert metodos[0] == METHOD_OCR, "una fila medida no puede quedar marcada como estimada"
    assert metodos[2] == METHOD_OCR
    assert metodos[3] == METHOD_OCR


def test_median_strategy_marks_with_its_own_method() -> None:
    resultado = fill_missing(_serie_con_hueco(), strategy="median")

    assert resultado.iloc[1]["method"] == METHOD_MEDIAN


def test_does_not_invent_when_a_fuel_has_no_measurement() -> None:
    """Sin ni un valor medido no hay de dónde estimar, y no se estima."""
    serie = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-08-01", "2026-08-08"]),
            "fuel_type": ["diesel"] * 2,
            "price_gtq_per_gallon": [np.nan, np.nan],
            "method": [None, None],
        }
    )

    resultado = fill_missing(serie, strategy="interpolate")

    assert resultado["price_gtq_per_gallon"].isna().all()


def test_does_not_mix_fuels_when_filling() -> None:
    """Rellenar un hueco de súper con precios de diésel daría un valor ajeno."""
    serie = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-08-01", "2026-08-08"] * 2),
            "fuel_type": ["regular", "regular", "diesel", "diesel"],
            "price_gtq_per_gallon": [40.0, np.nan, 60.0, 62.0],
            "method": [METHOD_OCR, None, METHOD_OCR, METHOD_OCR],
        }
    )

    resultado = fill_missing(serie, strategy="median")
    regular = resultado[resultado["fuel_type"] == "regular"]

    # La mediana de regular es 40, no algo arrastrado desde diesel.
    assert regular["price_gtq_per_gallon"].iloc[1] == pytest.approx(40.0)


def test_unknown_strategy_fails_loudly() -> None:
    with pytest.raises(ValueError, match="desconocida"):
        fill_missing(_serie_con_hueco(), strategy="magia")


def test_summary_counts_each_method() -> None:
    resultado = fill_missing(_serie_con_hueco(), strategy="interpolate")

    resumen = recovery_summary(resultado)

    assert resumen[METHOD_OCR] == 3
    assert resumen[METHOD_INTERPOLATED] == 1
