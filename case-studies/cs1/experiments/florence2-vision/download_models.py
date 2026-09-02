"""Descarga y cachea el modelo de caja negra. Correr una vez.

Fija la revision declarada en config.yml. El repo de Florence-2 no publica tags
ni releases, solo la rama main, y el commit 00d2f157 (2024-12-08) cambio los
pesos al modelo de contexto 4k. Fijar el SHA exacto es parte del procedimiento
reproducible; ademas acota que codigo remoto se ejecuta (trust_remote_code).
"""

from typing import Any

from transformers import AutoModelForCausalLM, AutoProcessor

from core.config import MODEL_HFA, PATH_STORAGE_MODEL, REVISIONS

# Anotar la tupla, no solo su contenido: es lo que hace que un checker detecte
# el clasico (MODEL_HFA) sin coma, que es un str y se itera letra por letra.
MODELOS: tuple[str, ...] = (MODEL_HFA,)

# El codigo remoto de Florence-2 declara _supports_sdpa como property que lee
# self.language_model, pero transformers >= 4.5x consulta ese flag dentro de
# PreTrainedModel.__init__, antes de que language_model exista. Pedir eager
# evita esa rama. El costo es no usar SDPA en inferencia.
ATTN_IMPLEMENTATION: str = "eager"


def descargar(model_id: str) -> None:
    revision: str | None = REVISIONS.get(model_id)
    if revision is None:
        raise KeyError(f"falta la revision de {model_id} en config.yml")
    print(f"descargando {model_id} (revision {revision}) ...")
    kwargs: dict[str, Any] = dict(
        cache_dir=str(PATH_STORAGE_MODEL),
        revision=revision,
        trust_remote_code=True,
    )
    AutoProcessor.from_pretrained(model_id, **kwargs)
    AutoModelForCausalLM.from_pretrained(
        model_id, attn_implementation=ATTN_IMPLEMENTATION, **kwargs
    )
    print(f"listo {model_id}")


if __name__ == "__main__":
    for mid in MODELOS:
        descargar(mid)
