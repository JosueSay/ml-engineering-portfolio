# Tareas que requieren una persona

Lo que no se puede automatizar porque necesita una cuenta, una credencial o una
decisión. Parte de la documentación; el índice está en [README.md](README.md).

Cada sección dice qué desbloquea, para poder hacer solo lo que haga falta ahora
y dejar el resto para cuando toque.

## 1. Cerrar la fase A

Estado: doce commits confirmados y sin empujar, más la refactorización de
nomenclatura pendiente de confirmar.

### Confirmar la refactorización

El comando completo, con su mensaje, está en
[fase-a-commits.md](fase-a-commits.md), sección 14. Antes conviene revisar que
el árbol esté como se espera:

```bash
cd case-studies/cs1 && make gates && cd ../..
git status --short
```

### Mover la etiqueta

La etiqueta se creó apuntando al duodécimo commit, antes de la refactorización.
Para que marque el final real de la fase:

```bash
git tag -f -a cs1-v0.1.0 -m "CS1: higiene, estructura y estandares"
```

### Empujar

```bash
git push origin fuel-case-study
git push --force origin cs1-v0.1.0
```

El `--force` es solo para la etiqueta, que se movió. La rama va con un empujón
normal: no se reescribió nada de lo ya publicado.

### Comprobar la integración continua

```bash
gh run watch
```

Se espera que **las etapas de datos aparezcan omitidas**, con el motivo escrito
en el resumen de la corrida: no hay fotografías en el repositorio ni credencial
de almacenamiento remoto. La calidad de código y la imagen de contenedor sí
deben verificarse.

Si en vez de omitidas aparecen falladas, el trabajo que decide la fuente de
datos no está haciendo su trabajo y hay que revisarlo.

## 2. Mejorar la extracción en local

Desbloquea: que la lectura de dígitos tenga una segunda opinión.

Hoy ninguna de las cinco fotografías piloto produce una lectura válida, y el
motor alterno de reconocimiento de texto no está instalado en esta máquina, así
que solo trabaja el lector de siete segmentos.

```bash
sudo apt-get install tesseract-ocr
cd case-studies/cs1 && make verify
```

No arregla el problema de fondo —que se aborda en la fase C con la detección
del visor— pero permite comparar los dos motores sobre las mismas fotografías y
saber si el fallo está en la lectura o en el recorte.

## 3. Google Drive

Desbloquea: la fase C completa, y que la integración continua tenga datos.

### Crear la cuenta de servicio

1. En la consola de Google Cloud, crear un proyecto.
2. Habilitar la API de Google Drive.
3. Crear una cuenta de servicio.
4. Generar una clave en formato JSON y descargarla.

### Preparar la carpeta

1. Crear una carpeta en Drive y subir las fotografías disponibles.
2. Compartirla con el correo de la cuenta de servicio, **como lectora**. Es el
   permiso mínimo: el pipeline solo lee.
3. Copiar el identificador de la carpeta, que es la parte final de su
   dirección web.

### Conectarla en local

```bash
cp ~/Descargas/<archivo-descargado>.json \
   case-studies/cs1/keys/google-drive-service-account.json
chmod 600 case-studies/cs1/keys/google-drive-service-account.json
```

Y en `.env`, rellenar el identificador de carpeta:

```
GDRIVE_FOLDER_ID=<el identificador copiado>
IMAGE_SOURCE=gdrive
```

Comprobar:

```bash
cd case-studies/cs1 && make keys-status
```

### Conectarla en la integración continua

Allí no hay archivos, hay secretos. El contenido va en base64 para que un JSON
de varias líneas sobreviva al paso por el entorno:

```bash
base64 -w0 case-studies/cs1/keys/google-drive-service-account.json | \
  gh secret set GDRIVE_SERVICE_ACCOUNT_JSON
```

A partir de ahí el trabajo que decide la fuente de datos encontrará la
credencial y las etapas dejarán de omitirse.

## 4. TestPyPI

Desbloquea: la fase D, la publicación del paquete.

1. Crear una cuenta en TestPyPI y verificar el correo.
2. Guardar los códigos de recuperación y activar la doble autenticación.
3. En la configuración de la cuenta, crear una credencial de interfaz de
   programación. La primera publicación exige alcance de cuenta completa;
   conviene reemplazarla por una acotada al proyecto en cuanto exista.

En local:

```bash
echo "<la credencial>" > case-studies/cs1/keys/testpypi-api.key
chmod 600 case-studies/cs1/keys/testpypi-api.key
```

En la integración continua:

```bash
gh secret set TESTPYPI_API_TOKEN < case-studies/cs1/keys/testpypi-api.key
```

### Entorno de publicación

Para que la publicación exija una aprobación manual en vez de dispararse sola:

1. En la configuración del repositorio, sección de entornos, crear uno llamado
   `testpypi`.
2. Activar la revisión requerida y añadirse como revisor.

Hoy el repositorio solo tiene el entorno de páginas.

## 5. Almacenamiento de objetos

Desbloquea: la alternativa a Drive, si se prefiere servidor propio.

Solo si se decide usarlo. Con un servicio compatible levantado, las llaves van
a `keys/object-store.env` y su dirección y depósito a `.env`. El secreto
correspondiente es `OBJECT_STORE_CREDENTIALS`.

## Qué hace falta para cada fase

| Fase | Qué necesita de una persona |
|---|---|
| B — Persistencia y linaje | Nada. Docker solo si se quiere levantar el contenedor de base de datos |
| C — Ingesta y análisis | Google Drive, secciones 2 y 3 |
| D — Publicación | TestPyPI, sección 4 |
| E — Cierre | Nada |

La fase B se puede arrancar ya.

## Comprobación rápida

```bash
cd case-studies/cs1
make verify        # intérprete, dependencias y estructura
make keys-status   # que credenciales faltan
make gates         # linter, pruebas y revision de secretos
gh secret list     # que secretos ve el repositorio
```
