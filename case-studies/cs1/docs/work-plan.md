# Plan de trabajo CS1 — Precios de gasolina Guatemala

Documento de diagnóstico, decisiones y planificación del caso de estudio.
Recoge el inventario de lo que existe, las reglas de trabajo acordadas, las
decisiones ya tomadas y el backlog pendiente.

- Fecha de la última revisión: 1 de septiembre de 2026
- Rama: `fuel-case-study`, se mantiene tal cual
- Estado: fase A completa. Los primeros 12 commits están etiquetados como
  `cs1-v0.1.0`; la refactorización de nomenclatura va aparte

## 1. El caso en una página

Fotos de tótems de gasolinera (mayoría Shell) como fuente cruda. De cada foto
hay que sacar cuatro precios por posición fija del panel (diésel, regular,
súper, V-Power), llevarlos a una base histórica trazable, y sobre esa base
predecir el precio a 1, 2 y 4 semanas con una señal de tendencia.

Dos mitades que no se mezclan:

- Extracción: imagen a pares (tipo de combustible, precio).
- Estimación: serie de precios a pronóstico. Es regresión, no visión.

Lo que se evalúa no es la sofisticación del extractor, sino el diseño del
flujo: que ingiera, transforme, persista y deje rastro cada vez que llega una
foto nueva.

## 2. Cómo se trabaja en este proyecto

Estas reglas son el estándar del caso de estudio. Están escritas aquí para que
no vuelvan a incumplirse por descuido, y para que cualquiera que entre al
proyecto sepa qué se espera sin tener que preguntarlo.

### 2.1 Datos e imágenes

- **Ninguna imagen entra al control de versiones.** Ni de muestra, ni de
  prueba, ni "solo estas cinco". El repositorio guarda código y documentación;
  los datos viven en el almacenamiento externo y se descargan.
- Las imágenes originales no se editan nunca. Cualquier transformación produce
  un archivo nuevo en otra carpeta.
- Toda carpeta de datos se declara en las exclusiones de control de versiones,
  con un marcador dentro para que la estructura exista sin que el contenido
  viaje.
- Un dato que no se puede rastrear hasta su origen no sirve. Cada valor que
  llega al conjunto de modelado debe poder seguirse hasta la foto y el recorte
  del que salió.

### 2.2 Configuración y credenciales

Tres niveles, y cada valor cae en exactamente uno:

| Nivel | Ubicación | Contenido | Versionado |
|---|---|---|---|
| 1 | `config/config.yaml` | Parámetros de negocio y de modelo | Sí |
| 2 | `.env` | Lo que cambia por máquina o entorno, nunca sensible | No, solo `.env.example` |
| 3 | `keys/` | Credenciales reales, en archivos | No, solo su documentación |

Regla de decisión, en este orden:

1. ¿Es igual en todas las máquinas y define cómo se comporta el sistema? Va a
   `config/config.yaml`.
2. ¿Cambia por máquina o entorno, pero se puede publicar sin riesgo? Va a
   `.env`.
3. ¿Da acceso a algo? Va a `keys/`, como archivo.

De ahí se sigue lo más importante: **`.env` nunca contiene el valor de una
credencial, solo la ruta al archivo que la guarda**. Las variables sensibles
terminan en `_FILE` apuntando dentro de `keys/`. Así una credencial no aparece
en un volcado de entorno, ni en un log de arranque, ni en una captura de
pantalla de la terminal.

### 2.3 Código

- Nada de valores quemados. Un número que decide comportamiento va a
  `config/config.yaml`; una ruta va a `.env` o se deriva de la raíz del
  proyecto.
- Nombres de archivos, carpetas e identificadores en inglés. Comentarios y
  documentación en español.
- Módulos de Python en minúsculas con guion bajo, carpetas en minúsculas con
  guion medio, clases en mayúscula inicial, constantes en mayúsculas.
- Tipado obligatorio en parámetros y retornos.
- Cada módulo con su documentación interna explicando el porqué, no el qué.
- El linter incluye la comprobación de seguridad y la de nomenclatura, y se
  ejecuta antes de cada confirmación de cambios.
- Ninguna función crítica sin prueba.
- Todo módulo, clase y función pública lleva documentación que explica el
  porqué, no el qué. El linter lo exige.
- `pyproject.toml` es la fuente única de las dependencias de cada paquete
  instalable. Un `requirements.txt` solo existe donde hay un entorno que no
  es un paquete, como los experimentos.

### 2.4 Ejecución

- La lógica vive en `scripts/`; el `Makefile` es solo el atajo. El mismo
  comando debe poder correrse sin `make`, y la integración continua llama a los
  scripts directamente.
- Solo se declara en el `Makefile` lo que existe. Un objetivo que apunta a un
  script inexistente es una promesa rota; lo pendiente vive en este documento.
- Todo lo que se ejecute debe funcionar igual en Windows, Linux, macOS y en un
  servidor modesto sin tarjeta gráfica.
- Ninguna etapa cara se repite sin motivo. Si el resultado dependía solo del
  código y de la configuración, y ninguno de los dos ha cambiado, se reutiliza
  lo ya calculado. La comprobación va contra las tres cosas a la vez —dato,
  versión y configuración—, porque basta que cambie un umbral para que el
  resultado deje de ser válido.

### 2.5 Puertos

Los puertos se parametrizan siempre, nunca se queman, y salen de un rango
reservado para este proyecto para no chocar con otras aplicaciones de la
máquina.

**Rango reservado: 19000 a 19099.** Está por debajo del rango de puertos
efímeros que el sistema asigna por su cuenta, que en Linux arranca en 32768, y
fuera de los puertos habituales de desarrollo: 3000, 5000, 5432, 8000, 8080 y
27017.

| Puerto | Servicio | Variable |
|---|---|---|
| 19010 | API de pronóstico | `API_PORT` |
| 19020 | Base de datos, si algún día se usa un motor servidor | `DB_PORT` |
| 19030 | Explorador de la base de datos | `DB_BROWSER_PORT` |
| 19040 | Almacenamiento de objetos, interfaz de programación | `OBJECT_STORE_PORT` |
| 19041 | Almacenamiento de objetos, consola web | `OBJECT_STORE_CONSOLE_PORT` |
| 19050-19099 | Libres para futuros servicios | — |

Todos con valor por defecto en `.env.example` y sobreescribibles por entorno.

## 3. Inventario: qué existe hoy

### 3.1 Extracción

| Componente | Archivo | Qué hace |
|---|---|---|
| Carga de imágenes | `extraction/heic_loader.py` | Lee HEIC y formatos comunes, extrae la fecha de captura |
| Privacidad | `extraction/privacy.py` | Difumina caras antes de procesar |
| Calibración | `extraction/calibration.py` | Ubica el panel de cada combustible por fracciones del encuadre |
| Preprocesado | `extraction/preprocess.py` | Localiza el visor y binariza |
| Lectura de dígitos | `extraction/digit_ocr.py` | Clasificador de siete segmentos por plantillas, más un motor alterno |
| Orquestador | `extraction/extractor.py` | Recorre el directorio, valida y escribe Bronze |

La lectura es determinista, sin tarjeta gráfica y sin modelos pesados. Compara
la forma completa del dígito contra diez plantillas de siete segmentos y se
queda con el mejor solapamiento. Cumple la restricción del servidor modesto y
la de no usar un modelo de lenguaje.

Validación ya implementada: descarta si no se pudo leer, si la confianza queda
bajo $0.55$, o si el precio cae fuera del rango $[10, 80]$ GTQ. Ante la duda
escribe nulo en vez de inventar.

### 3.2 Capas de datos

Arquitectura por capas en `data/pipeline.py`:

- Bronze: un documento por corrida con la lectura tal cual salió de la imagen,
  incluyendo las inválidas y su motivo de rechazo.
- Silver: tabla con solo las lecturas válidas, ya con la fecha real de captura.
- Gold: conjunto con variables de modelado, como rezagos, medias móviles y
  calendario.

### 3.3 Modelado, evaluación y servicio

- `modeling/training.py`: búsqueda aleatoria de 25 iteraciones sobre seis
  hiperparámetros, validación temporal de tres particiones, ventana de prueba
  de seis semanas, y una referencia de persistencia para comparar.
- `evaluation/metrics.py` y la compuerta de calidad: falla la corrida si el
  error absoluto medio supera Q1.00, si no mejora la referencia, o si la medida
  de tendencia baja de $0.55$.
- `serving/recommendation.py` y `serving/api.py`: recomendación de carga y
  servicio web.

### 3.4 Infraestructura

Imagen de contenedor multietapa, composición con cuatro servicios y tres
volúmenes, `Makefile` con detección de intérprete, y flujo de integración
continua con seis trabajos encadenados y artefactos con catorce días de
retención.

## 4. Problemas detectados

### 4.1 Las imágenes están en el repositorio, y duplicadas

Hay diez archivos en disco: cinco versionados en `datos/` y otros cinco sin
versionar en `data/raw/`. Es el mismo contenido en dos carpetas con el mismo
propósito y distinto nombre. Los versionados suman la mayor parte de los
8.1 MB que pesa el repositorio.

Incumple la primera regla de la sección 2.1 y hay que revertirlo: sacar las
imágenes del seguimiento, dejar una sola estructura de datos y recuperar las
fotos desde el almacenamiento externo.

**Decidido: solo se dejan de rastrear, no se reescribe el historial.** Los
archivos salen del seguimiento y del árbol de trabajo, pero permanecen en las
confirmaciones anteriores. Se aceptan esos 8 MB muertos a cambio de no obligar
al equipo a rehacer su copia local ni invalidar referencias ya publicadas. La
regla aplica de aquí en adelante.

### 4.2 No hay base de datos ni linaje

Todo se persiste como archivos sueltos. Bronze guarda el nombre del archivo
dentro del documento y Silver arrastra una columna con el origen. Eso es una
miga, no una cadena de custodia: hoy no se puede saber, ante una predicción
mala, si falló el modelo o la lectura.

### 4.3 No se recorta la región de interés

Se procesa la fotografía completa cuando los precios ocupan una franja concreta
del tótem, en la parte baja. Se gasta cómputo en píxeles que no aportan, y no
queda registro visual de qué porción se leyó, que es justo lo que haría
auditable una lectura dudosa.

### 4.4 No existe la corrección aritmética

Cuando el precio no se lee, se descarta. Muchas fotos incluyen el volumen
cargado y el total pagado, y con esos dos valores se recupera el precio
unitario:

$$
p = \frac{\text{total pagado}}{\text{galones cargados}}
$$

Es preparación de datos, no un truco aparte, y la redundancia de la imagen hoy
se desperdicia.

### 4.5 No hay tratamiento de faltantes

Si la lectura falla en un panel, esa combinación de fecha y combustible queda
sin valor y la serie sale con huecos. Falta una estrategia declarada de relleno
y, sobre todo, que cada valor rellenado quede marcado como tal.

### 4.6 Falta el campo de marca

No hay dónde guardar la marca ni la estación, así que no se puede contestar si
el precio varía según la gasolinera.

### 4.7 El paquete instalado no arranca fuera de su carpeta

La raíz del proyecto se busca subiendo dos niveles desde el archivo de
configuración. Al instalar de forma no editable ese archivo queda bajo el
directorio de paquetes, la suposición se cae, y el último recurso es el
directorio de trabajo actual. Quien instale el paquete y lo ejecute desde otra
carpeta recibe un error de archivo no encontrado.

### 4.8 Dos configuraciones que no se hablan

Conviven `config.yml` en la raíz del caso, con las rutas del experimento de
visión, y `config/config.yaml`, con la parametrización del pipeline. Distinta
extensión, distinta ubicación, propósitos solapados.

### 4.9 El linter no cubre seguridad ni nomenclatura

Faltan las comprobaciones de seguridad y de nombres. Es justo lo que detectaría
una credencial embebida o un uso inseguro de la ejecución de procesos y de la
deserialización, y el proyecto usa ambas cosas.

### 4.10 Deuda de nomenclatura

Carpetas e identificadores en español, dos carpetas de datos con nombres
distintos, un módulo con mayúsculas intercaladas, y servicios de la composición
sin prefijo de proyecto.

### 4.11 Dependencias desiguales

La actividad 1 del taller solo declara su archivo de proyecto, sin lista de
requisitos, así que no queda claro qué instalar para reproducirla. El caso de
estudio y la actividad 3 sí declaran ambos.

### 4.12 La imagen de contenedor no instala el motor alterno de lectura

El código documenta que ese motor está disponible dentro del contenedor. La
imagen no instala nada por el gestor de paquetes del sistema, así que nunca se
activa allí.

### 4.13 La imagen de contenedor copia las fotos

Funciona con cinco archivos y deja de funcionar con el histórico completo: la
imagen crecería sin control y habría que reconstruirla por cada foto nueva.

### 4.14 Modelo de visión residual

El descargador baja 1.5 GB y ejecuta código remoto de terceros. El pipeline no
lo usa: la extracción es de siete segmentos con visión clásica. Mantenerlo en
el camino productivo choca con la restricción del servidor modesto.

### 4.15 La integración continua se quedó sin fuente de datos

Consecuencia directa y esperada de sacar las imágenes del control de versiones:
el trabajo de extracción se ejecuta sobre `data/raw`, que en una máquina limpia
está vacía. Hasta que exista el trabajo de ingesta de la fase C, la cadena
falla en la primera etapa.

No se disimula haciendo que la etapa se salte en silencio: un pipeline que pasa
en verde sin haber procesado nada es peor que uno que falla.

**Resuelto en la fase A.** Un trabajo dedicado decide si hay fuente de datos
—imágenes locales o credencial de almacenamiento remoto— y es el único sitio
donde se toma esa decisión; el resto la consulta. Cuando no la hay, las etapas
de datos se omiten y el motivo queda escrito en el resumen de la corrida, junto
con qué secreto hay que declarar para habilitarlas. La calidad de código y la
imagen de contenedor se verifican siempre, porque no dependen de los datos: la
prueba de humo solo comprueba que el servicio levanta y responde, así que ese
trabajo pasó a colgar de la calidad de código en vez de la evaluación.

Cuando exista el adaptador de la fase C, ese mismo trabajo descargará las
imágenes en vez de limitarse a comprobar si están.

### 4.16 La extracción lee poco, y eso es parte del problema a resolver

**El objetivo no es leer el cien por cien.** Con fotografías tomadas en la
calle, a distintas horas y desde distintos ángulos, siempre habrá lecturas que
no salgan. Lo que el caso tiene que resolver bien es lo que pasa *después*: qué
se hace con esos huecos, con qué método se rellenan y cómo queda registrado que
se rellenaron. Un pipeline que lee el ochenta por ciento y trata con rigor el
veinte restante vale más que uno que promete el cien y esconde sus fallos.

Lo medido hasta ahora, y las decisiones que salieron de ahí, quedan recogidas
en esta sección.

### 4.16.1 Estado del reconocimiento

Detectado al verificar el pipeline completo. De las cinco fotografías salen
veinte lecturas y **ninguna válida**: quince fallan en el reconocimiento de
dígitos, cuatro caen fuera del encuadre calibrado y una no llega a la confianza
mínima por poco.

Comprobado contra el código anterior a la refactorización, con el mismo
resultado exacto: no es una regresión, es el estado real del extractor.

La consecuencia práctica es que el conjunto de modelado es **cien por cien
sintético**. La compuerta de calidad ya lo detecta y pasa a modo informativo en
vez de bloquear, y la recomendación lo advierte. Pero significa que la mitad de
visión del caso todavía no funciona sobre datos reales, y que el trabajo de la
fase C sobre la calibración y la detección del visor no es una mejora opcional
sino lo que hace falta para que el caso tenga datos propios.

### 4.16.2 Qué se midió y qué se corrigió

Se montó un conjunto de referencia con los seis precios legibles anotados a
mano y los diez recortes vacíos como casos negativos, y una herramienta que
compara motores sobre los mismos datos. Sin eso, "mejorar el reconocimiento" no
era una afirmación comprobable.

Dos hallazgos y sus arreglos:

- **Los dígitos son itálicos por diseño**, como los de un reloj digital. No es
  perspectiva de la fotografía: rectificarla no cambiaba nada. Las plantillas de
  comparación eran de trazos rectos, y por eso se confundían justo los dígitos
  que más se parecen al inclinarse. Enderezar la inclinación antes de comparar
  llevó la lectura de cero dígitos correctos a cuatro de cinco en el mejor caso.
- **El separador decimal se perdía.** Se llegó a leer 4609 donde decía 40.09,
  con confianza suficiente para casi pasar. Un precio en quetzales por galón
  siempre tiene dos decimales, así que el punto se recoloca por posición cuando
  el número de dígitos es el esperado, y solo entonces.

Y una consecuencia que hubo que atajar: recolocar el punto hacía que texto
basura de cuatro dígitos se convirtiera en precios de aspecto plausible, y la
tasa de invención subió al cuarenta por ciento. Se resolvió buscando el visor
por su aspecto antes de leer: donde no hay visor, no se intenta leer.

### 4.16.3 Cuándo pasar a un modelo entrenado

Un detector entrenado sigue siendo el camino para encuadres variados, y el
Business Understanding ya lo contemplaba. El criterio de disparo: si con el
histórico completo la tasa de lecturas válidas queda por debajo del setenta por
ciento, se entrena uno para localizar el visor. Con ese conjunto habrá con qué
entrenar y con qué validar, que hoy no existe.

La inferencia de un detector pequeño corre en procesador, así que no rompe la
restricción del servidor modesto; la tarjeta gráfica solo haría falta para
entrenarlo una vez.

### 4.17 El conjunto sintético no es reproducible

La serie generada se construye hasta la fecha actual, así que dos corridas en
días distintos producen conjuntos distintos y, con ellos, huellas distintas.

Tiene dos consecuencias. La primera es que el manifiesto de modelos, que
debería versionarse por ser texto y dejar constancia de con qué datos se
entrenó cada modelo, ensuciaría el historial cambiando en cada corrida sin que
nada real haya cambiado; por eso hoy está excluido, con el motivo escrito en las
exclusiones. La segunda es más de fondo: un pipeline cuyo conjunto de
entrenamiento cambia solo por el paso del tiempo no es reproducible, y la
reproducibilidad es un requisito del caso.

Se resuelve solo en cuanto haya datos reales, porque entonces la serie deja de
generarse. Mientras tanto, fijar la fecha de corte por configuración lo haría
determinista sin esperar a las fotografías.

## 5. Decisiones tomadas

### 5.1 Base de datos

**Motor embebido en contenedor propio**, con el archivo en un volumen dedicado
y la carpeta de imágenes montada. Se accede mediante un mapeo objeto-relacional,
de modo que la lógica de negocio no conozca el motor y cambiar a un motor
servidor sea cambiar la cadena de conexión.

El linaje es una cadena de claves foráneas, así que el modelo relacional es el
que corresponde. La parte sin estructura fija, que es el resultado crudo de la
extracción, se guarda en una columna de documento dentro de la misma tabla.

Se usará el estilo declarativo actual del mapeador: una clase base declarativa,
columnas anotadas con su tipo, y relaciones con vuelta atrás explícita sobre una
conexión de archivo local.

### 5.2 Esquema

```
image(id, sha256, original_name, source_uri, captured_at, brand, station,
      width, height, ingested_at)
   |
image_crop(id, image_id, region, bbox, path, created_at)
   |
extraction_run(id, image_id, package_version, ocr_engine, config_hash,
               executed_at)
   |
price_reading(id, extraction_run_id, image_crop_id, fuel_type, price,
              confidence, raw_text, bbox, is_valid, rejection_reason, method)
   |
silver_price(id, observed_on, fuel_type, price, price_reading_id, method)
   |
gold_dataset(id, observed_on, fuel_type, price, features, source,
             silver_price_id)
   |
trained_model(id, dataset_hash, hyperparameters, metrics, artifact_path,
              trained_at)
```

El campo `method` recorre toda la cadena y dice cómo se obtuvo cada valor:
lectura directa, reconstrucción aritmética, relleno por media, relleno por
mediana o interpolación.

La huella `sha256` de la imagen sirve a la vez de identidad, de deduplicación y
de llave de caché para la descarga.

**Regla firme: en Bronze no se rellena nunca.** La imputación ocurre al
construir Silver y Gold, y siempre queda marcada. Una fila rellenada que no se
distingue de una medida es una mentira con formato de dato.

### 5.3 Almacenamiento de imágenes: adaptable por diseño

El almacenamiento se trata como un detalle de infraestructura, no como parte de
la lógica. Se define un contrato de fuente de imágenes con las operaciones que
el pipeline necesita —listar, descargar, resolver identidad por huella— y cada
proveedor es una implementación intercambiable de ese contrato:

- Carpeta local, que es la que usa la integración continua cuando no hay
  credenciales.
- Google Drive con cuenta de servicio, que es el destino previsto.
- Almacenamiento de objetos compatible con la interfaz estándar, para cuando
  haya servidor propio.

El proveedor activo se elige por variable de entorno. Cambiar de proveedor toca
un solo módulo: ni el extractor, ni las capas, ni el modelo se enteran.

Mientras el instructor comparte su carpeta, se trabaja con una propia: se suben
las fotos disponibles, se genera la credencial y se consume exactamente igual
que se consumirá la definitiva. Así el camino queda probado de punta a punta
antes de recibir el enlace real, y el día que llegue solo cambia el
identificador de carpeta.

### 5.4 Ciclo de vida de las imágenes

```
Fuente remota
    -> data/raw/          Original intacto, nunca se edita
    -> data/interim/      Recorte de la franja de precios
    -> data/processed/    bronze, silver y gold
```

La base de datos relaciona las tres etapas: guarda la referencia al original, la
ruta del recorte con su caja delimitadora, la lectura que produjo y, más
adelante, la predicción que alimentó. Todo el ciclo es reconstruible hacia
atrás.

El recorte no es solo un ahorro de cómputo: es la evidencia de qué se leyó. Ante
una lectura sospechosa se puede mirar exactamente la porción de píxeles que la
generó.

**Cómo se ubica la franja: detección automática con calibración de respaldo.**
Se busca el visor en cada fotografía por sus características visuales, y solo
si esa búsqueda no da un resultado confiable se recurre al encuadre calibrado
que ya existe. Es la única estrategia que sobrevive a un conjunto real de
varios años con encuadres, distancias e inclinaciones distintas: la tabla de
perfiles fijos se construyó contra cinco fotos y no escala a miles.

Cada recorte guarda en la base con qué método se obtuvo su región, de modo que
al analizar los fallos se pueda separar lo que falló por detección de lo que
falló por lectura.

### 5.5 Refactorización completa de nomenclatura

Se hace el refactor completo en lugar de arrastrar la deuda, para que el
proyecto quede con un solo criterio y no a medias en dos idiomas. Va en su
propio cambio, separado de cualquier funcionalidad, con la comprobación de
nombres del linter activada para verificar que no queden restos.

| Actual | Nuevo |
|---|---|
| `datos/` | Se elimina; las imágenes salen del repositorio |
| `datos_procesados/` | `data/processed/` |
| `image_convert/` | `image_convert/` |
| `config.yml` en la raíz del caso | Se fusiona en `config/config.yaml` |
| `workshop/actividad_1` | `workshop/activity-01-sklearn-pipeline` |
| `workshop/activity-03-hyperparameter-tuning` | `workshop/activity-03-hyperparameter-tuning` |
| Identificadores del código | Inglés |
| Paquete `fuel-price-gt` | `fuel-price-gt` |
| Módulo `fuel_price_gt` | `fuel_price_gt` |
| Comando `fuel-price-gt` | `fuel-price-gt` |

El paquete también se traduce, para no dejar el proyecto a medias: sería
incoherente publicar una distribución con nombre en español cuando todo el
código quedó en inglés. `fuel-price-gt` está libre tanto en el índice público
como en el de pruebas, verificado.

La rama se mantiene con su nombre actual: renombrarla no aporta y rompe
referencias ya publicadas.

### 5.6 Publicación del paquete

Se publica en el índice de pruebas, siguiendo el mismo estándar que ya quedó
probado en el ejercicio de empaquetado propio, para no inventar un
procedimiento distinto por cada proyecto:

- Sistema de construcción con `hatchling`, no con la herramienta heredada.
- Distribución declarada por completo: nombre, versión, autoría, descripción,
  documento de presentación, versión mínima del intérprete, clasificadores,
  licencia declarada por expresión y archivo de licencia referenciado por
  patrón, y enlaces del proyecto.
- Disposición con el código bajo `src/`.
- La credencial del índice vive en `keys/`, como el resto, y la carpeta se
  excluye entera del control de versiones. Excluir por patrón de nombre falla
  en cuanto alguien guarda el archivo tal como lo descargó del proveedor.
- En la integración continua la credencial se materializa desde los secretos
  del repositorio hacia esa misma carpeta, de modo que el código tenga una sola
  ruta de lectura sea cual sea el entorno.

Lo que este caso añade respecto del ejercicio de práctica es que la
distribución tiene que ser **útil por sí misma**, no un envoltorio vacío. Quien
la instale debe poder, sin clonar el repositorio: ejecutar el flujo completo
desde la línea de comandos, leer precios de una fotografía propia, consultar el
linaje de un valor y levantar el servicio de pronóstico. Eso obliga a dos
cosas que hoy no se cumplen: que la configuración viaje dentro del paquete, y
que las dependencias pesadas queden como extras opcionales para que la
instalación mínima sea liviana.

### 5.7 Contenedores

Prefijo de proyecto y nombres temáticos consistentes, para que no choquen con
otros contenedores de la máquina y para que se recuerde qué hace cada uno:

| Servicio | Contenedor | Criterio |
|---|---|---|
| Extracción y construcción de capas | `gt-harvester` | La cosechadora que extrae el recurso |
| Base de datos | `gt-sietch` | El refugio donde se guardan las reservas |
| API de pronóstico | `gt-muaddib` | La presciencia, quien ve el futuro |
| Herramientas de línea de comandos | `gt-thopter` | Transporte ágil para tareas puntuales |
| Red | `gt-guild` | La cofradía, que lo conecta todo |

### 5.8 Ejecución mediante scripts

La lógica pasa a `scripts/`, con numeración por orden de ejecución:

```
scripts/
├── 00_verify_environment.sh    Comprueba intérprete, contenedores y dependencias
├── 01_env_init.sh              Crea .env desde la plantilla
├── 02_keys_init.sh             Materializa keys/ y reporta faltantes
├── 03_gates.sh                 Linter, pruebas y revisión de secretos
├── 10_ingest_images.py         Descarga y cachea desde la fuente activa
├── 11_crop_regions.py          Recorta la franja de precios
├── 12_extract_prices.py        Bronze
├── 13_build_layers.py          Silver y Gold, con relleno marcado
├── 14_train_models.py          Entrenamiento
├── 15_quality_gate.py          Compuerta de calidad
├── 16_recommend.py             Inferencia de humo
├── 20_db_init.py               Crea el esquema
├── 21_db_shell.sh              Consola contra la base
├── 30_models_download.py       Descarga verificada de pesos externos
├── 31_models_status.py         Estado del manifiesto
└── tools/
    ├── check_services.py       Verifica que cada credencial sirve
    ├── lineage_query.py        Linaje inverso de un precio
    └── image_source_test.py    Prueba la fuente configurada
```

Objetivos del `Makefile` agrupados por etapa: puesta en marcha, datos, base de
datos, modelos, calidad, contenedores y paquete.

### 5.9 Modelos

Dos almacenes separados, porque tienen ciclos de vida opuestos:

```
models/
├── vendor/     Pesos de terceros. Desechables, se vuelven a bajar.
└── trained/    Artefactos propios, uno por corrida de entrenamiento.
```

Ningún peso entra al repositorio. Sí entra un manifiesto de texto con
identificador, revisión exacta, huella y tamaño, que reproduce la descarga y
permite verificar integridad. La revisión se fija por identificador completo de
confirmación, nunca por rama. Los modelos entrenados quedan registrados en la
base con la huella del conjunto que los produjo, sus hiperparámetros y sus
métricas, de modo que el linaje llegue hasta la predicción.

En los contenedores los modelos van en volumen, no dentro de la imagen.

### 5.10 El modelo de visión residual se aísla

No se elimina: se mueve fuera del camino productivo, a una carpeta de
experimentos documentada como tal. Conserva el trabajo hecho y la investigación
sobre por qué hay que fijar la revisión exacta de un modelo publicado sin
etiquetas, que tiene valor para el informe, sin que su descarga de 1.5 GB ni su
ejecución de código de terceros contaminen un pipeline que debe correr en un
servidor modesto.

Queda claramente separado: lo que se exploró y se descartó, con el motivo del
descarte, es parte del recorrido del caso; lo que se ejecuta en producción es
otra cosa.

## 6. Pendientes

### 6.1 Fase A — Higiene, estructura y estándares

- [x] Corregir el titular de la licencia
- [x] Bloque de exclusiones de control de versiones, antes de crear cualquier archivo sensible
- [x] Sacar las imágenes del seguimiento y eliminar la carpeta duplicada
- [x] Dejar una sola estructura de datos: `raw`, `interim`, `processed`
- [x] Crear `keys/` con su documentación y su marcador de carpeta
- [x] Implementar los scripts de arranque de entorno y de credenciales
- [x] Escribir `.env.example`
- [x] Cargar el entorno de forma explícita en el código
- [x] Fusionar las dos configuraciones en una
- [x] Eliminar los valores quemados y llevarlos a configuración
- [x] Activar las comprobaciones de seguridad y de nomenclatura en el linter
- [x] Igualar la declaración de dependencias en todas las carpetas del repositorio
- [x] Separar el almacén de modelos y registrar cada entrenamiento en el manifiesto
- [x] Aislar el experimento de visión en `experiments/`
- [x] Alinear las rutas de la configuración con la nueva estructura de datos
- [x] Arreglar la imagen de contenedor, que dejó de construir al salir las fotografías
- [x] Instalar el motor alterno de lectura en la imagen
- [x] Sacar los datos de la imagen y montarlos como volumen
- [x] Renombrar servicios, volúmenes y red de la composición según la convención
- [x] Parametrizar los puertos de la composición desde el rango reservado
- [x] Devolver la fuente de datos a la integración continua (ver 4.15)
- [x] Actualizar el README, que describía la estructura anterior
- [x] Migrar la lógica del `Makefile` a `scripts/`
- [x] Hacer que la integración continua llame a los scripts y no al `Makefile`
- [x] Documentar todo el código y exigirlo en el linter
- [x] Documentar entorno, comandos y estructura en `docs/`
- [x] Refactorización completa de nomenclatura, en su propio cambio

### 6.2 Fase B — Persistencia, recorte y linaje

- [x] Modelo de datos declarativo con el esquema de 5.2
- [x] Script de creación de esquema, idempotente
- [x] Contenedor de base de datos con volumen dedicado y explorador web
- [x] Caché de extracción: no reprocesar una fotografía sin cambios de código ni configuración
- [x] Registrar por lectura qué motor la produjo
- [x] Recorte de la franja de precios, guardado en `data/interim`
- [x] Registrar cada recorte con su caja delimitadora y su ruta
- [x] Migrar Bronze a la base, con el resultado crudo en columna de documento
- [x] Migrar Silver y Gold, dejando los archivos tabulares como exportación
- [x] Corrección aritmética de precios ilegibles
- [x] Relleno de faltantes, siempre marcado en el campo de método
- [x] Campos de marca y estación
- [x] Consulta de linaje inverso: de un precio a la foto y el recorte
- [x] Registrar cada modelo entrenado con la huella de su conjunto
- [x] Pruebas de linaje, de reconstrucción aritmética y de relleno

### 6.3 Fase C — Ingesta y análisis con datos reales

- [x] Contrato de fuente de imágenes con implementación local
- [x] Adaptador de Google Drive con cuenta de servicio
- [x] Adaptador de Drive por enlace, con clave de API
- [x] Fuente de manifiesto: lista de direcciones, sin credencial
- [ ] Adaptador de almacenamiento de objetos
- [ ] Subir las fotos disponibles a una carpeta propia y generar la credencial
- [ ] Probar el camino completo de descarga, recorte, extracción y carga
- [x] Caché por huella para no reprocesar una fotografía ya leída
- [x] Caché por huella para no volver a descargar una fotografía ya traída
- [x] Idempotencia: reprocesar no duplica imágenes ni recortes
- [x] Procesamiento por lotes, para que el histórico completo quepa en memoria
- [x] Trabajo de ingesta condicionado a que exista la credencial
- [x] Conjunto de referencia con verdad conocida y casos negativos
- [x] Herramienta para comparar motores de reconocimiento sobre los mismos datos
- [x] Corregir la inclinación propia del display antes de comparar
- [x] Recolocar el separador decimal por posición cuando los dígitos están completos
- [x] Detectar el visor por su aspecto antes de leer, para no inventar sobre carcasa
- [ ] Revisar la verdad conocida anotada a mano antes de darla por buena
- [x] Hacer reproducible el conjunto sintético fijando la fecha de corte (ver 4.17)
- [ ] Versionar el manifiesto de modelos cuando el conjunto sea reproducible
- [ ] Volver a medir con el histórico completo y decidir si hace falta un detector entrenado
- [ ] Si la tasa de lecturas válidas queda por debajo del 70%, entrenar un detector de visor
- [ ] Revisar la calibración de paneles contra el conjunto real
- [ ] Análisis exploratorio sobre la base ya poblada, en cuaderno aparte
- [ ] Decidir y aplicar la estrategia de relleno según lo que muestre el análisis
- [ ] Contestar si el precio varía según la marca de la gasolinera

### 6.4 Fase D — Publicación del paquete

- [ ] Cambiar el sistema de construcción a `hatchling`
- [x] Renombrar la distribución, el módulo y el comando de consola
- [ ] Mover la configuración dentro del paquete y leerla como recurso
- [ ] Completar los metadatos de distribución según el estándar de 5.6
- [ ] Declarar extras opcionales para no arrastrar dependencias pesadas
- [ ] Versión leída de una sola fuente
- [ ] Comprobar que la instalación limpia permite el flujo completo sin clonar
- [ ] Guardar la credencial del índice de pruebas en `keys/`
- [ ] Trabajo de publicación disparado por etiqueta
- [ ] Verificación cruzada instalando desde el índice de pruebas en dos sistemas
- [ ] Documentar el procedimiento de publicación en `docs/`

`fuel-price-gt` está libre en el índice público y en el de pruebas, verificado.

### 6.5 Fase E — Cierre

- [ ] Documentar las tres primeras fases del ciclo de vida en `docs/`
- [ ] Diagrama del flujo completo
- [ ] Publicar el caso en la página de casos de estudio
- [ ] Etiquetas por entrega

## 7. Orden recomendado

Fase A primero: es preventiva, barata, y sin ella las demás arrancan sobre una
base que habría que rehacer. Incluye sacar las imágenes del repositorio, que
cuanto antes se haga menos historial arrastra.

Fase B enseguida, porque es lo que tiene fecha y lo que más pesa en la
evaluación.

Fase C cuando llegue el enlace, con el camino ya probado contra la carpeta
propia.

Fase D al final: se cierra rápido una vez destrabado el problema de la
configuración.

## 8. Lo que no se va a hacer

- No cambiar el modelo. La validación temporal cumple, y la única restricción
  del curso es no usar un modelo de lenguaje como predictor.
- No sustituir la lectura de siete segmentos por un modelo de visión pesado. Es
  determinista, no necesita tarjeta gráfica y respeta la restricción del
  servidor modesto.
- No mover los cuadernos al pipeline. La exploración vive aparte de la
  ejecución productiva.
- No renombrar la rama.
