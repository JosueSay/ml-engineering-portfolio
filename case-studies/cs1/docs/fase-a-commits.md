# Commits de la fase A

Propuesta de división. Sigue Conventional Commits en español, que es el estilo
del historial existente.

El orden importa: cada commit apoya sobre el anterior. Las exclusiones van
antes de crear cualquier archivo sensible, y las fotografías salen antes de
tocar lo que dependía de ellas.

Una advertencia: algunos archivos acumulan cambios de varios tipos, porque se
tocaron en varios pasos del trabajo. En esos casos el archivo va al commit de
su cambio dominante en vez de partirlo con `git add -p`.

Ejecutar todo desde la raíz del repositorio.

## 0. Vaciar el índice

Los movimientos de archivos se hicieron con `git mv` y `git rm --cached`, así
que ya hay entradas preparadas. Si no se vacía primero, el primer `git commit`
se llevaría todas ellas por delante.

```bash
git reset
```

Vacía el índice sin tocar el árbol de trabajo: no se pierde ningún cambio. Git
vuelve a detectar los renombrados al confirmar.

## 1. Licencia

```bash
git add LICENSE
git commit -m "chore: agregar licencia MIT"
```

## 2. Exclusiones

Va antes que nada porque es preventivo: sin esto, el primer archivo de `keys/`
o el primer `.env` quedarían rastreados.

```bash
git add .gitignore case-studies/cs1/.gitignore case-studies/cs1/.dockerignore
git commit -m "chore(cs1): excluir credenciales, datos y modelos del control de versiones

La carpeta de credenciales se excluye entera y no por patron de nombre:
ignorar por nombre falla en cuanto alguien guarda el archivo tal como lo
descargo del proveedor."
```

## 3. Las fotografías salen del repositorio

Las fotografías se sacan del índice con `git rm --cached` porque su carpeta ya
no existe en el árbol, y un `git add` sobre una ruta que no existe falla.

```bash
git rm -r --cached --quiet case-studies/cs1/datos
git add -A case-studies/cs1/data case-studies/cs1/models \
           case-studies/cs1/config/panelCalibration.json
git commit -m "refactor(cs1)!: sacar las fotografias del repositorio y unificar la estructura de datos

Habia diez imagenes en disco: cinco versionadas en datos/ y cinco duplicadas
sin versionar en data/raw/. Mismo contenido, dos carpetas, mismo proposito.

Queda una sola estructura: raw para los originales, interim para los recortes y
processed para las capas. Los almacenes de modelos se separan en vendor y
trained porque tienen ciclos de vida opuestos.

La calibracion de paneles no era un dato sino configuracion, asi que pasa a
config/.

Las imagenes se dejan de rastrear pero no se reescribe el historial: se aceptan
esos 8 MB en confirmaciones anteriores a cambio de no obligar al equipo a
rehacer su copia local.

BREAKING CHANGE: data/raw esta vacia en un clon nuevo. Las fotografias se
obtienen del almacenamiento externo."
```

## 4. El experimento se aísla

```bash
git add -A case-studies/cs1/experiments case-studies/cs1/config.yml \
           case-studies/cs1/core case-studies/cs1/download_models.py \
           case-studies/cs1/requirements.txt
git commit -m "refactor(cs1): aislar el experimento de vision fuera del camino productivo

El modelo de vision y lenguaje no lo usa el pipeline: la extraccion es un
clasificador de siete segmentos con vision clasica. Mantenerlo en la raiz
significaba 1.5 GB de descarga y ejecucion de codigo de terceros dentro de un
proyecto que debe correr en un servidor modesto.

Se conserva con el motivo del descarte y con la leccion que si aporto: fijar la
revision exacta de un modelo publicado, nunca la rama.

El requirements.txt de la raiz declaraba torch y transformers, que son
dependencias de este experimento y no del paquete. Viaja con el."
```

## 5. Entorno y credenciales

```bash
git add case-studies/cs1/.env.example case-studies/cs1/keys \
        case-studies/cs1/src/gasolina_gt/config.py
git commit -m "feat(cs1): gestionar entorno y credenciales en tres niveles

Los parametros de negocio van a config/config.yaml, lo que cambia por maquina
va a .env, y las credenciales a keys/.

De ahi la regla que sostiene el tercer nivel: .env nunca contiene el valor de
una credencial, solo la ruta al archivo que la guarda. Las variables sensibles
terminan en _FILE y se leen con read_secret. Asi una credencial no aparece en
un volcado de entorno ni en un registro de arranque.

La raiz del proyecto pasa a buscarse hacia arriba hasta encontrar la
configuracion, en vez de contar niveles fijos: al instalar el paquete de forma
no editable ese conteo dejaba de valer."
```

## 6. Orquestación por scripts

```bash
git add -A case-studies/cs1/scripts case-studies/cs1/Makefile
git commit -m "feat(cs1): orquestar mediante scripts con el Makefile como atajo

La logica pasa a scripts/ y el Makefile queda como una linea por objetivo. El
mismo comando corre sin make, y la integracion continua deja de depender de el.

Se declara solo lo que existe: un objetivo que apunta a un script inexistente
es una promesa rota.

00_verify_environment.sh existe porque el fallo mas comun no es un error de
codigo sino un interprete por debajo del minimo, que revienta al importar con
un mensaje que no dice nada sobre la causa."
```

## 7. Valores quemados y manifiesto de modelos

```bash
git add case-studies/cs1/config/config.yaml \
        case-studies/cs1/src/gasolina_gt/data/pipeline.py \
        case-studies/cs1/src/gasolina_gt/data/features.py \
        case-studies/cs1/src/gasolina_gt/evaluation/metrics.py \
        case-studies/cs1/src/gasolina_gt/modeling/training.py \
        case-studies/cs1/src/gasolina_gt/extraction/calibration.py \
        case-studies/cs1/tests/integration/test_training_evaluation.py
git commit -m "refactor(cs1): llevar valores quemados a configuracion y registrar los modelos entrenados

Los nombres de los archivos de salida estaban repetidos en el modulo que
escribe y en el que lee. Dos literales que tienen que coincidir acaban por no
hacerlo, asi que pasan a config. Lo mismo con la ruta del artefacto de modelo,
la ventana de historia sintetica y los umbrales de entrenamiento.

Cada entrenamiento queda anotado en models/manifest.json con la huella del
conjunto que lo produjo, sus hiperparametros y la version del paquete. El
manifiesto es texto y si se versiona; los pesos no.

La prueba de entrenamiento construia la configuracion a mano y se rompia ante
cualquier clave nueva. Ahora parte de la real y solo ajusta lo que necesita."
```

## 8. Imagen y composición

```bash
git add case-studies/cs1/Dockerfile case-studies/cs1/compose.yaml
git commit -m "fix(cs1): reparar la imagen y la composicion tras salir las fotografias

El Dockerfile copiaba una carpeta que dejo de existir, asi que la imagen no
construia. Los datos y los modelos pasan a entrar por volumen: horneados en la
imagen obligarian a reconstruir por cada foto nueva.

Se instala el motor alterno de lectura, que el codigo daba por hecho dentro del
contenedor sin que nada lo instalara, y las dependencias de sistema de la
biblioteca de vision, que faltaban.

Los servicios se renombran con prefijo de proyecto para que no choquen con
contenedores de otras aplicaciones, y los puertos salen del rango reservado."
```

## 9. Integración continua

```bash
git add .github/workflows/cs1-ml-pipeline.yml
git commit -m "ci(cs1): llamar a los scripts y omitir las etapas sin fuente de datos

Al salir las fotografias del repositorio, la cadena se quedaba sin datos y
fallaba en la primera etapa. No se disimula saltando la etapa en silencio: un
pipeline en verde que no proceso nada es peor que uno que falla.

Un trabajo dedicado decide si hay fuente disponible y es el unico sitio donde
se toma esa decision. Cuando no la hay, las etapas de datos se omiten y el
motivo queda escrito en el resumen de la corrida.

El trabajo de la imagen pasa a colgar de la calidad de codigo: la prueba de
humo solo comprueba que el servicio levanta, asi que no necesita ni datos ni
modelo entrenado y debe verificarse en toda corrida."
```

## 10. Linter y hallazgos de seguridad

```bash
git add case-studies/cs1/pyproject.toml \
        case-studies/cs1/src/gasolina_gt/augmentation/image_augment.py \
        case-studies/cs1/src/gasolina_gt/extraction/digit_ocr.py \
        case-studies/cs1/src/gasolina_gt/extraction/heic_loader.py
git commit -m "style(cs1): exigir seguridad, nomenclatura y documentacion en el linter

Faltaban las comprobaciones que detectan credenciales embebidas y usos
inseguros de la ejecucion de procesos y de la deserializacion, que es
justamente lo que el proyecto usa.

Los hallazgos que reporto:

- El motor externo de lectura se invocaba por nombre suelto, confiando en el
  PATH del momento de la llamada. Ahora se resuelve su ruta absoluta una vez.
- La lectura de la fecha de captura silenciaba cualquier excepcion sin dejar
  rastro, ocultando por que una fotografia quedaba sin fecha, que es el dato
  que ancla toda la serie temporal."
```

## 11. Documentación

```bash
git add -A case-studies/cs1/src case-studies/cs1/docs \
           case-studies/cs1/README.md case-studies/cs1/experiments/README.md
git commit -m "docs(cs1): documentar el codigo y el proyecto

Cuarenta y cuatro modulos, clases y funciones sin documentacion. Los docstrings
explican el porque y no el que, y el linter ahora exige que existan.

Se agrega documentacion de puesta en marcha, referencia de variables de
entorno, referencia de comandos y descripcion de la estructura. El README
describia una estructura que ya no existia."
```

## 12. Dependencias del taller

```bash
git add -A workshop/actividad_3
git commit -m "chore(workshop): unificar la declaracion de dependencias en pyproject

El requirements.txt de la actividad 3 solo repetia lo que ya declaraba su
pyproject. La regla queda escrita: pyproject es la fuente unica de las
dependencias de cada paquete instalable, y un requirements.txt solo existe
donde hay un entorno que no es un paquete."
```

## 13. Auditoría del sitio

Es otro tema, no forma parte del caso de estudio.

```bash
git add docs/
git commit -m "docs: auditar el sitio del portafolio

Tres problemas medidos en produccion con sus culpables localizados: el hueco
del menu contraido, el parpadeo en cada navegacion por una cascada de tres
saltos de red antes del primer pintado, y el salto del contenido al llegar las
traducciones.

Incluye el inventario de lo que existe en el repositorio y no esta publicado en
el sitio."
```

## Antes de empujar

```bash
cd case-studies/cs1 && make gates && cd ../..
git log --oneline -13
git status --short
```

`git status` debe quedar limpio salvo por lo que sigue ignorado: `.env`,
`.venv/`, `data/` con las fotografías y `keys/`.

## Etiqueta

Si se quiere marcar la entrega, según el estándar de versionado:

```bash
git tag -a cs1-v0.1.0 -m "CS1: higiene, estructura y estandares"
```
