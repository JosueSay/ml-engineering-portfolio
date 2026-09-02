"""Fotografías de una carpeta de Drive compartida por enlace.

La vía corta. Cuando la carpeta ya está accesible por enlace —porque quien la
comparte lo hizo así— pedir una cuenta de servicio para leer algo que de todos
modos es público es ceremonia sin beneficio.

Necesita solo una clave de API, que se crea en un paso, y habla con la misma
interfaz oficial que la variante con cuenta de servicio. No arrastra el cliente
de Google: basta el cliente HTTP que el proyecto ya usa para consultar el precio
de referencia.

**Cuándo NO usar esto.** Si la carpeta contiene material que no debería ser
público, esta vía obliga a dejarla accesible por enlace, y un enlace se propaga
sin que se sepa quién lo tiene. Para ese caso está `gdrive.py`, que mantiene la
carpeta privada a cambio de unos pasos más de configuración.

La decisión no es técnica sino sobre el material: quién puede ver esas
fotografías.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import requests

from ..config import env, read_secret
from .source import ImageSource, RemoteImage

logger = logging.getLogger(__name__)

BASE = "https://www.googleapis.com/drive/v3/files"
MIME_CARPETA = "application/vnd.google-apps.folder"
CAMPOS = "nextPageToken, files(id, name, size, modifiedTime, md5Checksum, mimeType)"
TAMANO_PAGINA = 200
TIEMPO_ESPERA = 60
TROZO = 1024 * 256


class GoogleDrivePublicSource(ImageSource):
    """Lee una carpeta compartida por enlace usando una clave de API."""

    name = "gdrive-public"

    def __init__(
        self,
        folder_id: str | None = None,
        api_key: str | None = None,
        *,
        recursive: bool = True,
    ):
        self.folder_id = folder_id or env("GDRIVE_FOLDER_ID") or ""
        # La clave puede venir de un archivo en keys/ o directamente del
        # entorno. Lo primero es lo que sigue la convencion del proyecto; lo
        # segundo existe porque en integracion continua es mas comodo y una
        # clave de API restringida a una sola interfaz es de bajo riesgo.
        self.api_key = api_key or read_secret("GDRIVE_API_KEY_FILE") or env("GDRIVE_API_KEY") or ""
        self.recursive = recursive

    # --- Disponibilidad ---------------------------------------------------------

    def is_available(self) -> bool:
        """Si hay carpeta y clave. Se dice cuál falta, no solo que no se puede."""
        if not self.folder_id:
            logger.info("Drive publico: falta declarar GDRIVE_FOLDER_ID")
            return False
        if not self.api_key:
            logger.info(
                "Drive publico: falta la clave de API. Puede ir en "
                "keys/gdrive-api.key o en la variable GDRIVE_API_KEY"
            )
            return False
        return True

    def describe(self) -> str:
        """Una línea sobre el origen, para los registros."""
        return f"Google Drive por enlace, carpeta {self.folder_id}"

    # --- Operaciones del contrato -------------------------------------------------

    def _listar_carpeta(self, folder_id: str) -> Iterator[dict]:
        """Recorre una carpeta página a página."""
        token = None
        while True:
            parametros = {
                "q": f"'{folder_id}' in parents and trashed = false",
                "fields": CAMPOS,
                "pageSize": TAMANO_PAGINA,
                "orderBy": "name",
                "key": self.api_key,
            }
            if token:
                parametros["pageToken"] = token

            respuesta = requests.get(BASE, params=parametros, timeout=TIEMPO_ESPERA)
            if respuesta.status_code == 403:
                raise PermissionError(
                    "Drive rechazo la peticion. Suele ser que la clave de API no "
                    "tiene habilitada la Drive API, o que la carpeta no esta "
                    "compartida por enlace"
                )
            if respuesta.status_code == 404:
                raise FileNotFoundError(
                    f"No existe la carpeta {folder_id}, o no es accesible por enlace"
                )
            respuesta.raise_for_status()

            datos = respuesta.json()
            yield from datos.get("files", [])
            token = datos.get("nextPageToken")
            if not token:
                break

    def list_available(self) -> Iterator[RemoteImage]:
        """Enumera las fotografías, entrando en las subcarpetas que haya."""
        pendientes = [self.folder_id]
        visitadas: set[str] = set()

        while pendientes:
            actual = pendientes.pop(0)
            if actual in visitadas:
                continue
            visitadas.add(actual)

            for archivo in self._listar_carpeta(actual):
                if archivo.get("mimeType") == MIME_CARPETA:
                    if self.recursive:
                        pendientes.append(archivo["id"])
                    continue

                imagen = RemoteImage(
                    identifier=archivo["id"],
                    name=archivo["name"],
                    size=int(archivo["size"]) if archivo.get("size") else None,
                    modified_at=_a_fecha(archivo.get("modifiedTime")),
                    checksum=archivo.get("md5Checksum"),
                )
                if imagen.is_image:
                    yield imagen

        if len(visitadas) > 1:
            logger.info("Recorridas %d carpetas en Drive", len(visitadas))

    def fetch(self, image: RemoteImage, destination: Path) -> Path:
        """Descarga una fotografía por trozos.

        Se escribe en un archivo temporal y se renombra al terminar: si la
        descarga se corta, no queda un archivo incompleto con aspecto de bueno
        que el resto del pipeline daria por valido.

        Por trozos porque una fotografía de móvil ronda los dos megabytes y el
        histórico son miles: cargarlas enteras en memoria no escala.
        """
        destination.parent.mkdir(parents=True, exist_ok=True)
        parcial = destination.with_suffix(destination.suffix + ".partial")

        respuesta = requests.get(
            f"{BASE}/{image.identifier}",
            params={"alt": "media", "key": self.api_key},
            stream=True,
            timeout=TIEMPO_ESPERA,
        )
        respuesta.raise_for_status()

        with open(parcial, "wb") as fh:
            for trozo in respuesta.iter_content(chunk_size=TROZO):
                if trozo:
                    fh.write(trozo)

        parcial.replace(destination)
        return destination


def _a_fecha(valor: str | None) -> datetime | None:
    """Convierte la marca de tiempo de Drive, que llega en formato ISO."""
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return None
