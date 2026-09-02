# Comandos

Referencia de los comandos del caso de estudio. Parte de la documentación; el
índice está en [README.md](README.md).

## Doble interfaz

La lógica vive en `scripts/` y en la interfaz de línea de comandos del paquete.
El `Makefile` es **solo el atajo**: cada objetivo es una línea que invoca a uno
de los dos.

Eso tiene dos consecuencias buscadas. El mismo comando corre sin `make`, que no
está instalado por defecto en todas las plataformas. Y la integración continua
llama a los scripts directamente, así que no depende de `make` para nada.

La otra regla es que **solo se declara lo que existe**. Un objetivo que apunta
a un script inexistente es una promesa rota; lo pendiente vive en
[work-plan.md](work-plan.md), no en el `help`.

```bash
make help    # lista todo, agrupado por etapa
```

Todos los comandos se ejecutan desde `case-studies/cs1/`.

## Puesta en marcha

| Comando | Equivalente sin make | Qué hace |
|---|---|---|
| `make verify` | `bash scripts/00_verify_environment.sh` | Comprueba intérprete, dependencias, herramientas y estructura |
| `make venv` | `python3 -m venv .venv` | Crea el entorno virtual |
| `make install` | `pip install -e .` | Instala el paquete |
| `make install-dev` | `pip install -e '.[dev]'` | Instala el paquete y las herramientas de desarrollo |
| `make env-init` | `bash scripts/01_env_init.sh` | Crea `.env` desde la plantilla versionada |
| `make env-check` | `bash scripts/01_env_init.sh --check` | Compara `.env` con la plantilla, sin escribir |
| `make keys-init` | `bash scripts/02_keys_init.sh` | Prepara `keys/` y materializa lo que haya en el entorno |
| `make keys-status` | `bash scripts/02_keys_init.sh --status` | Dice qué credenciales faltan, sin crear ni imprimir nada |

`make verify` va primero por una razón concreta: el fallo más común no es un
error de código sino un intérprete equivocado. El proyecto necesita Python 3.11
o superior y `python3` puede apuntar a una versión anterior del sistema, con lo
que las pruebas fallan al importar con un mensaje que no dice nada sobre la
causa real.

### Primera vez

```bash
make verify
make venv
make install-dev
make env-init
make keys-status
make gates
```

## Pipeline de datos

| Comando | Equivalente sin make | Qué hace |
|---|---|---|
| `make ingest` | `python scripts/10_ingest_images.py` | Trae las fotografías de la fuente configurada. `LIMIT=10` para probar |
| `make extract` | `python scripts/12_extract_prices.py` | Lee los precios de las fotografías (Bronze) |
| `make transform` | `python -m fuel_price_gt.cli build-data` | Construye Silver y Gold |
| `make train` | `python -m fuel_price_gt.cli train --fuel regular` | Entrena y evalúa los horizontes configurados |
| `make evaluate` | `python scripts/15_quality_gate.py` | Compuerta de calidad sobre el modelo entrenado |
| `make recommend` | `python -m fuel_price_gt.cli recommend ...` | Recomendación de carga |
| `make pipeline` | los cinco anteriores en orden | Encadena todas las etapas |

Las etapas del pipeline son parte del paquete y se invocan por su interfaz de
línea de comandos, sin script envoltorio: una capa que solo reenvía argumentos
es una capa que hay que mantener sin que aporte nada.

Cada etapa se puede ejecutar por separado a propósito. Encadenarlas siempre
obligaría a repetir la extracción, que es la parte cara, cada vez que falla
algo posterior.

### Parámetros

| Variable | Por defecto | Valores |
|---|---|---|
| `FUEL` | `regular` | `regular`, `super`, `diesel`, `vpower` |
| `HORIZON` | `1` | `1`, `2`, `4` semanas |
| `HOUR` | `18` | Hora del día, 0 a 23 |

```bash
make train FUEL=super
make recommend FUEL=diesel HORIZON=2 HOUR=7
```

## Base de datos

| Comando | Qué hace |
|---|---|
| `make db-init` | Crea el esquema si falta y dice cuántas filas hay en cada tabla |
| `make db-browser` | Levanta el explorador web para recorrer el linaje |

`db-init` es idempotente y no borra nada. Vaciar la base es una operación
aparte y deliberada, porque perder el linaje significa perder la respuesta a
por qué un precio vale lo que vale.

El modelo de datos y cómo consultarlo están en
[06_data_model.md](06_data_model.md).

## Modelos

| Comando | Qué hace |
|---|---|
| `make models-status` | Qué hay en cada almacén y con qué datos se entrenó cada modelo |
| `make clean-vendor` | Borra los pesos de terceros. Se vuelven a descargar |
| `make clean-trained` | Borra los artefactos propios. Obliga a reentrenar |

Hay dos objetivos de limpieza porque los dos almacenes tienen ciclos de vida
opuestos: borrar un peso descargado no cuesta nada, borrar un artefacto propio
obliga a repetir el entrenamiento.

## Contenedores

| Comando | Qué hace |
|---|---|
| `make up` | Levanta el stack |
| `make down` | Lo detiene conservando los volúmenes |
| `make logs` | Sigue los registros. `SERVICE=api` para uno solo |
| `make ps` | Estado de los contenedores |
| `make docker-build` | Construye la imagen de producción |
| `make docker-smoke` | Construye y verifica que la API responda |

Los datos y los modelos entran por volumen, no dentro de la imagen.

## Calidad

| Comando | Qué hace |
|---|---|
| `make gates` | Todas las puertas. Es lo que hay que pasar antes de confirmar cambios |
| `make lint` | Análisis estático |
| `make test` | Pruebas |
| `make format` | Reformatea. **Reescribe archivos** |

`make gates` comprueba cinco cosas, y tres de ellas no las ve ni el linter ni
las pruebas:

1. Análisis estático, incluidas las reglas de seguridad, nomenclatura y
   documentación.
2. Pruebas.
3. Que no se haya versionado ninguna credencial.
4. Que no se haya versionado ninguna imagen.
5. Que `.env` no se haya desincronizado de su plantilla.

## Limpieza

| Comando | Qué borra | Qué **no** toca |
|---|---|---|
| `make clean` | Reportes y cachés | `data/`, `keys/`, modelos |
| `make clean-logs` | Registros de corrida | Todo lo demás |
| `make clean-vendor` | Pesos de terceros | Artefactos propios |
| `make clean-trained` | Artefactos propios | Pesos de terceros |

Ningún comando de limpieza toca `data/` ni `keys/`: recuperar una credencial o
volver a descargar el conjunto de fotografías cuesta mucho más que reejecutar
cualquier etapa.

## Scripts

Numerados por orden de ejecución. Los que aún no existen están en el plan de
trabajo, no aquí.

| Script | Qué hace |
|---|---|
| `00_verify_environment.sh` | Comprueba que la máquina tiene lo necesario |
| `01_env_init.sh` | Crea `.env` desde la plantilla. Admite `--check` y `--force` |
| `02_keys_init.sh` | Prepara `keys/`. Admite `--status` |
| `03_gates.sh` | Puertas de calidad |
| `10_ingest_images.py` | Etapa de ingesta, con caché de descarga y lotes |
| `12_extract_prices.py` | Etapa de extracción, con caché por huella |
| `20_db_init.py` | Crea el esquema y reporta su estado |
| `15_quality_gate.py` | Compuerta de calidad |
| `31_models_status.py` | Estado del almacén de modelos |
| `tools/compare_ocr_engines.py` | Compara motores de reconocimiento sobre los mismos recortes |
