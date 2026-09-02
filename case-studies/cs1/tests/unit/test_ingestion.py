from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pytest

from fuel_price_gt.ingestion.ingest import ingest_images
from fuel_price_gt.ingestion.source import (
    ImageSource,
    LocalDirectorySource,
    RemoteImage,
)


class FuenteFalsa(ImageSource):
    """Fuente remota simulada, para probar sin red ni credenciales.

    Cuenta las descargas: es lo que permite comprobar que el caché de verdad
    evita trabajo, y no solo que el resultado final coincide.
    """

    name = "falsa"

    def __init__(self, imagenes: list[RemoteImage], fallar: set[str] | None = None):
        self.imagenes = imagenes
        self.fallar = fallar or set()
        self.descargas: list[str] = []

    def list_available(self) -> Iterator[RemoteImage]:
        yield from self.imagenes

    def fetch(self, image: RemoteImage, destination: Path) -> Path:
        if image.name in self.fallar:
            raise OSError("descarga interrumpida")
        self.descargas.append(image.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"contenido")
        return destination

    def describe(self) -> str:
        return "fuente falsa"


@pytest.fixture
def config(tmp_path: Path) -> dict:
    return {"paths": {"raw": str(tmp_path / "raw")}}


def _remota(nombre: str, checksum: str | None = "abc") -> RemoteImage:
    return RemoteImage(
        identifier=f"id-{nombre}",
        name=nombre,
        size=1234,
        modified_at=datetime(2026, 8, 1, 12, 0),
        checksum=checksum,
    )


# --- Cache de descarga ----------------------------------------------------------

def test_downloads_what_is_missing(config: dict) -> None:
    fuente = FuenteFalsa([_remota("a.heic"), _remota("b.heic", "def")])

    reporte = ingest_images(config, source=fuente)

    assert reporte.downloaded == 2
    assert len(fuente.descargas) == 2


def test_does_not_download_twice(config: dict) -> None:
    """El caché tiene que evitar el trabajo, no solo dar el mismo resultado."""
    fuente = FuenteFalsa([_remota("a.heic"), _remota("b.heic", "def")])
    ingest_images(config, source=fuente)

    segunda = ingest_images(config, source=fuente)

    assert segunda.downloaded == 0
    assert segunda.skipped == 2
    assert len(fuente.descargas) == 2, "no debio pedir ninguna descarga mas"


def test_downloads_again_when_the_checksum_changes(config: dict) -> None:
    """Un archivo distinto con el mismo nombre sí hay que volver a traerlo."""
    ingest_images(config, source=FuenteFalsa([_remota("a.heic", "suma-vieja")]))

    fuente = FuenteFalsa([_remota("a.heic", "suma-nueva")])
    reporte = ingest_images(config, source=fuente)

    assert reporte.downloaded == 1


# --- Robustez -------------------------------------------------------------------

def test_one_failure_does_not_stop_the_batch(config: dict) -> None:
    """Con miles de fotografías, una corrupta no puede costar la corrida."""
    fuente = FuenteFalsa(
        [_remota("a.heic", "1"), _remota("rota.heic", "2"), _remota("c.heic", "3")],
        fallar={"rota.heic"},
    )

    reporte = ingest_images(config, source=fuente)

    assert reporte.downloaded == 2
    assert reporte.failed == 1
    assert any("rota.heic" in e for e in reporte.errors)


def test_limit_stops_early(config: dict) -> None:
    fuente = FuenteFalsa([_remota(f"{i}.heic", str(i)) for i in range(10)])

    reporte = ingest_images(config, source=fuente, limit=3)

    assert reporte.downloaded == 3
    assert len(fuente.descargas) == 3


def test_batching_does_not_change_the_result(config: dict) -> None:
    """Procesar por lotes acota la memoria; no debe alterar lo que se trae."""
    imagenes = [_remota(f"{i}.heic", str(i)) for i in range(7)]

    reporte = ingest_images(config, source=FuenteFalsa(imagenes), batch_size=2)

    assert reporte.downloaded == 7


# --- Fuente local ---------------------------------------------------------------

def test_local_source_only_lists_images(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "foto.HEIC").write_bytes(b"x")
    (raw / "otra.jpg").write_bytes(b"x")
    (raw / "notas.txt").write_text("no es una imagen")

    encontradas = {i.name for i in LocalDirectorySource(raw).list_available()}

    assert encontradas == {"foto.HEIC", "otra.jpg"}


def test_local_source_reports_when_the_folder_is_missing(tmp_path: Path) -> None:
    fuente = LocalDirectorySource(tmp_path / "no-existe")

    assert not fuente.is_available()
    assert list(fuente.list_available()) == []


def test_cache_key_prefers_the_checksum() -> None:
    """Con huella del proveedor no hace falta adivinar por tamaño y fecha."""
    con_suma = _remota("a.heic", "abc")
    sin_suma = _remota("a.heic", None)

    assert con_suma.cache_key() == "sum:abc"
    assert "id-a.heic" in sin_suma.cache_key()
