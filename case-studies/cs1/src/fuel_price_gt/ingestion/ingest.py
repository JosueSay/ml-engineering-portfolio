"""Trae las fotografías de la fuente configurada al disco local.

Dos cosas que solo importan cuando el conjunto es grande, y que por eso es fácil
dejarse:

**No volver a descargar lo ya traído.** Con miles de archivos, repetir la
descarga en cada corrida gasta tiempo y ancho de banda para acabar con lo mismo
que ya había. Se lleva un índice de lo descargado y se compara antes de pedir
nada.

**No cargar el catálogo entero en memoria.** La fuente se recorre en lotes, así
que el consumo no depende de cuántas fotografías haya. Con cinco daría igual;
con el histórico de varios años, no.

La elección de fuente cae siempre del lado seguro: si la remota no está
disponible —falta la credencial, no responde— se usa la carpeta local en vez de
fallar. Eso es lo que permite que la integración continua siga corriendo en
ramas sin acceso.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from ..config import env, load_config, resolve_path
from .source import ImageSource, LocalDirectorySource, RemoteImage

logger = logging.getLogger(__name__)

NOMBRE_INDICE = ".ingest-index.json"
TAMANO_LOTE = 50


@dataclass
class IngestReport:
    """Qué hizo una corrida de ingesta."""

    source: str
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Cuántas fotografías vio la corrida, se trajeran o no."""
        return self.downloaded + self.skipped + self.failed

    def as_dict(self) -> dict:
        """Resumen serializable, para el registro de la corrida."""
        return {
            "source": self.source,
            "available": self.total,
            "downloaded": self.downloaded,
            "skipped_cached": self.skipped,
            "failed": self.failed,
            "errors": self.errors[:10],
        }


def get_source(config: dict | None = None) -> ImageSource:
    """Devuelve la fuente configurada, o la local si aquella no está lista.

    La comprobación de disponibilidad se hace aquí y no en cada llamada: quien
    ingiere no debería tener que preguntarse si la credencial existe.
    """
    cfg = config or load_config()
    local = LocalDirectorySource(resolve_path(cfg["paths"]["raw"]))

    elegida = (env("IMAGE_SOURCE") or "local").strip().lower()
    if elegida in ("", "local"):
        return local

    if elegida == "manifest":
        # La via mas simple: una lista ya hecha de direcciones. No necesita
        # credencial porque no pregunta que hay en ninguna carpeta.
        from .manifest import ManifestSource

        remota: ImageSource = ManifestSource()
    elif elegida in ("gdrive-public", "gdrive_public"):
        # La via corta: carpeta compartida por enlace y clave de API. Menos
        # pasos de configuracion, a cambio de que la carpeta quede accesible a
        # quien tenga el enlace.
        from .gdrive_public import GoogleDrivePublicSource

        remota = GoogleDrivePublicSource()
    elif elegida == "gdrive":
        # Carpeta privada compartida con una cuenta de servicio. Mas pasos, y
        # deja constancia de quien tiene acceso.
        from .gdrive import GoogleDriveSource

        remota = GoogleDriveSource()
    else:
        logger.warning("Fuente desconocida %r; se usa la carpeta local", elegida)
        return local

    if remota.is_available():
        return remota

    logger.warning(
        "La fuente %r no esta disponible; se usa la carpeta local. "
        "Las etapas siguientes trabajaran con lo que ya haya en disco",
        elegida,
    )
    return local


def _leer_indice(directorio: Path) -> dict[str, str]:
    """Índice de lo ya descargado: clave de caché contra nombre de archivo."""
    ruta = directorio / NOMBRE_INDICE
    if not ruta.exists():
        return {}
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        # Un índice ilegible no debe impedir ingerir: en el peor caso se vuelve
        # a descargar todo, que es lento pero correcto.
        logger.warning("Indice de ingesta ilegible (%s); se reconstruye", exc)
        return {}


def _guardar_indice(directorio: Path, indice: dict[str, str]) -> None:
    """Escribe el índice, sin dejar que un fallo aquí tire la ingesta."""
    try:
        directorio.mkdir(parents=True, exist_ok=True)
        (directorio / NOMBRE_INDICE).write_text(
            json.dumps(indice, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("No se pudo guardar el indice de ingesta: %s", exc)


def _en_lotes(iterable: Iterator[RemoteImage], tamano: int) -> Iterator[list[RemoteImage]]:
    """Agrupa el catálogo en lotes para no tenerlo entero en memoria."""
    lote: list[RemoteImage] = []
    for elemento in iterable:
        lote.append(elemento)
        if len(lote) >= tamano:
            yield lote
            lote = []
    if lote:
        yield lote


def ingest_images(
    config: dict | None = None,
    *,
    source: ImageSource | None = None,
    limit: int | None = None,
    batch_size: int = TAMANO_LOTE,
) -> IngestReport:
    """Trae al disco lo que falte de la fuente configurada.

    `limit` sirve para probar contra una fuente grande sin descargarla entera.
    """
    cfg = config or load_config()
    destino = resolve_path(cfg["paths"]["raw"])
    destino.mkdir(parents=True, exist_ok=True)

    origen = source or get_source(cfg)
    reporte = IngestReport(source=origen.describe())
    logger.info("Ingiriendo desde %s", origen.describe())

    # Una fuente local ya tiene los archivos donde deben estar: recorrerla para
    # copiarlos sobre si mismos no aporta nada.
    if isinstance(origen, LocalDirectorySource):
        reporte.skipped = sum(1 for _ in origen.list_available())
        logger.info("Fuente local: %d fotografias ya en disco", reporte.skipped)
        return reporte

    indice = _leer_indice(destino)
    traidas = 0

    for lote in _en_lotes(origen.list_available(), batch_size):
        for imagen in lote:
            if limit is not None and traidas >= limit:
                logger.info("Alcanzado el limite de %d descargas", limit)
                _guardar_indice(destino, indice)
                return reporte

            clave = imagen.cache_key()
            destino_archivo = destino / imagen.name

            if indice.get(clave) and destino_archivo.exists():
                reporte.skipped += 1
                continue

            try:
                origen.fetch(imagen, destino_archivo)
            except Exception as exc:  # noqa: BLE001
                # Un archivo que falla no detiene el lote: con miles de
                # fotografias, uno corrupto no puede costar la corrida entera.
                reporte.failed += 1
                reporte.errors.append(f"{imagen.name}: {exc}")
                logger.warning("No se pudo traer %s: %s", imagen.name, exc)
                continue

            indice[clave] = imagen.name
            reporte.downloaded += 1
            traidas += 1

        _guardar_indice(destino, indice)

    _guardar_indice(destino, indice)
    logger.info(
        "Ingesta terminada: %d traidas, %d ya estaban, %d fallidas",
        reporte.downloaded,
        reporte.skipped,
        reporte.failed,
    )
    return reporte
