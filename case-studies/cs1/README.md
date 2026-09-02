# CS1 — Precios de combustible en Guatemala

[![Pipeline](https://github.com/JosueSay/ml-engineering-portfolio/actions/workflows/cs1-ml-pipeline.yml/badge.svg?branch=main)](https://github.com/JosueSay/ml-engineering-portfolio/actions/workflows/cs1-ml-pipeline.yml)
[![Publicación](https://github.com/JosueSay/ml-engineering-portfolio/actions/workflows/cs1-publish.yml/badge.svg)](https://github.com/JosueSay/ml-engineering-portfolio/actions/workflows/cs1-publish.yml)
[![TestPyPI](https://img.shields.io/pypi/v/fuel-price-gt?pypiBaseUrl=https%3A%2F%2Ftest.pypi.org&label=TestPyPI)](https://test.pypi.org/project/fuel-price-gt/)
[![Imagen](https://img.shields.io/badge/ghcr.io-fuel--price--gt-blue?logo=docker&logoColor=white)](https://github.com/JosueSay/ml-engineering-portfolio/pkgs/container/fuel-price-gt)
[![Python](https://img.shields.io/pypi/pyversions/fuel-price-gt?pypiBaseUrl=https%3A%2F%2Ftest.pypi.org)](https://test.pypi.org/project/fuel-price-gt/)
[![Licencia](https://img.shields.io/badge/licencia-MIT-blue)](https://github.com/JosueSay/ml-engineering-portfolio/blob/main/LICENSE)

Las dos primeras dicen si el sistema está en pie ahora mismo, no si lo estuvo
alguna vez: una entrega que solo se puede comprobar abriendo el historial de
corridas no está comprobada.

Caso de estudio de extracción y pronóstico de precios de combustible a partir
de fotografías de tótems de gasolinera.

El plan de trabajo, las decisiones tomadas y lo que falta están en
[docs/work-plan.md](https://github.com/JosueSay/ml-engineering-portfolio/blob/main/case-studies/cs1/docs/work-plan.md).

## Qué hace

De cada fotografía se extraen los cuatro precios del panel (diésel, regular,
súper, V-Power), se llevan a una base histórica trazable y sobre ella se
predice el precio a 1, 2 y 4 semanas con una señal de tendencia y una
recomendación de carga.

Dos mitades que no se mezclan: la extracción es visión, la estimación es
regresión sobre una serie temporal.

La lectura de dígitos es determinista y no necesita tarjeta gráfica: compara la
forma de cada dígito contra plantillas de siete segmentos y se queda con el
mejor solapamiento. Si el motor alterno de reconocimiento de texto está
instalado, se usa como segunda opinión y gana el de mayor confianza.

## Instalación

```bash
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ fuel-price-gt
```

El segundo índice hace falta porque las dependencias viven en el índice normal,
no en el de pruebas.

Instalado funciona sin clonar el repositorio, desde cualquier carpeta:

```bash
fuel-price-gt build-data          # construye el conjunto de modelado
```

Eso es lo que trae la instalación mínima: leer fotografías y construir las
capas de datos. Entrenar y recomendar necesitan el extra de modelado, porque
para leer un modelo hace falta la misma biblioteca con la que se escribió:

```bash
pip install "fuel-price-gt[modeling]"
fuel-price-gt train --fuel regular
fuel-price-gt recommend --fuel regular
```

Pedirlos sin el extra no revienta: dice qué instalar. Los demás extras siguen
el mismo criterio, no arrastrar lo que no se va a usar:

```bash
pip install "fuel-price-gt[serving]"   # servicio web
pip install "fuel-price-gt[gdrive]"    # carpeta privada de Drive
pip install "fuel-price-gt[all]"       # todo
```

### Como contenedor

La misma versión, con el servicio web ya montado:

```bash
docker run -p 19010:8000 \
  -v "$PWD/data:/app/data" \
  -v "$PWD/models:/app/models" \
  ghcr.io/josuesay/fuel-price-gt:0.3.4
```

Los datos y los modelos entran por volumen, no dentro de la imagen: meterlos
obligaría a reconstruir por cada fotografía nueva.

Para trabajar sobre el código, en cambio, se clona el repositorio y se sigue la
puesta en marcha de abajo.

## Puesta en marcha

Todos los comandos se ejecutan **desde `case-studies/cs1/`**.

```bash
make verify        # comprueba interprete, dependencias y estructura
make venv          # crea el entorno virtual
make install-dev   # instala el paquete y las herramientas de desarrollo
make env-init      # crea .env desde la plantilla versionada
make keys-status   # informa que credenciales faltan, sin crear nada
```

`make verify` es el primero por una razón: el fallo más común no es un error de
código sino un intérprete equivocado. El proyecto necesita Python 3.11 o
superior, y `python3` puede apuntar a una versión anterior del sistema.

`make help` lista todos los comandos disponibles, agrupados por etapa.

## Ejecución

```bash
make extract       # lee los precios de las fotografias (Bronze)
make transform     # construye Silver y Gold
make train         # entrena y evalua los horizontes configurados
make evaluate      # compuerta de calidad
make recommend     # recomendacion de carga
make pipeline      # encadena todo lo anterior
```

El combustible y el horizonte se pasan por variable:

```bash
make train FUEL=super
make recommend FUEL=diesel HORIZON=2 HOUR=18
```

La lógica vive en `scripts/` y en la interfaz de línea de comandos del paquete;
el `Makefile` es solo el atajo. El mismo comando corre sin `make`, y la
integración continua llama a los scripts directamente.

## Configuración

Tres niveles, y cada valor cae en exactamente uno.

| Nivel | Dónde | Qué | Versionado |
|---|---|---|---|
| 1 | `config/config.yaml` | Parámetros de negocio y de modelo | Sí |
| 2 | `.env` | Lo que cambia por máquina o entorno, nunca sensible | No, solo `.env.example` |
| 3 | `keys/` | Credenciales reales, en archivos | No, solo su documentación |

Para decidir dónde va un valor nuevo, en este orden:

1. ¿Es igual en todas las máquinas y define cómo se comporta el sistema? A
   `config/config.yaml`.
2. ¿Cambia por máquina o entorno, pero se puede publicar sin riesgo? A `.env`.
3. ¿Da acceso a algo? A `keys/`, como archivo.

De ahí la regla que sostiene el tercer nivel: **`.env` nunca contiene el valor
de una credencial, solo la ruta al archivo que la guarda**. Las variables
sensibles terminan en `_FILE` y se leen con `read_secret`. Así una credencial
no aparece en un volcado de entorno, ni en un registro de arranque, ni en una
captura de pantalla de la terminal.

Qué credencial hace falta para qué, cómo se obtiene y con qué permisos mínimos:
[keys/README.md](keys/README.md).

### Puertos

Se parametrizan siempre y salen del rango reservado del proyecto, **19000 a
19099**, elegido por debajo de donde el sistema empieza a asignar puertos
efímeros por su cuenta y fuera de los puertos habituales de desarrollo.

| Puerto | Servicio | Variable |
|---|---|---|
| 19010 | API de pronóstico | `API_PORT` |
| 19020 | Base de datos, si se usa un motor servidor | `DB_PORT` |
| 19030 | Explorador de la base de datos | `DB_BROWSER_PORT` |
| 19040, 19041 | Almacenamiento de objetos | `OBJECT_STORE_PORT`, `OBJECT_STORE_CONSOLE_PORT` |

## Datos

**Ninguna imagen entra al control de versiones.** El repositorio guarda código
y documentación; las fotografías viven en el almacenamiento externo y se
descargan.

```
data/
├── raw/         Originales tal como llegan. Nunca se editan.
├── interim/     Recortes de la franja de precios.
└── processed/
    ├── bronze/  Lectura cruda por imagen, con las invalidas y su motivo
    ├── silver/  Tabla limpia de precio por fecha y combustible
    └── gold/    Conjunto con variables de modelado
```

Los originales no se modifican nunca: cada transformación produce un archivo
nuevo en otra carpeta. El recorte no es solo un ahorro de cómputo, es la
evidencia de qué se leyó; ante una lectura sospechosa se puede mirar
exactamente la porción de píxeles que la generó.

## Modelos

```
models/
├── vendor/    Pesos de terceros. Desechables, se vuelven a bajar.
└── trained/   Artefactos propios, uno por corrida de entrenamiento.
```

Están separados porque tienen ciclos de vida opuestos, y por eso hay dos
objetivos de limpieza distintos: `make clean-vendor` y `make clean-trained`.
Ningún peso entra al repositorio.

## Contenedores

```bash
make up            # levanta el stack
make ps            # estado
make logs          # sigue los registros
make down          # detiene conservando los volumenes
make docker-smoke  # construye y verifica que la API responda
```

Los datos y los modelos entran por volumen, no dentro de la imagen: meterlos
obligaría a reconstruir por cada foto nueva y haría crecer la imagen sin
control con el histórico completo.

## Calidad

```bash
make gates   # linter, pruebas y revision de secretos
make lint
make test
make format  # reescribe archivos
```

`make gates` es lo que hay que pasar antes de confirmar cambios. Además del
linter y las pruebas comprueba tres cosas que ninguna de las dos ve: que no se
haya versionado una credencial, que no se haya versionado una imagen, y que
`.env` no se haya desincronizado de su plantilla.

## Estructura

```
cs1/
├── config/
│   ├── config.yaml           Parametros de negocio y de modelo
│   └── panelCalibration.json Regiones de panel calibradas
├── src/fuel_price_gt/
│   ├── extraction/           Carga, privacidad, calibracion, lectura de digitos
│   ├── data/                 Capas Bronze, Silver y Gold, y variables
│   ├── augmentation/         Aumento de imagenes y de series
│   ├── modeling/             Entrenamiento con validacion temporal
│   ├── evaluation/           Metricas y compuerta de calidad
│   ├── scraping/             Precio de referencia externo
│   └── serving/              API y recomendacion
├── scripts/                  Logica de arranque, credenciales y etapas
├── experiments/              Lo explorado y descartado, fuera del camino productivo
├── data/                     Ignorado por git
├── models/                   Ignorado por git
├── keys/                     Ignorado por git, salvo su documentacion
└── docs/work-plan.md         Plan, decisiones y pendientes
```

## Experimentos

`experiments/` guarda lo que se probó y no quedó, con el motivo del descarte.
Nada de ahí se instala con el paquete, se ejecuta en la integración continua ni
entra en la imagen. Ver [experiments/README.md](experiments/README.md).

## Problemas comunes

**`ImportError` al importar, o pruebas que fallan al recolectar**

El intérprete es anterior a 3.11. `make verify` lo dice y señala dónde hay uno
válido.

**`FileNotFoundError` buscando `config/config.yaml`**

Se está ejecutando desde el directorio equivocado. Todos los comandos van desde
`case-studies/cs1/`. Si hace falta ejecutar desde otro sitio, se declara la
raíz con `FUEL_PRICE_GT_ROOT`.

**El pipeline no encuentra fotografías**

`data/raw` está vacía, que es el estado normal de un clon nuevo: las imágenes
no se versionan. Hay que poblarla desde el almacenamiento externo.

**Aviso de enlaces simbólicos al descargar modelos en Windows**

Es esperado sin el modo de desarrollador activado. Funciona igual, solo usa más
disco.
