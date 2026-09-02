"""Construcción de las capas de datos, de la extracción al conjunto final.

Bronze guarda lo que dio la imagen, con sus fallos y sus motivos. Silver deja
solo lo aprovechable, ya fechado, e incorpora los precios recuperados por
aritmética. Gold añade las variables de modelado y, cuando falta historia,
la completa declarando siempre qué parte es medida y qué parte no.

La base de datos es la fuente de verdad de las tres capas. Los archivos
tabulares que se escriben al lado son exportaciones: cómodas para abrir en una
hoja de cálculo o publicar como artefacto, pero incapaces de responder de qué
fotografía salió un precio, que es la pregunta que sostiene el caso.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from ..augmentation.series_augment import generate_synthetic_series
from ..config import load_config, resolve_path
from ..db import replace_gold, session_scope, upsert_silver_price
from ..db.models import (
    METHOD_OCR,
    METHOD_SYNTHETIC,
    GoldRow,
    PriceReading,
    SilverPrice,
)
from .features import build_features
from .recovery import fill_missing, recovery_summary

logger = logging.getLogger(__name__)


def build_silver(config: dict | None = None) -> pd.DataFrame:
    """Construye la capa Silver a partir de lo ya extraído.

    Lee de la base en vez de volver a procesar las fotografías: la extracción
    es la etapa cara y repetirla para reconstruir una tabla derivada no aporta
    nada. Si hace falta releer las imágenes, se ejecuta antes la etapa de
    extracción.

    Cada precio conserva el enlace a la lectura que lo produjo. Ese enlace es
    lo que permite, más adelante, volver de un valor del conjunto de modelado
    hasta el recorte de píxeles del que salió.
    """
    cfg = config or load_config()

    rows: list[dict] = []
    with session_scope() as session:
        lecturas = session.scalars(
            select(PriceReading).where(PriceReading.is_valid).order_by(PriceReading.id)
        )
        for lectura in lecturas:
            imagen = lectura.extraction_run.image
            if imagen.captured_at is None:
                # Sin fecha de captura el precio no se puede situar en la serie.
                # No se descarta en Bronze, pero aquí no hay dónde ponerlo.
                logger.warning(
                    "Lectura %s sin fecha de captura: no entra en la serie", lectura.id
                )
                continue
            rows.append(
                {
                    "date": imagen.captured_at.date(),
                    "fuel_type": lectura.fuel_type,
                    "price_gtq_per_gallon": lectura.price_gtq_per_gallon,
                    "confidence": lectura.confidence,
                    "method": lectura.method,
                    "brand": imagen.brand,
                    "reading_id": lectura.id,
                    "source_file": imagen.original_name,
                }
            )

        for fila in rows:
            upsert_silver_price(
                session,
                observed_on=fila["date"],
                fuel_type=fila["fuel_type"],
                price_gtq_per_gallon=fila["price_gtq_per_gallon"],
                method=fila["method"],
                price_reading_id=fila["reading_id"],
                brand=fila["brand"],
            )

    df = pd.DataFrame(
        rows,
        columns=[
            "date", "fuel_type", "price_gtq_per_gallon", "confidence",
            "method", "brand", "reading_id", "source_file",
        ],
    )

    silver_dir = resolve_path(cfg["paths"]["silver"])
    silver_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(silver_dir / cfg["files"]["silver"], index=False)
    logger.info("Silver: %d precios aprovechables", len(df))
    return df


def _silver_desde_base() -> pd.DataFrame:
    """Lee la capa Silver ya persistida, para no reconstruirla dos veces."""
    with session_scope() as session:
        filas = [
            {
                "date": p.observed_on,
                "fuel_type": p.fuel_type,
                "price_gtq_per_gallon": p.price_gtq_per_gallon,
                "method": p.method,
                "brand": p.brand,
                "silver_id": p.id,
            }
            for p in session.scalars(select(SilverPrice).order_by(SilverPrice.observed_on))
        ]
    return pd.DataFrame(
        filas,
        columns=["date", "fuel_type", "price_gtq_per_gallon", "method", "brand", "silver_id"],
    )


def resolve_cutoff(
    df_silver: pd.DataFrame, config: dict, end_date: date | None = None
) -> date:
    """Decide hasta qué fecha llega la serie, en orden de preferencia.

    1. Lo que pida quien llama, si lo pide.
    2. La fecha declarada en la configuración.
    3. La última observación real, cuando hay datos.
    4. El día de hoy, avisando.

    El último caso es el único que rompe la reproducibilidad: dos corridas en
    días distintos generarían conjuntos distintos sin que nada haya cambiado.
    Por eso avisa en vez de hacerlo en silencio.
    """
    if end_date is not None:
        return end_date

    declarada = config.get("modeling", {}).get("data_cutoff")
    if declarada:
        return declarada if isinstance(declarada, date) else date.fromisoformat(str(declarada))

    if not df_silver.empty:
        return max(df_silver["date"])

    hoy = date.today()
    logger.warning(
        "Sin datos ni fecha de corte declarada: la serie llega hasta hoy (%s). "
        "El conjunto no sera reproducible; declarar modeling.data_cutoff para fijarlo",
        hoy,
    )
    return hoy


def build_gold(
    df_silver: pd.DataFrame | None = None,
    config: dict | None = None,
    end_date: date | None = None,
    fill_strategy: str = "interpolate",
) -> pd.DataFrame:
    """Construye la capa Gold, lista para modelar.

    Tres cosas ocurren aquí y conviene no confundirlas:

    1. Si no hay historia suficiente, se completa con una serie generada. Esas
       filas quedan marcadas como tales y sin enlace a ningún precio medido.
    2. Los huecos que queden se rellenan con la estrategia indicada, y cada
       fila rellenada guarda con qué método.
    3. Se añaden las variables de modelado, todas mirando hacia atrás.

    Al terminar se informa de cuántas filas vienen de cada procedencia. Es el
    número que hay que mirar antes de creerse una métrica.
    """
    cfg = config or load_config()
    df_silver = df_silver if df_silver is not None else _silver_desde_base()

    end_date = resolve_cutoff(df_silver, cfg, end_date)
    if not df_silver.empty:
        start_date = min(df_silver["date"]) - timedelta(weeks=8)
    else:
        start_date = end_date - timedelta(weeks=cfg["modeling"]["synthetic_history_weeks"])

    series = generate_synthetic_series(df_silver, start_date, end_date, cfg)
    if "method" not in series.columns:
        series["method"] = METHOD_OCR
    # Lo generado se marca como tal. Heredar el metodo de una lectura para una
    # fila que nadie leyo haria inutil el resto del registro de procedencia.
    if "source" in series.columns:
        series.loc[series["source"] == "synthetic", "method"] = METHOD_SYNTHETIC
    series = fill_missing(series, strategy=fill_strategy)

    gold = build_features(series, cfg)

    # El enlace al precio medido solo existe para las filas que vienen de uno.
    enlaces: dict[tuple, int] = {}
    if "silver_id" in df_silver.columns:
        enlaces = {
            (fila["date"], fila["fuel_type"]): fila["silver_id"]
            for _, fila in df_silver.iterrows()
            if pd.notna(fila.get("silver_id"))
        }

    columnas_variables = [
        c for c in gold.columns
        if c not in {"date", "fuel_type", "price_gtq_per_gallon", "source", "method", "brand", "silver_id"}
    ]
    filas_db = []
    for _, fila in gold.iterrows():
        observado = fila["date"]
        observado = observado.date() if hasattr(observado, "date") else observado
        variables = {
            c: (None if pd.isna(fila[c]) else float(fila[c]))
            for c in columnas_variables
            if pd.api.types.is_number(fila[c]) or pd.isna(fila[c])
        }
        filas_db.append(
            {
                "observed_on": observado,
                "fuel_type": fila["fuel_type"],
                "price_gtq_per_gallon": float(fila["price_gtq_per_gallon"]),
                "features": variables,
                "source": fila.get("source", "synthetic"),
                "method": fila.get("method", METHOD_OCR),
                "silver_price_id": enlaces.get((observado, fila["fuel_type"])),
            }
        )

    with session_scope() as session:
        replace_gold(session, filas_db)

    gold_dir = resolve_path(cfg["paths"]["gold"])
    gold_dir.mkdir(parents=True, exist_ok=True)
    gold.to_csv(gold_dir / cfg["files"]["gold"], index=False)

    logger.info(
        "Gold: %d filas | procedencia %s | metodos %s",
        len(gold),
        dict(gold["source"].value_counts()) if "source" in gold else {},
        recovery_summary(gold),
    )
    return gold


def load_gold_if_exists(config: dict | None = None) -> pd.DataFrame | None:
    """Lee el conjunto de modelado ya construido, o `None` si no está.

    Se prefiere la base al archivo exportado: es la fuente de verdad y trae la
    procedencia de cada fila. El archivo queda como respaldo para cuando el
    conjunto se recibe suelto, por ejemplo descargado como artefacto de una
    corrida anterior.
    """
    cfg = config or load_config()

    try:
        with session_scope() as session:
            filas = list(session.scalars(select(GoldRow).order_by(GoldRow.observed_on)))
    except OperationalError:
        # En una instalacion recien hecha la base todavia no existe. Es un
        # estado normal, no un fallo: quien lea esto acaba de instalar el
        # paquete y aun no ha construido nada. Consultar no debe crear el
        # esquema por su cuenta, que seria un efecto sorprendente para una
        # funcion de lectura.
        logger.info("La base no tiene esquema todavia; se busca el archivo exportado")
        filas = []

    if filas:
        # Las filas se leyeron dentro de la sesion y siguen accesibles fuera
        # porque no se invalidan al confirmar, asi que no hace falta abrir otra.
        registros = []
        for fila in filas:
            registro = {
                "date": pd.Timestamp(fila.observed_on),
                "fuel_type": fila.fuel_type,
                "price_gtq_per_gallon": fila.price_gtq_per_gallon,
                "source": fila.source,
                "method": fila.method,
            }
            registro.update(fila.features or {})
            registros.append(registro)
        return pd.DataFrame(registros)

    path = resolve_path(cfg["paths"]["gold"]) / cfg["files"]["gold"]
    if not path.exists():
        return None
    logger.info("Conjunto leido del archivo exportado; la base esta vacia")
    return pd.read_csv(path, parse_dates=["date"])


def build_silver_and_gold(config: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Encadena las dos capas derivadas y devuelve ambas."""
    cfg = config or load_config()
    silver = build_silver(cfg)
    gold = build_gold(config=cfg)
    return silver, gold


__all__ = [
    "build_gold",
    "build_silver",
    "build_silver_and_gold",
    "load_gold_if_exists",
]
