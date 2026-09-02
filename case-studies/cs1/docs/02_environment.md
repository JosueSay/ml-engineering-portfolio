# Variables de entorno

Referencia completa de `.env`. Parte de la documentación del caso de estudio;
el índice está en [README.md](README.md).

## Dónde va cada valor

La configuración del proyecto se reparte en tres niveles y cada valor cae en
exactamente uno.

| Nivel | Ubicación | Contenido | Versionado |
|---|---|---|---|
| 1 | `config/config.yaml` | Parámetros de negocio y de modelo | Sí |
| 2 | `.env` | Lo que cambia por máquina o entorno, nunca sensible | No, solo `.env.example` |
| 3 | `keys/` | Credenciales reales, en archivos | No, solo su documentación |

Para decidir dónde va un valor nuevo, en este orden:

1. ¿Es igual en todas las máquinas y define cómo se comporta el sistema? A
   `config/config.yaml`.
2. ¿Cambia por máquina o entorno, pero se puede publicar sin riesgo? A `.env`.
3. ¿Da acceso a algo? A `keys/`, como archivo.

De ahí la regla que sostiene el tercer nivel:

> **`.env` nunca contiene el valor de una credencial, solo la ruta al archivo
> que la guarda.**

Las variables sensibles terminan en `_FILE` y apuntan dentro de `keys/`. Así
una credencial no aparece en un volcado de entorno, ni en un registro de
arranque, ni en una captura de pantalla de la terminal. En el código se leen
con `read_secret()`, nunca con `env()`.

## Cómo se crea y se mantiene

```bash
make env-init    # crea .env a partir de .env.example
make env-check   # compara ambos y dice qué falta o qué sobra
```

`.env.example` es la fuente de verdad de qué variables existen y sí se
versiona. Al agregar una variable se agrega ahí, y `make env-check` avisa a
quien tenga su `.env` desactualizado. Esa comprobación forma parte de
`make gates`.

Una variable definida de verdad en el entorno **gana** sobre el archivo. Es lo
que permite que la integración continua o un contenedor sobreescriban un valor
sin editar nada:

```bash
APP_ENV=production make recommend
```

## Referencia

### Entorno

| Variable | Por defecto | Para qué |
|---|---|---|
| `APP_ENV` | `local` | Entorno activo: `local`, `development`, `staging` o `production` |
| `LOG_LEVEL` | `INFO` | Nivel de detalle de los registros |

### Rutas del proyecto

| Variable | Por defecto | Para qué |
|---|---|---|
| `FUEL_PRICE_GT_ROOT` | vacío | Raíz del proyecto. Vacío significa deducirla de la ubicación del paquete; se rellena para apuntar a otra, por ejemplo dentro de un contenedor |
| `FUEL_PRICE_GT_CONFIG` | vacío | Ruta a un `config.yaml` alterno, para correr con otra parametrización sin tocar la del repositorio |

### Base de datos

| Variable | Por defecto | Para qué |
|---|---|---|
| `DATABASE_URL` | `sqlite+pysqlite:///data/fuel-prices.db` | Conexión. El motor embebido por defecto es un archivo y no necesita servicio |

Con el motor embebido esto es una ruta y su sensibilidad es baja. Si se pasa a
un motor servidor la cadena lleva la contraseña embebida y deja de ser apta
para este archivo: entonces la contraseña va a `keys/` y aquí queda solo su
ruta.

### Fuente de imágenes

| Variable | Por defecto | Para qué |
|---|---|---|
| `IMAGE_SOURCE` | `local` | Proveedor activo: `local`, `gdrive` u `object-store` |
| `IMAGE_RAW_DIR` | `data/raw` | Originales, tal como llegan |
| `IMAGE_INTERIM_DIR` | `data/interim` | Recortes de la franja de precios |
| `IMAGE_CACHE_DIR` | `data/raw` | Dónde se cachea lo descargado |

Sin credenciales configuradas el sistema siempre cae a `local`, para que la
integración continua siga funcionando en ramas sin acceso.

### Modelos

| Variable | Por defecto | Para qué |
|---|---|---|
| `MODELS_DIR` | `models` | Raíz de los dos almacenes: `vendor` y `trained` |

### Puertos

Se parametrizan siempre y salen del **rango reservado 19000-19099**, elegido
por dos razones: está por debajo de 32768, que es donde el sistema empieza a
asignar puertos efímeros por su cuenta, y fuera de los puertos habituales de
desarrollo (3000, 5000, 5432, 8000, 8080, 27017).

| Variable | Por defecto | Servicio |
|---|---|---|
| `API_PORT` | `19010` | API de pronóstico |
| `DB_PORT` | `19020` | Base de datos, si se usa un motor servidor |
| `DB_BROWSER_PORT` | `19030` | Explorador de la base de datos |
| `OBJECT_STORE_PORT` | `19040` | Almacenamiento de objetos, interfaz de programación |
| `OBJECT_STORE_CONSOLE_PORT` | `19041` | Almacenamiento de objetos, consola web |

Los puertos 19050 a 19099 quedan libres para servicios futuros del mismo
proyecto.

### Google Drive

| Variable | Por defecto | Para qué |
|---|---|---|
| `GDRIVE_FOLDER_ID` | vacío | Identificador de la carpeta compartida |
| `GDRIVE_CREDENTIALS_FILE` | `keys/google-drive-service-account.json` | **Ruta** a la credencial, no la credencial |

El identificador de carpeta es un caso de frontera: señala un recurso privado
pero no da acceso por sí solo, así que se queda en este nivel.

### Almacenamiento de objetos

| Variable | Por defecto | Para qué |
|---|---|---|
| `OBJECT_STORE_ENDPOINT` | vacío | Dirección del servicio |
| `OBJECT_STORE_BUCKET` | vacío | Depósito del proyecto |
| `OBJECT_STORE_REGION` | vacío | Región, si el proveedor la exige |
| `OBJECT_STORE_CREDENTIALS_FILE` | `keys/object-store.env` | **Ruta** al par de llaves |

### Publicación del paquete

| Variable | Por defecto | Para qué |
|---|---|---|
| `PACKAGE_INDEX_URL` | `https://test.pypi.org/legacy/` | Índice de destino |
| `PACKAGE_INDEX_TOKEN_FILE` | `keys/testpypi-api.key` | **Ruta** a la credencial de publicación |

### Modelos de terceros

| Variable | Por defecto | Para qué |
|---|---|---|
| `HF_TOKEN_FILE` | `keys/huggingface.key` | **Ruta** al token, solo si se usa un modelo de acceso restringido |

Hoy no hace falta: el camino productivo no descarga ningún modelo externo.

## Credenciales

Ninguna es obligatoria. Lo que falte hace que esa parte del sistema use su
alternativa local en vez de fallar.

```bash
make keys-status   # dice qué falta, sin crear ni imprimir nada
make keys-init     # prepara la carpeta y materializa lo que haya en el entorno
```

Qué archivo va en `keys/`, cómo se obtiene cada uno y con qué permisos mínimos:
[keys/README.md](../keys/README.md).

En integración continua no hay archivos sino secretos del repositorio, y el
script los materializa antes de ejecutar cualquier etapa, de modo que el código
tenga una sola ruta de lectura sin importar el entorno:

```
secretos del repositorio  ->  scripts/02_keys_init.sh  ->  keys/  ->  código
```

## Uso desde el código

```python
from gasolina_gt.config import env, env_int, read_secret, secret_path

modo = env("APP_ENV", "local")           # variable no sensible
puerto = env_int("API_PORT", 19010)      # variable numérica
token = read_secret("HF_TOKEN_FILE")     # contenido de la credencial
ruta = secret_path("GDRIVE_CREDENTIALS_FILE")  # el archivo, sin leerlo
```

`read_secret` y `secret_path` devuelven `None` cuando la credencial no está.
Esa ausencia es un estado válido del sistema, no un error.
