"""Fotografías listadas en un manifiesto de direcciones.

La vía más simple de las tres, y la que no necesita credencial de ningún tipo.

Descargar un archivo por su dirección nunca ha necesitado autenticación; lo que
sí la necesita es preguntarle a una carpeta qué contiene. Este módulo evita esa
pregunta: en vez de recorrer la carpeta, lee una lista ya hecha.

Esa lista puede vivir donde sea —un archivo del repositorio, una dirección
pública, un documento compartido exportado— y contener enlaces de cualquier
origen: almacenamiento de objetos, un servidor propio, o enlaces directos de
Drive. Es la misma idea por la que un conjunto de datos publicado se carga con
una sola línea: alguien dejó el archivo en una dirección estable.

**Su límite es también su virtud.** No descubre nada por su cuenta: si aparecen
fotografías nuevas y nadie actualiza el manifiesto, la ingesta no las verá.
Sirve cuando el conjunto está cerrado o cuando quien lo publica mantiene la
lista; para una carpeta que crece sola, conviene una fuente que la recorra.

Formatos aceptados, ambos porque cuestan lo mismo de leer:

    # texto plano: una direccion por linea, se ignoran los comentarios
    https://ejemplo.org/fotos/IMG_0001.HEIC
    https://ejemplo.org/fotos/IMG_0002.HEIC

    # o JSON, cuando se quiere declarar el nombre o la huella
    [
      {"url": "https://...", "name": "IMG_0001.HEIC", "checksum": "abc123"},
      {"url": "https://..."}
    ]
"""
from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

from ..config import env, resolve_path
from .source import ImageSource, RemoteImage

logger = logging.getLogger(__name__)

TIEMPO_ESPERA = 60
TROZO = 1024 * 256

# Un enlace de Drive apunta a una pagina, no al archivo. Para descargarlo hace
# falta la direccion de descarga directa, que se construye con su identificador.
_PATRONES_DRIVE = (
    re.compile(r"drive\.google\.com/file/d/([\w-]+)"),
    re.compile(r"drive\.google\.com/open\?id=([\w-]+)"),
    re.compile(r"drive\.google\.com/uc\?(?:export=download&)?id=([\w-]+)"),
)


def normalizar_enlace(url: str) -> str:
    """Convierte un enlace de Drive en su dirección de descarga directa.

    Pegar el enlace que ofrece Drive al compartir es lo natural, y ese enlace
    devuelve una página web en vez del archivo. Traducirlo aquí evita que cada
    quien tenga que saberlo.

    Cualquier otra dirección se deja intacta.
    """
    for patron in _PATRONES_DRIVE:
        encontrado = patron.search(url)
        if encontrado:
            return f"https://drive.google.com/uc?export=download&id={encontrado.group(1)}"
    return url


def _nombre_desde_url(url: str) -> str:
    """Deduce el nombre de archivo a partir de la dirección."""
    ruta = unquote(urlparse(url).path)
    nombre = Path(ruta).name
    return nombre or "descarga"


class ManifestSource(ImageSource):
    """Lee las fotografías listadas en un manifiesto."""

    name = "manifest"

    def __init__(self, location: str | Path | None = None):
        self.location = str(location or env("IMAGE_MANIFEST") or "")

    def is_available(self) -> bool:
        """Si hay manifiesto declarado y se puede leer."""
        if not self.location:
            logger.info("Manifiesto: falta declarar IMAGE_MANIFEST")
            return False
        if self.location.startswith(("http://", "https://")):
            return True
        if not resolve_path(self.location).is_file():
            logger.info("Manifiesto: no existe el archivo %s", self.location)
            return False
        return True

    def describe(self) -> str:
        """Una línea sobre el origen, para los registros."""
        return f"manifiesto {self.location}"

    def _contenido(self) -> str:
        """Trae el manifiesto, esté en disco o en una dirección."""
        if self.location.startswith(("http://", "https://")):
            respuesta = requests.get(self.location, timeout=TIEMPO_ESPERA)
            respuesta.raise_for_status()
            return respuesta.text
        return resolve_path(self.location).read_text(encoding="utf-8")

    def list_available(self) -> Iterator[RemoteImage]:
        """Enumera lo que declara el manifiesto, sin descargar nada."""
        texto = self._contenido().strip()
        if not texto:
            return

        entradas: list[dict]
        if texto.startswith(("[", "{")):
            datos = json.loads(texto)
            entradas = datos if isinstance(datos, list) else datos.get("images", [])
        else:
            entradas = [
                {"url": linea.strip()}
                for linea in texto.splitlines()
                if linea.strip() and not linea.lstrip().startswith("#")
            ]

        for indice, entrada in enumerate(entradas, start=1):
            crudo = str(entrada.get("url", "")).strip()
            if not crudo:
                continue
            url = normalizar_enlace(crudo)
            declarado = entrada.get("name")
            deducido = _nombre_desde_url(url)

            # Una direccion de descarga no lleva el nombre del archivo en la
            # ruta: el enlace de Drive normalizado acaba en "uc". Descartar esas
            # entradas por no reconocer la extension dejaria fuera justo los
            # enlaces que mas se pegan a mano, y sin decir por que.
            sin_nombre_util = Path(deducido).suffix == ""
            nombre = str(declarado or (f"imagen-{indice:04d}.jpg" if sin_nombre_util else deducido))

            if sin_nombre_util and not declarado:
                logger.warning(
                    "La direccion %d no permite deducir el nombre del archivo; se "
                    "usara %s. Declarar 'name' en el manifiesto lo evita",
                    indice,
                    nombre,
                )

            imagen = RemoteImage(
                identifier=url,
                name=nombre,
                size=entrada.get("size"),
                checksum=entrada.get("checksum"),
            )
            if imagen.is_image:
                yield imagen
            else:
                logger.info("Se omite, no parece una imagen: %s", imagen.name)

    def fetch(self, image: RemoteImage, destination: Path) -> Path:
        """Descarga una fotografía por trozos, con escritura atómica."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        parcial = destination.with_suffix(destination.suffix + ".partial")

        respuesta = requests.get(image.identifier, stream=True, timeout=TIEMPO_ESPERA)
        respuesta.raise_for_status()

        # Drive intercala una pagina de aviso cuando el archivo es grande. Se
        # detecta por el tipo de contenido: si llega HTML donde deberia llegar
        # una imagen, la descarga no sirve y decirlo es mejor que guardar la
        # pagina como si fuera la fotografia.
        tipo = respuesta.headers.get("Content-Type", "")
        if tipo.startswith("text/html"):
            raise OSError(
                "La respuesta es una pagina web, no una imagen. Suele pasar con "
                "enlaces de Drive a archivos grandes, que piden confirmacion"
            )

        with open(parcial, "wb") as fh:
            for trozo in respuesta.iter_content(chunk_size=TROZO):
                if trozo:
                    fh.write(trozo)

        parcial.replace(destination)
        return destination
