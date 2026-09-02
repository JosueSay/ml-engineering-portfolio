# Conectar la fuente de fotografías

Cómo hacer que el pipeline traiga las imágenes. Parte de la documentación; el
índice está en [README.md](README.md).

## Elegir la vía

Hay tres, y la diferencia no es técnica sino sobre **quién puede ver esas
fotografías** y **cuánto trabajo cuesta mantener la lista**.

| | Manifiesto | Drive por enlace | Drive privado |
|---|---|---|---|
| `IMAGE_SOURCE` | `manifest` | `gdrive-public` | `gdrive` |
| Configuración | Ninguna | Clave de API | Cuenta de servicio |
| La carpeta queda | Como esté | Accesible por enlace | Privada |
| Descubre archivos nuevos | No | Sí | Sí |
| Dependencias nuevas | Ninguna | Ninguna | Cliente de Google |

Una distinción que aclara las tres: **descargar un archivo por su dirección
nunca ha necesitado autenticación; lo que sí la necesita es preguntarle a una
carpeta qué contiene.** El manifiesto evita esa pregunta leyendo una lista ya
hecha; las otras dos la hacen, y por eso piden credencial.

**Cuál usar.** Si el conjunto está cerrado y alguien mantiene la lista, el
manifiesto es lo más simple y no tiene ningún inconveniente. Si la carpeta
crece y ya es pública, la vía por enlace. Si el material no debería ser
accesible por enlace —y las fotografías de calle sin tratar suelen entrar en ese
caso— la vía privada, que cuesta unos pasos más.

Sobre lo último conviene ser explícito: **las fotografías originales no están
tratadas**. El pipeline difumina las caras al procesarlas, pero lo que hay en el
origen es el archivo tal como salió de la cámara, con lo que hubiera de fondo.
Un enlace se propaga sin que se sepa quién lo tiene.

## Vía 1: manifiesto

La más simple. Una lista de direcciones, en un archivo o publicada en una
dirección.

```
# data/manifest.txt: una direccion por linea
https://ejemplo.org/fotos/IMG_0001.HEIC
https://drive.google.com/file/d/1AbCdEf.../view?usp=sharing
```

Los enlaces de Drive se pueden pegar tal cual: el enlace que ofrece Drive al
compartir apunta a una página, no al archivo, y se traduce solo a su dirección
de descarga.

Con esa traducción se pierde el nombre del archivo, así que para enlaces de
Drive conviene el formato con nombres:

```json
[
  {"url": "https://drive.google.com/file/d/1AbC.../view", "name": "IMG_8271.HEIC"},
  {"url": "https://drive.google.com/file/d/2DeF.../view", "name": "IMG_8286.HEIC"}
]
```

En `.env`:

```
IMAGE_SOURCE=manifest
IMAGE_MANIFEST=data/manifest.json
```

Su límite es también su virtud: **no descubre nada por su cuenta**. Si aparecen
fotografías nuevas y nadie actualiza la lista, la ingesta no las verá. Para una
carpeta que crece sola, conviene una de las otras dos.

## Vía 2: Drive por enlace

Recorre la carpeta, así que sí descubre lo que se añada. Necesita una clave de
API, que se crea en un paso.

1. En la consola de Google Cloud, crear un proyecto.
2. Habilitar **Google Drive API**. Sin esto la clave se crea pero no sirve, y el
   error que da luego no es evidente.
3. En **Credenciales**, crear una **clave de API**.
4. Restringirla a la Drive API. Una clave sin restringir sirve para cualquier
   interfaz del proyecto, y eso amplía el daño si se filtra.
5. Compartir la carpeta como *cualquiera con el enlace, lector*.

```bash
echo "<la clave>" > case-studies/cs1/keys/gdrive-api.key
chmod 600 case-studies/cs1/keys/gdrive-api.key
```

En `.env`:

```
IMAGE_SOURCE=gdrive-public
GDRIVE_FOLDER_ID=<el identificador de la carpeta>
GDRIVE_API_KEY_FILE=keys/gdrive-api.key
```

## Vía 3: Drive privado

La carpeta no se comparte por enlace, sino con una identidad concreta. Más
pasos, y queda constancia de quién tiene acceso.

1. Proyecto en Google Cloud y **Google Drive API** habilitada.
2. En **IAM y administración → Cuentas de servicio**, crear una. No necesita
   ningún rol del proyecto: los permisos que importan son los de la carpeta.
3. Copiar su correo, con esta forma:

   ```
   nombre@proyecto.iam.gserviceaccount.com
   ```

4. En sus **claves**, crear una de tipo **JSON** y descargarla.
5. Compartir la carpeta con ese correo, como **Lector**.

Ese archivo es una credencial completa: no se envía por correo ni por
mensajería, y no entra al repositorio.

```bash
cp ~/Descargas/<archivo>.json case-studies/cs1/keys/google-drive-service-account.json
chmod 600 case-studies/cs1/keys/google-drive-service-account.json
.venv/bin/python -m pip install -e '.[gdrive]'
```

En `.env`:

```
IMAGE_SOURCE=gdrive
GDRIVE_FOLDER_ID=<el identificador de la carpeta>
GDRIVE_CREDENTIALS_FILE=keys/google-drive-service-account.json
```

## El identificador de la carpeta

Está en la dirección, después de `/folders/`:

```
https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J
                                       └── el identificador ──┘
```

## Cómo organizar la carpeta

**Las subcarpetas funcionan.** El recorrido entra en ellas, así que se puede
organizar por año, por mes o por estación. Con un histórico de varios años es lo
natural.

**Los nombres pueden repetirse.** La identidad de una fotografía es la huella de
su contenido, no su nombre: dos archivos llamados igual con distinto contenido
son dos fotografías, y el mismo archivo con dos nombres es una sola.

Lo que sí conviene: no renombrar después de una ingesta. No rompe nada, pero
complica seguir el rastro a ojo.

## Comprobar

```bash
make keys-status
make ingest LIMIT=3
```

Con `LIMIT` se traen solo tres. Es lo sensato la primera vez: si algo está mal
configurado se descubre en segundos, y no después de bajar el histórico entero.

```json
{
  "source": "Google Drive por enlace, carpeta 1A2B3C...",
  "available": 3,
  "downloaded": 3,
  "skipped_cached": 0,
  "failed": 0,
  "images_on_disk": 8
}
```

Al repetirlo, `downloaded` en cero: lo ya traído no se vuelve a descargar.

Si sale `carpeta local` en vez de la fuente elegida, la remota no estaba
disponible y cayó a la alternativa. El registro dice qué falta.

Luego, la ingesta completa y el pipeline:

```bash
make ingest
make pipeline
```

## En la integración continua

```bash
# Via por enlace
gh secret set GDRIVE_API_KEY --body "<la clave>"
gh variable set GDRIVE_FOLDER_ID --body "<el identificador>"

# Via privada
base64 -w0 case-studies/cs1/keys/google-drive-service-account.json | \
  gh secret set GDRIVE_SERVICE_ACCOUNT_JSON
gh variable set GDRIVE_FOLDER_ID --body "<el identificador>"
```

El identificador va como **variable** y no como secreto: no da acceso por sí
solo, y verlo en los registros ayuda a diagnosticar.

## Qué pasa si algo falla

| Síntoma | Causa probable |
|---|---|
| Cae a `carpeta local` sin más | Falta la credencial o el identificador. El registro dice cuál |
| `available: 0` con la carpeta llena | La carpeta no está compartida como toca, o el identificador es de otra |
| Error de API deshabilitada | Falta habilitar Drive API en el proyecto |
| «La respuesta es una página web» | Enlace de Drive a un archivo grande, que pide confirmación. Usar una de las vías con API |
| `available` menor de lo esperado | Solo se listan los formatos que el pipeline lee |
| Una descarga falla | No detiene el lote: sale en `failed` y se reintenta en la siguiente corrida |

## Si más adelante se prefiere otro almacenamiento

El pipeline habla con un contrato, no con Drive. Cambiar a un depósito de
objetos es escribir otra implementación de ese contrato y cambiar
`IMAGE_SOURCE`. Ni el extractor, ni las capas de datos, ni el modelo se enteran.

El contrato está descrito en [04_structure.md](04_structure.md) y el modelo de
datos que alimenta, en [06_data_model.md](06_data_model.md).
