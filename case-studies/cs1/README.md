# CS1 — Fuel case study

Caso de estudio sobre Florence-2 como modelo de caja negra. La reproducibilidad
depende de fijar la revision exacta del modelo, no solo su nombre: el repo de
Hugging Face no publica tags y sus pesos ya cambiaron una vez sobre la misma
rama `main`.

## Requisitos

- Python 3.11+
- ~4 GB libres en disco (1.5 GB de pesos + torch y sus dependencias)
- Conexion a internet para la primera corrida

## Instalacion

Todos los comandos se corren **desde `case-studies/cs1/`**, no desde la raiz del
repo. Eso importa: los modulos importan `core.config`, y `core/` solo esta en el
path si el directorio de trabajo es `cs1`.

```bash
python -m venv .venv
```

Activar el entorno:

```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

> `requirements.txt` debe estar en **UTF-8**. Si lo regeneras en PowerShell 5.1,
> `pip freeze > requirements.txt` lo escribe en UTF-16 y `pip install` falla con
> `Invalid requirement: 'n\x00u\x00m\x00p\x00y\x00...'`. Usa:
>
> ```powershell
> python -m pip freeze | Set-Content -Encoding utf8 requirements.txt
> ```

## Uso

### 1. Descargar el modelo

```bash
python download_models.py
```

Script suelto, no modulo: vive en la raiz de `cs1`, asi que Python ya pone ese
directorio en `sys.path` y `from core.config import ...` resuelve.

Baja ~1.5 GB a `models/` y cachea el modelo bajo la revision fijada en
`config.yml`. Es idempotente: si el cache ya esta, no vuelve a descargar.

Corre `trust_remote_code=True`, o sea que ejecuta el `modeling_florence2.py` del
repo de Microsoft. Fijar el SHA acota exactamente que codigo se ejecuta.

### 2. Convertir imagenes HEIC a JPG

```bash
python -m imageConvert.convert --input <dir> --output <dir> [--delete]
```

Este si es **modulo** (`python -m`), no script. Si lo corres como
`python imageConvert/convert.py`, Python pone `imageConvert/` en `sys.path` en
vez de `cs1/`, y cualquier import de `core.` deja de resolver. `python -m` corre
desde `cs1/`, que es lo que se quiere.

- `--input` y `--output` son requeridos: no hay rutas por defecto.
- `--delete` borra el `.heic` original **solo** si la conversion fue exitosa.
- El manifiesto de cada corrida queda en `imageConvert/output/manifest.json`.

## Configuracion

Todo parametro vive en `config.yml`; no hay rutas absolutas en el codigo. Las
rutas del yml son relativas a `cs1/` y `core/config.py` las ancla a la raiz del
proyecto con `Path(__file__).resolve().parent.parent`, no al directorio actual.

| Clave | Que controla |
|---|---|
| `models.path_storage_models` | Cache de pesos de Hugging Face |
| `models.model_hfa` | Model id en el Hub |
| `models.revision_hfa` | **SHA del commit**. Ver nota abajo |
| `data.path_raw_data` | Imagenes de entrada sin procesar |
| `logging.path_storage_log` | Destino de los `.jsonl` de corrida |
| `logging.level` | Nivel de log |
| `output.path_storage_output` | Artefactos de salida |

### Sobre `revision_hfa`

`microsoft/Florence-2-large` no publica tags ni releases: solo la rama `main`.
El commit `00d2f157` (2024-12-08) **cambio los pesos** al modelo de contexto 4k,
asi que "el modelo" no es una cosa fija. Por eso se fija el SHA completo y no
`main`. Si lo cambias, los resultados dejan de ser comparables con los anteriores.

`download_models.py` falla ruidosamente si la revision no esta declarada, en vez
de caer silenciosamente a `main`.

### Nota sobre `attn_implementation`

Se pide `eager` a proposito. El codigo remoto de Florence-2 declara
`_supports_sdpa` como una property que lee `self.language_model`, pero
transformers 4.57 consulta ese flag dentro de `PreTrainedModel.__init__`, antes
de que `language_model` exista. El costo es no usar SDPA en inferencia.

La alternativa es `florence-community/Florence-2-large` (rev `4271c66b`), que usa
el soporte nativo de transformers, no ejecuta codigo remoto y si despacha SDPA.

## Estructura

```
cs1/
├── config.yml              # Toda la parametrizacion
├── download_models.py      # Entry point: cachea el modelo (script)
├── core/
│   ├── config.py           # Carga config.yml, ancla rutas a la raiz
│   ├── logging_setup.py    # Consola legible + JSONL por corrida
│   └── jsonio.py           # json.dump tolerante a tipos de numpy
├── imageConvert/           # Entry point: HEIC -> JPG (modulo, python -m)
├── models/                 # Cache de pesos (ignorado por git)
├── data/raw/               # Entrada (ignorado por git)
├── logs/                   # JSONL por corrida (ignorado por git)
└── output/                 # Artefactos (ignorado por git)
```

## Problemas comunes

**`KeyError: falta la revision de ... en config.yml`**
Falta `models.revision_hfa`, o el model id del yml no coincide con la llave del
diccionario `REVISIONS`.

**`ModuleNotFoundError: No module named 'core'`**
Estas corriendo desde el directorio equivocado. Todos los comandos van desde
`case-studies/cs1/`.

**`Invalid requirement: 'n\x00u\x00m\x00p\x00y\x00...'`**
`requirements.txt` quedo en UTF-16. Ver la nota en Instalacion.

**Warning de symlinks de `huggingface_hub` en Windows**
Es esperado sin Developer Mode. Funciona igual, solo usa mas disco.
