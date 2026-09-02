# Credenciales del caso de estudio

Esta carpeta guarda las credenciales reales. **Nada de lo que hay aquí se
versiona**, salvo este documento y el marcador de carpeta: las exclusiones
cubren `keys/*` completo.

Se excluye la carpeta entera y no un patrón de nombre, porque ignorar por
nombre falla en cuanto alguien guarda el archivo tal como lo descargó del
proveedor.

## Por qué existe esta carpeta

La configuración del proyecto se reparte en tres niveles y cada valor cae en
exactamente uno:

| Nivel | Dónde | Qué |
|---|---|---|
| 1 | `config/config.yaml` | Parámetros de negocio y de modelo |
| 2 | `.env` | Lo que cambia por máquina o entorno, nunca sensible |
| 3 | `keys/` | Credenciales reales, en archivos |

De ahí la regla que hace útil esta carpeta: **`.env` nunca contiene el valor de
una credencial, solo la ruta al archivo que la guarda**. Las variables
sensibles terminan en `_FILE` y apuntan aquí dentro. Así una credencial no
aparece en un volcado de entorno, ni en un log de arranque, ni en una captura
de pantalla de la terminal.

## Archivos esperados

Ninguno es obligatorio. Si falta uno, la parte del sistema que lo necesita cae
a su alternativa local en vez de fallar; así la integración continua sigue
funcionando en ramas sin acceso a credenciales.

### `google-drive-service-account.json`

Cuenta de servicio para leer la carpeta compartida de fotografías.

- Cómo se obtiene: en la consola de Google Cloud, crear un proyecto, habilitar
  la API de Drive, crear una cuenta de servicio y generar una clave en formato
  JSON.
- Permiso mínimo: solo lectura sobre la carpeta compartida. La cuenta de
  servicio se agrega como lectora de esa carpeta concreta, nunca con acceso a
  la unidad entera.
- Variable que lo referencia: `GDRIVE_CREDENTIALS_FILE`.

### `object-store.env`

Par de llaves del almacenamiento de objetos, para cuando se use servidor
propio.

- Cómo se obtiene: en el panel del proveedor, crear una llave de acceso
  limitada al depósito del proyecto.
- Permiso mínimo: lectura y escritura sobre un único depósito.
- Variable que lo referencia: `OBJECT_STORE_CREDENTIALS_FILE`.

### `testpypi-api.key`

Credencial para publicar la distribución en el índice de pruebas.

- Cómo se obtiene: en la configuración de la cuenta de TestPyPI, crear una
  credencial de interfaz de programación.
- Permiso mínimo: limitado a este proyecto una vez publicada la primera
  versión. La primera publicación exige alcance de cuenta completa, así que
  conviene reemplazarla por una acotada en cuanto el proyecto exista.
- Variable que lo referencia: `PACKAGE_INDEX_TOKEN_FILE`.

### `huggingface.key`

Solo si se llega a usar un modelo de acceso restringido. Hoy no hace falta.

- Variable que lo referencia: `HF_TOKEN_FILE`.

## Cómo se llenan

En una máquina local:

```bash
make keys-status   # dice qué falta, sin crear nada
```

Después se colocan los archivos a mano con los nombres de arriba.

En integración continua no hay archivos, hay secretos del repositorio. El
script de arranque los materializa en esta carpeta antes de ejecutar cualquier
etapa, de modo que el código tenga una sola ruta de lectura sin importar el
entorno:

```bash
Secretos del repositorio  ->  scripts/02_keys_init.sh  ->  keys/  ->  código
```

## Si una credencial se expone

Revocarla en el proveedor antes que ninguna otra cosa, generar una nueva y
actualizar el secreto del repositorio. Quitar el archivo del disco no basta:
mientras la credencial siga siendo válida en el proveedor, sigue sirviendo a
quien la haya visto.
