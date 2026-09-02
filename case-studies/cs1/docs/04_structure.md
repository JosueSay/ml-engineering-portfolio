# Estructura del proyecto

Qué hay en cada carpeta y por qué está donde está. Parte de la documentación;
el índice está en [README.md](README.md).

## Vista general

```
cs1/
├── config/               Parametros versionados
├── src/gasolina_gt/      El paquete: la logica del caso
├── scripts/              Orquestacion: arranque, credenciales y etapas
├── tests/                Pruebas unitarias y de integracion
├── experiments/          Lo explorado y descartado, fuera del camino productivo
├── docs/                 Esta documentacion
├── data/                 Fotografias y capas de datos      (ignorado por git)
├── models/               Pesos y artefactos                (ignorado por git)
├── keys/                 Credenciales                      (ignorado por git)
├── logs/                 Registros de corrida              (ignorado por git)
├── Makefile              Atajos
├── Dockerfile            Imagen
├── compose.yaml          Composicion de servicios
├── pyproject.toml        Declaracion del paquete y del linter
└── .env.example          Plantilla de entorno versionada
```

## El paquete

```
src/gasolina_gt/
├── config.py             Acceso a los tres niveles de configuracion
├── cli.py                Interfaz de linea de comandos
├── extraction/           De una fotografia a pares (combustible, precio)
│   ├── heic_loader.py    Carga y fecha real de captura
│   ├── privacy.py        Difuminado de caras
│   ├── calibration.py    Region del panel de cada combustible
│   ├── preprocess.py     Aislamiento del visor
│   ├── digit_ocr.py      Lectura de digitos
│   └── extractor.py      Orquestador y validacion
├── data/                 Capas Bronze, Silver y Gold
│   ├── pipeline.py       Construccion de las capas
│   └── features.py       Variables de modelado
├── augmentation/         Aumento de imagenes y de series
├── modeling/training.py  Entrenamiento con validacion temporal
├── evaluation/metrics.py Metricas y compuerta de calidad
├── scraping/             Precio de referencia externo
└── serving/              API y recomendacion
```

Los módulos de `extraction/` están en el orden en que se aplican. Cada uno
puede fallar sin tumbar al siguiente: una fotografía sin fecha, un panel fuera
del encuadre o un dígito ilegible producen un registro con su motivo, no una
excepción que detenga el lote.

## Datos

**Ninguna imagen entra al control de versiones.** El repositorio guarda código
y documentación; las fotografías viven en el almacenamiento externo.

```
data/
├── raw/                  Originales tal como llegan. Nunca se editan.
├── interim/              Recortes de la franja de precios
└── processed/
    ├── bronze/           Lectura cruda, con las invalidas y su motivo
    ├── silver/           Tabla limpia de precio por fecha y combustible
    └── gold/             Conjunto con variables de modelado
```

Las tres capas existen para poder retroceder hasta el origen sin haberlo
destruido. Bronze es fiel a lo que se leyó, incluidos los rechazos; Silver deja
solo lo válido; Gold añade lo que el modelo necesita.

El recorte en `interim/` no es solo un ahorro de cómputo: es la evidencia de
qué se leyó. Ante una lectura sospechosa se puede mirar exactamente la porción
de píxeles que la generó.

Cada carpeta lleva un marcador para que la estructura exista en un clon nuevo
sin que viaje su contenido.

## Modelos

```
models/
├── vendor/               Pesos de terceros. Desechables.
├── trained/              Artefactos propios del entrenamiento
└── manifest.json         Registro versionado de que se entreno y con que datos
```

Están separados porque tienen ciclos de vida opuestos. El manifiesto es la
única parte que entra al control de versiones: es texto, guarda la huella del
conjunto con el que se entrenó cada modelo, sus hiperparámetros y la versión
del paquete, y permite responder si un modelo se entrenó con los datos que uno
cree, sin guardar un solo binario en el repositorio.

## Configuración

```
config/
├── config.yaml           Parametros de negocio y de modelo
└── panelCalibration.json Regiones de panel calibradas
```

Secciones de `config.yaml`:

| Sección | Qué controla |
|---|---|
| `paths` | Ubicación de cada capa, almacén y artefacto |
| `archivos` | Nombres de los archivos de salida |
| `extraccion` | Orden de combustibles, rango plausible, confianza mínima |
| `calibracion_camara` | Perfiles de encuadre |
| `negocio` | Combustible principal, horizontes, moneda, unidad |
| `modelado` | Hiperparámetros, umbrales, semilla, ventana de prueba |
| `evaluacion` | Criterios de la compuerta de calidad |
| `recomendacion` | Margen de decisión y horas pico |
| `scraping` | Fuente del precio de referencia |
| `augmentation` | Parámetros del aumento de datos |

`archivos` existe por un motivo concreto: esos nombres estaban repetidos en el
módulo que escribe y en el que lee, y dos literales que tienen que coincidir
acaban por no hacerlo.

Las variables de entorno están documentadas aparte, en
[02_environment.md](02_environment.md).

## Scripts

Numerados por orden de ejecución. La lógica vive aquí; el `Makefile` es solo el
atajo.

```
scripts/
├── 00_verify_environment.sh   Comprueba la maquina
├── 01_env_init.sh             Entorno local
├── 02_keys_init.sh            Credenciales
├── 03_gates.sh                Puertas de calidad
├── 12_extract_prices.py       Bronze
├── 15_quality_gate.py         Compuerta de calidad
└── 31_models_status.py        Estado del almacen de modelos
```

La numeración deja huecos a propósito: los pasos que faltan tienen su número
reservado. Cuáles son y en qué fase entran está en
[work-plan.md](work-plan.md).

## Experimentos

```
experiments/
└── florence2-vision/     Extraccion con un modelo de vision y lenguaje
```

Guarda lo que se probó y no quedó, con el motivo del descarte. Nada de ahí se
instala con el paquete, se ejecuta en la integración continua ni entra en la
imagen. Tiene sus propias dependencias, fijadas por versión exacta porque
existe para reproducir lo que se probó, no para correr con lo último de cada
biblioteca.

## Qué no entra al control de versiones

| Carpeta | Motivo |
|---|---|
| `data/` | El repositorio guarda código, no fotografías |
| `models/` | Los pesos son binarios grandes. Sí entra `manifest.json` |
| `keys/` | Credenciales. Sí entra su `README.md` |
| `logs/`, `reports/` | Artefactos de ejecución, reproducibles |
| `.env` | Configuración local. Sí entra `.env.example` |
| `.venv/` | Entorno virtual |

`make gates` comprueba que ninguna credencial ni ninguna imagen se hayan
colado, porque un `.gitignore` correcto no protege de un `git add -f` ni de un
archivo que ya estaba en el índice antes de la regla.
