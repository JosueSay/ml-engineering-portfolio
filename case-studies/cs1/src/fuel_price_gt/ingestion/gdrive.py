"""Fotografías guardadas en una carpeta compartida de Google Drive.

Es el destino previsto: el instructor comparte el histórico por ahí. Mientras
llega, se trabaja contra una carpeta propia con las mismas credenciales y el
mismo código, de modo que el día que cambie el enlace solo cambie el
identificador de carpeta.

Dos decisiones sobre credenciales, ambas por el mismo motivo:

- Se usa una cuenta de servicio y no un usuario. Un pipeline que necesita que
  alguien inicie sesión no se puede automatizar.
- Se pide solo lectura. El pipeline nunca escribe en la carpeta de origen, así
  que pedir más permiso del necesario solo amplía el daño si la credencial se
  filtra.

La biblioteca de Google es una dependencia opcional a propósito: quien instale
el paquete para leer una fotografía suya no tiene por qué arrastrarla.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from ..config import env, secret_path
from .source import ImageSource, RemoteImage

logger = logging.getLogger(__name__)

# Solo lectura: es el permiso mínimo para lo que el pipeline hace.
ALCANCE = ["https://www.googleapis.com/auth/drive.readonly"]

# Lo que se pide de cada archivo. Pedir campos concretos y no todos reduce el
# tamaño de la respuesta, que con miles de archivos se nota.
CAMPOS = "nextPageToken, files(id, name, size, modifiedTime, md5Checksum, mimeType)"

TAMANO_PAGINA = 200

# Como identifica Drive a una carpeta.
MIME_CARPETA = "application/vnd.google-apps.folder"


class GoogleDriveSource(ImageSource):
    """Lee una carpeta compartida de Drive con una cuenta de servicio."""

    name = "gdrive"

    def __init__(
        self,
        folder_id: str | None = None,
        credentials_file: Path | None = None,
        *,
        recursive: bool = True,
    ):
        self.folder_id = folder_id or env("GDRIVE_FOLDER_ID") or ""
        self.credentials_file = credentials_file or secret_path("GDRIVE_CREDENTIALS_FILE")
        # Se recorre en profundidad por defecto: organizar un historico de
        # varios anios en subcarpetas por anio o por mes es lo natural, y una
        # ingesta que solo mirase el primer nivel se dejaria casi todo sin
        # avisar de nada.
        self.recursive = recursive
        self._service = None

    # --- Disponibilidad ---------------------------------------------------------

    def is_available(self) -> bool:
        """Si hay credencial, carpeta y biblioteca para poder trabajar.

        Se comprueban las tres cosas por separado y se dice cuál falta: "no
        disponible" a secas obliga a adivinar, y las tres se arreglan distinto.
        """
        if not self.folder_id:
            logger.info("Drive: falta declarar GDRIVE_FOLDER_ID")
            return False
        if self.credentials_file is None:
            logger.info("Drive: no hay credencial en la ruta de GDRIVE_CREDENTIALS_FILE")
            return False
        try:
            import googleapiclient  # noqa: F401
        except ImportError:
            logger.info(
                "Drive: falta la dependencia opcional. Instalar con: "
                "pip install -e '.[gdrive]'"
            )
            return False
        return True

    def describe(self) -> str:
        """Una línea sobre el origen, para los registros."""
        return f"Google Drive, carpeta {self.folder_id}"

    # --- Conexión ---------------------------------------------------------------

    def _connect(self):
        """Abre la conexión una sola vez y la reutiliza."""
        if self._service is not None:
            return self._service

        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credenciales = service_account.Credentials.from_service_account_file(
            str(self.credentials_file), scopes=ALCANCE
        )
        # cache_discovery en falso evita un aviso ruidoso y un archivo de caché
        # que no aporta nada en un proceso de vida corta.
        self._service = build("drive", "v3", credentials=credenciales, cache_discovery=False)
        return self._service

    # --- Operaciones del contrato -------------------------------------------------

    def _listar_carpeta(self, folder_id: str) -> Iterator[dict]:
        """Recorre una carpeta página a página y entrega cada entrada.

        Se pagina porque una carpeta con el histórico de varios años no cabe en
        una sola respuesta, y pedirla entera fallaría justo cuando el conjunto
        empieza a ser interesante.
        """
        servicio = self._connect()
        consulta = f"'{folder_id}' in parents and trashed = false"
        token = None
        while True:
            respuesta = (
                servicio.files()
                .list(
                    q=consulta,
                    fields=CAMPOS,
                    pageSize=TAMANO_PAGINA,
                    pageToken=token,
                    orderBy="name",
                )
                .execute()
            )
            yield from respuesta.get("files", [])
            token = respuesta.get("nextPageToken")
            if not token:
                break

    def list_available(self) -> Iterator[RemoteImage]:
        """Enumera las fotografías, entrando en las subcarpetas que haya.

        El recorrido lleva un registro de las carpetas visitadas: en Drive un
        mismo elemento puede estar en varios sitios a la vez, y sin ese control
        una carpeta enlazada dentro de sí misma dejaría la ingesta dando vueltas.
        """
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
        """Descarga una fotografía al destino indicado.

        Se escribe primero en un archivo temporal y se renombra al terminar: si
        la descarga se corta a medias, no queda un archivo incompleto con
        aspecto de bueno, que el resto del pipeline daría por válido.
        """
        from googleapiclient.http import MediaIoBaseDownload

        servicio = self._connect()
        destination.parent.mkdir(parents=True, exist_ok=True)
        parcial = destination.with_suffix(destination.suffix + ".partial")

        peticion = servicio.files().get_media(fileId=image.identifier)
        with open(parcial, "wb") as fh:
            descarga = MediaIoBaseDownload(fh, peticion)
            terminado = False
            while not terminado:
                _, terminado = descarga.next_chunk()

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
