"""De dónde vienen las fotografías.

El almacenamiento es infraestructura, no lógica del caso: el pipeline habla con
un contrato y cada proveedor es una implementación intercambiable. Cambiar de
Drive a un depósito de objetos, o a una carpeta, no toca nada más que el módulo
del proveedor.
"""
from .ingest import IngestReport, get_source, ingest_images
from .manifest import ManifestSource, normalizar_enlace
from .source import ImageSource, LocalDirectorySource, RemoteImage

__all__ = [
    "ImageSource",
    "IngestReport",
    "LocalDirectorySource",
    "ManifestSource",
    "RemoteImage",
    "get_source",
    "ingest_images",
    "normalizar_enlace",
]
