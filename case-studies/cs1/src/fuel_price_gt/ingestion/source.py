"""De dónde salen las fotografías: el contrato y lo que comparten sus variantes.

El almacenamiento es un detalle de infraestructura, no parte de la lógica del
caso. Por eso el pipeline habla con este contrato y no con Drive, ni con un
depósito de objetos, ni con una carpeta: el día que cambie el proveedor se
escribe otra implementación y nada más se entera.

Las tres operaciones que el pipeline necesita son pocas a propósito. Cuantas
menos exija el contrato, más fácil es que un proveedor nuevo lo cumpla.

Hay una decisión que atraviesa todo el módulo: **descargar es caro y leer dos
veces la misma fotografía no aporta nada**. Con un histórico de varios años son
miles de archivos, así que cada implementación declara lo que sabe de un archivo
antes de traerlo, y el ingestor decide con eso si vale la pena.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

EXTENSIONES = {".heic", ".heif", ".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class RemoteImage:
    """Una fotografía disponible en la fuente, todavía sin traer.

    Lo que se sabe de ella sin descargarla. `checksum` es lo más valioso cuando
    el proveedor lo da, porque permite saber si el archivo cambió sin gastar
    ancho de banda; cuando no lo da, hay que conformarse con el tamaño y la
    fecha, que son señales más débiles pero suficientes para descartar lo que
    con seguridad no ha cambiado.
    """

    identifier: str
    name: str
    size: int | None = None
    modified_at: datetime | None = None
    checksum: str | None = None

    @property
    def is_image(self) -> bool:
        """Si el nombre corresponde a un formato que el pipeline sabe leer."""
        return Path(self.name).suffix.lower() in EXTENSIONES

    def cache_key(self) -> str:
        """Clave con la que decidir si este archivo ya se trajo.

        Se prefiere la huella del proveedor. Sin ella, la combinación de
        identificador, tamaño y fecha de modificación: no es infalible, pero un
        archivo que coincide en las tres casi nunca es otro.
        """
        if self.checksum:
            return f"sum:{self.checksum}"
        marca = self.modified_at.isoformat() if self.modified_at else "-"
        return f"id:{self.identifier}|{self.size or '-'}|{marca}"


class ImageSource(ABC):
    """Contrato que cumple cualquier origen de fotografías."""

    name: str = "abstract"

    @abstractmethod
    def list_available(self) -> Iterator[RemoteImage]:
        """Enumera lo que hay en la fuente, sin descargar nada."""

    @abstractmethod
    def fetch(self, image: RemoteImage, destination: Path) -> Path:
        """Trae una fotografía y devuelve dónde quedó."""

    def is_available(self) -> bool:
        """Si la fuente se puede usar ahora mismo.

        Falso cuando falta la credencial o el servicio no responde. El pipeline
        lo consulta para caer a la alternativa local en vez de fallar, que es lo
        que mantiene la integración continua funcionando en ramas sin acceso.
        """
        return True

    def describe(self) -> str:
        """Una línea sobre el origen, para los registros de ejecución."""
        return self.name


class LocalDirectorySource(ImageSource):
    """Fotografías que ya están en el disco.

    Es la fuente por defecto y la que usa la integración continua cuando no hay
    credenciales. Traer un archivo aquí no es descargar sino comprobar que
    sigue donde decía, así que el coste es despreciable.
    """

    name = "local"

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def list_available(self) -> Iterator[RemoteImage]:
        """Recorre el directorio en orden estable."""
        if not self.directory.exists():
            logger.warning("El directorio de origen no existe: %s", self.directory)
            return
        for ruta in sorted(self.directory.rglob("*")):
            if not ruta.is_file() or ruta.suffix.lower() not in EXTENSIONES:
                continue
            info = ruta.stat()
            yield RemoteImage(
                identifier=str(ruta),
                name=ruta.name,
                size=info.st_size,
                modified_at=datetime.fromtimestamp(info.st_mtime),
            )

    def fetch(self, image: RemoteImage, destination: Path) -> Path:
        """Devuelve la ruta del archivo, que ya está donde tiene que estar."""
        origen = Path(image.identifier)
        if not origen.exists():
            raise FileNotFoundError(f"Ya no esta donde decia: {origen}")
        return origen

    def is_available(self) -> bool:
        """Si el directorio de origen existe."""
        return self.directory.exists()

    def describe(self) -> str:
        """Una línea sobre el origen, para los registros."""
        return f"carpeta local {self.directory}"
