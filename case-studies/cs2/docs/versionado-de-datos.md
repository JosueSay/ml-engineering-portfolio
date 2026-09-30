# Versionado de datos y reproducibilidad: DVC y alternativas

Documento de decisión. Evalúa si DVC entra en CS2, con qué alcance, y qué
alternativas se consideraron. Al final hay dos decisiones que necesitan
respuesta y una tercera recomendación que no es para nuestro repositorio sino
para el cliente.

La versión de la sintaxis citada aquí se verificó contra la documentación
vigente de DVC, no de memoria.

## Por qué la pregunta no tiene la misma respuesta que en CS1

En CS1 el dato de entrada eran fotografías de tótems de gasolinera. Una foto
tomada un martes en una estación concreta no se puede volver a generar: si se
pierde, se perdió. Ahí el versionado de datos no es una comodidad, es la
diferencia entre poder repetir un resultado y no poder.

En CS2 el dato de entrada **no existe**. No hay acceso al sistema del cliente,
así que el POC corre sobre datos sintéticos generados por un simulador cuyos
parámetros ya están fijados en
[`config/poc-parameters.yaml`](../config/poc-parameters.yaml): semilla 20260922,
700 clientes, 240 grupos familiares, 30 meses desde enero de 2024, y siete tasas
de defecto.

Eso cambia la pregunta por completo. Si el dataset es una función determinista
de la configuración, entonces **versionar la configuración ya versiona el
dato**, y el archivo de 40 MB en el repositorio no agrega información: agrega
peso. Es la misma lección que CS1 pagó cara, cuando cinco fotografías en el
historial resultaron ser el 84% del repositorio.

## Qué resuelve DVC en realidad

Casi toda la discusión sobre DVC se arruina porque se lo trata como una cosa.
Son tres, y se pueden adoptar por separado:

| Pilar | Qué hace | Comando central |
| --- | --- | --- |
| **Versionado de datos** | Guarda el archivo grande fuera de git y deja en git un puntero de unos cientos de bytes | `dvc add`, `dvc push`, `dvc checkout` |
| **Pipelines reproducibles** | Declara etapas con sus entradas y salidas, y vuelve a ejecutar solo lo que cambió | `dvc.yaml`, `dvc repro`, `dvc dag` |
| **Experimentos y métricas** | Registra parámetros y métricas de cada corrida y las compara | `dvc exp run`, `dvc metrics` |

La decisión para CS2 es distinta en cada pilar, y ahí está el fondo del
documento.

### Pilar 1, versionado de datos: casi redundante en CS2

Casi, no del todo. Que la regeneración sustituya al versionado exige tres cosas,
y conviene verlas escritas porque dos no son obvias:

- **Determinismo real, no nominal.** Una semilla no garantiza un flujo idéntico
  entre versiones de la librería. NumPy congeló por política explícita el
  generador antiguo (`RandomState`), pero para el moderno (`Generator`) se
  reserva el derecho de cambiar el flujo en versiones de característica. Si el
  simulador usa `Generator` y alguien actualiza NumPy, la misma semilla puede
  dar otros datos. Se resuelve fijando la versión en el entorno, que es algo que
  CS2 tiene que hacer de todos modos porque hoy no tiene `pyproject.toml`.
- **Costo de regenerar bajo.** Con 700 clientes y 30 meses, regenerar es
  cuestión de segundos. Aquí se cumple de sobra.
- **Que nadie edite el dato a mano.** El día que alguien corrija una fila en
  silver para que una tabla del notebook cuadre, la regeneración deja de
  reproducir lo que se reportó. Esto no es una restricción técnica, es una
  disciplina, y es la que más fácil se rompe.

Con las tres cumplidas, `dvc add` sobre `data/` no aporta nada que la semilla no
dé. Y tiene un costo que conviene conocer: `dvc add` sobre un directorio lo
agrega al `.gitignore`, de modo que los `.gitkeep` que hoy mantienen la
estructura de carpetas visible dejarían de tener sentido y la forma de las capas
medallón desaparecería del repositorio para quien solo lo lee en GitHub.

### Pilar 2, pipelines: es el que sí vale

Aquí DVC aporta algo que hoy no existe en CS2 de ninguna forma. El flujo
bronze → silver → gold se declararía así:

```yaml
stages:
  simular:
    cmd: python scripts/10_simular.py
    deps:
      - scripts/10_simular.py
      - src/puntos_bi/simulador.py
    params:
      - config/poc-parameters.yaml:simulacion
    outs:
      - data/processed/bronze
  limpiar:
    cmd: python scripts/20_bronze_a_silver.py
    deps:
      - data/processed/bronze
      - src/puntos_bi/limpieza.py
    params:
      - config/poc-parameters.yaml:rubros_de_tasa_reducida
      - config/poc-parameters.yaml:tipo_de_cambio_gtq_usd
    outs:
      - data/processed/silver
  acumular:
    cmd: python scripts/30_silver_a_gold.py
    deps:
      - data/processed/silver
      - src/puntos_bi/motor.py
    params:
      - config/assumptions.yaml:acumulacion_transaccional
      - config/poc-parameters.yaml:grano_del_tope_anual
    outs:
      - data/processed/gold
```

Cuatro cosas de ese archivo importan más de lo que parece:

- **`params` puede apuntar a un archivo con nombre propio.** DVC usa
  `params.yaml` por omisión, pero admite el prefijo `archivo:clave`. Es el punto
  que decide la compatibilidad: los dos YAML de `config/` se quedan donde están,
  con los nombres que ya tienen, y no hay que partirlos ni renombrarlos para que
  DVC los lea.
- **La promesa de `poc-parameters.yaml` se vuelve verificable.** Ese archivo
  dice que cuando el cliente responda P-2 a P-5 se cambian los valores y el POC
  vuelve a correr sin tocar código. Hoy eso es una intención. Con las etapas
  declaradas, cambiar `tipo_de_cambio_gtq_usd` y ejecutar `dvc repro` vuelve a
  correr limpieza y acumulación y **no** vuelve a correr la simulación, porque
  DVC sabe que ese parámetro no la alimenta. La afirmación queda demostrada por
  la herramienta en vez de prometida en un comentario.
- **El grafo se dibuja desde el código.** `dvc dag` genera el flujo a partir de
  las dependencias declaradas. Un diagrama de flujo dibujado a mano se
  desincroniza del pipeline el primer día que alguien agrega una etapa; uno
  generado del código no puede. En un caso cuyo hallazgo crítico (H-2) es
  precisamente que la documentación de un sistema no coincide con el sistema,
  entregar un diagrama que se deriva del código es coherente con lo que le
  estamos recomendando al cliente.
- **Una advertencia de operación.** `dvc exp run` borra las salidas de una etapa
  antes de ejecutarla, salvo que se marque `persist: true`. Para capas que se
  regeneran completas es el comportamiento deseado; conviene saberlo antes de
  que borre algo que alguien creía acumulativo.

### Pilar 3, experimentos: no aplica todavía

`dvc exp` y las métricas sirven para comparar corridas de un modelo. CS2 no
entrena nada por ahora: la propuesta de ML es un documento, no un modelo
entrenado. Si el candidato de clasificación de rubro llegara a implementarse,
este pilar entra solo y sin discusión. Hoy sería maquinaria sin carga.

## Qué uso tiene DVC en el sistema de puntos

Hasta aquí el documento hablaba de nuestro repositorio. Esta sección responde la
otra pregunta, que es la que importa para el entregable: **qué uso tendría una
herramienta de versionado en el sistema de puntos del cliente.**

La respuesta empieza partiendo los datos del banco en dos clases. La división no
es por tamaño ni por tecnología, es por **con qué frecuencia cambian y a cuántas
transacciones afectan**:

| Clase | Ejemplos | Cómo cambia | A qué afecta un cambio |
| --- | --- | --- | --- |
| **Datos de referencia** | Reglas del programa, mapa de rubros, catálogo de premios, política de tipo de cambio, tasas de millas por producto, topes por categoría | Raras veces, por decisión humana | A cada acreditación futura, y a la interpretación de todas las pasadas |
| **Datos transaccionales** | Consumos, saldos promedio, lotes acreditados, canjes | Constantemente, por evento | A una fila |

DVC está construido para la primera clase y es inservible para la segunda. Ahí
está el uso, y ahí está el límite.

### Cinco usos concretos, cada uno anclado a un hallazgo

**U-1. Versionar el mapa de rubros del comercio.** La decisión de aplicar la tasa
base o la reducida depende de clasificar el comercio, y ese mapa es un archivo
que cambia por decisión humana. Un comercio reclasificado acumula la décima
parte, o diez veces más. Hoy no se puede responder *con qué versión del mapa se
acreditó esta transacción*. Con el mapa versionado, sí. Ancla: H-6.

**U-2. Versionar el catálogo de premios.** El caso tiene la prueba de que cambia:
el PDF de arquitectura registra 1,595 puntos por el certificado de Q100 y la
lectura del 22 de septiembre de 2026 dice 1,615. Sin versionar el catálogo no se
puede decir cuánto valía un punto el día que alguien lo canjeó, que es el único
número con el que se puede juzgar si el canje fue justo.

**U-3. Versionar las reglas del programa como configuración ejecutable.** Es el
uso más fuerte y el menos obvio. H-2 dice que la regla no está escrita en ningún
lado. La respuesta intuitiva es escribir un manual, pero un manual se
desincroniza del motor en el primer cambio: es la enfermedad que el cliente ya
tiene. La respuesta estructural es que **el motor lea la regla de un archivo
versionado y legible**, de modo que la documentación y la configuración sean el
mismo objeto y no puedan divergir.

Nuestro POC es la demostración de eso. El motor no tiene constantes
incrustadas: lee [`assumptions.yaml`](../config/assumptions.yaml). Lo que le
recomendamos al cliente es exactamente lo que el POC hace, y eso se puede
mostrar corriendo en vez de argumentar.

**U-4. Versionar el conjunto de entrenamiento y el modelo del clasificador de
rubro.** Es el uso canónico de DVC y el único donde el artefacto es grande. Si el
candidato de ML de [`proposal/ml-ai-llm.md`](proposal/ml-ai-llm.md) llega a
implementarse, hace falta poder decir con qué datos se entrenó el modelo que
clasificó un comercio concreto. Sin eso, una reclamación sobre puntos mal
acreditados no se puede investigar.

**U-5. Reproducir un estado de cuenta histórico ante un reclamo.** Es el uso que
justifica los otros cuatro. Para recalcular el saldo de un cliente a una fecha
pasada hacen falta cuatro cosas: el registro de transacciones, las reglas
vigentes entonces, el tipo de cambio de entonces y el mapa de rubros de entonces.
La primera existe. Las otras tres son datos de referencia, y hoy ninguna se
guarda con su vigencia. Ancla: H-4 y H-7.

Ese último punto merece decirse sin rodeos, porque es el hallazgo detrás del
hallazgo: **hay algo peor que un tipo de cambio no público, y es un tipo de
cambio no guardado.** Si la acreditación registra los puntos resultantes pero no
la tasa con la que convirtió, el saldo no es reproducible ni teniendo las reglas
en la mano. El banco no puede auditar su propio motor hacia atrás.

### Dónde DVC no tiene ningún uso en el sistema de puntos

Decir esto es lo que hace creíble lo anterior:

- **Volumen transaccional.** DVC versiona árboles de directorios. No tiene
  transacciones, ni escritura concurrente, ni viaje en el tiempo por fila. Para
  eso existen Delta Lake e Iceberg.
- **Retención regulatoria.** El caché de DVC no es un almacén de auditoría. Un
  banco necesita inmutabilidad demostrable, y eso es una propiedad del
  almacenamiento, no de la herramienta que lo indexa.
- **Ruta operativa.** Una autorización de tarjeta no puede esperar un `dvc pull`.
  DVC es una herramienta del ciclo de desarrollo.
- **Gobierno de acceso.** No tiene permisos por fila ni por columna. En un banco
  eso no es un detalle.

## Las alternativas

Se evaluaron siete. Las dos últimas no son alternativas en sentido estricto y se
explica por qué.

| Opción | Qué resuelve | Costo de entrada | Veredicto para CS2 |
| --- | --- | --- | --- |
| **Make y regeneración con semilla** | Orquestación mínima. Es lo que hace CS1 | Nulo, ya se conoce | Suficiente, pero no declara dependencias: `make` no sabe qué etapa invalida un cambio de parámetro |
| **DVC, solo pipelines** | Dependencias declaradas, ejecución incremental, grafo derivado del código | Bajo. Un archivo y un `dvc init` | **Recomendado** |
| **DVC completo, con remoto** | Lo anterior más datos versionados fuera de git | Medio. Hace falta un remoto y gobernarlo | No: los datos son regenerables y el remoto es infraestructura sin dueño |
| **Git LFS** | Solo guarda blobs grandes fuera del historial | Bajo | No: no aporta pipeline ni parámetros, y el problema de CS2 no es el tamaño |
| **Delta Lake** | Capas medallón con historial y viaje en el tiempo sobre las tablas | Medio a alto. Spark o `delta-rs` | No para el POC. Sí como referencia de lo que se le recomienda al cliente |
| **Databricks con Unity Catalog** | Linaje automático, permisos por rol, medallón gobernada | Alto. Plataforma, cuenta y aprovisionamiento | No para el POC. Es el marco del curso y el lenguaje natural de la propuesta al cliente |
| **lakeFS** | Ramas y commits sobre un almacén de objetos completo | Alto | No: resuelve un problema de escala que CS2 no tiene |
| **MLflow** | Registro de experimentos y de modelos | Bajo | No es alternativa. Es complementario, y solo cuando haya modelo |
| **Parquet con hash de contenido** | Verificar que un archivo es el que se reportó, sin versionarlo | Muy bajo | Complemento útil: cierra el agujero de la edición manual sin traer ninguna herramienta |

Ese último merece una línea propia, porque es la contramedida más barata al
riesgo más probable. Si cada capa deja escrito el hash de su salida junto con la
semilla y la versión de las librerías, entonces una edición a mano se detecta al
volver a ejecutar, y la regeneración deja de depender de la disciplina de nadie.
Son veinte líneas de código y resuelven la única de las tres condiciones de la
sección anterior que no se puede garantizar por construcción.

## Cómo se evaluó: matriz de decisión ponderada

La tabla anterior es el juicio cualitativo. Esta sección lo pone en números con
una **matriz de decisión ponderada**, el método clásico de evaluación multicriterio
(también llamado matriz de Pugh), y registra la decisión en el formato de un
registro de decisión de arquitectura: opciones, criterios, veredicto y qué lo
haría cambiar.

El método tiene una debilidad conocida y conviene nombrarla antes de usarlo: **los
pesos los elige quien hace la matriz**, así que una matriz puede justificar
cualquier conclusión si se ajustan después de ver los puntajes. Dos contramedidas,
las dos aplicadas aquí:

- Los pesos se declaran y se justifican **antes** de puntuar.
- Al final hay un **análisis de sensibilidad**: si el ganador cambia al mover un
  peso, la conclusión es frágil y hay que decirlo.

Las notas van de 1 a 5, donde 5 es mejor. Los totales son la suma de nota por
peso.

### Matriz A: la decisión de nuestro POC

Los criterios, con su peso y por qué:

| ID | Criterio | Peso | Por qué ese peso |
| --- | --- | --- | --- |
| A1 | Reproducibilidad de la corrida que se reportó | 5 | Es el requisito del entregable. Sin esto el notebook no se puede defender |
| A2 | Ejecución incremental por valor de parámetro | 4 | Es la promesa explícita de `poc-parameters.yaml` |
| A3 | Grafo del flujo derivado del código | 3 | Evita que el diagrama del entregable se desincronice |
| A4 | Costo de entrada | 3 | Somos tres personas con un semestre |
| A5 | Reversibilidad si se abandona | 2 | Importa, pero es una salvaguarda, no un objetivo |
| A6 | Familiaridad del equipo | 2 | Se compensa con documentación |

| Opción | A1 | A2 | A3 | A4 | A5 | A6 | **Total** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **DVC solo pipelines** | 5 | 5 | 5 | 4 | 5 | 3 | **88** |
| DVC completo con remoto | 5 | 5 | 5 | 2 | 3 | 2 | 76 |
| Makefile | 4 | 2 | 2 | 5 | 5 | 5 | 69 |
| Nada (estado de hoy) | 2 | 1 | 1 | 5 | 5 | 5 | 52 |

El criterio que decide es A2, y vale explicar por qué `make` saca 2 y no 5:
**`make` reacciona a fechas de modificación de archivos, no a valores de
parámetros.** Si se declara `poc-parameters.yaml` como dependencia de una etapa,
entonces cambiar *cualquier* clave del archivo invalida *todas* las etapas que lo
declaran, incluida la simulación que ese parámetro no alimenta. DVC declara la
dependencia a nivel de clave, así que cambiar el tipo de cambio vuelve a correr
limpieza y acumulación y deja la simulación intacta. Es la diferencia entre
demostrar la promesa de `poc-parameters.yaml` y aproximarla.

### Matriz B: la decisión del cliente

Aquí la pregunta es otra: **con qué se versionan los datos de referencia que
gobiernan la acumulación.** El alcance son los datos de referencia, no los
transaccionales, por la división de la sección anterior.

| ID | Criterio | Peso | Por qué ese peso |
| --- | --- | --- | --- |
| C1 | Reproducibilidad de una acreditación pasada | 5 | Es el requisito que originó el análisis. H-4 y H-7 |
| C2 | Auditabilidad ante un reclamo o un regulador | 4 | Es un banco. No es opcional |
| C3 | Que la regla publicada y la que ejecuta el motor sean el mismo artefacto | 4 | Ataca H-2, el hallazgo crítico |
| C4 | Costo y fricción de adopción | 3 | Una recomendación que el banco no puede adoptar no sirve |
| C5 | Gobierno de acceso | 2 | Necesario, pero resoluble en cualquiera de las opciones |
| C6 | Se extiende también a los datos transaccionales | 2 | Vale tener una sola herramienta, pero no es el problema que se está resolviendo |

| Opción | C1 | C2 | C3 | C4 | C5 | C6 | **Total** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **O7. Tablas con vigencia para el motor, más git como documento** | 5 | 4 | 5 | 3 | 5 | 4 | **88** |
| O2. Tablas de referencia con vigencia, tipo SCD 2 | 5 | 4 | 2 | 4 | 5 | 4 | 79 |
| O5. Catálogo gobernado sobre Delta Lake | 5 | 5 | 2 | 1 | 5 | 5 | 76 |
| O6. Git puro con los archivos de reglas | 5 | 3 | 5 | 4 | 1 | 1 | 73 |
| O4. Delta Lake con viaje en el tiempo | 5 | 4 | 2 | 2 | 3 | 5 | 71 |
| O3. DVC sobre los datos de referencia | 5 | 3 | 5 | 3 | 1 | 1 | 70 |
| O1. Sin versionar, el estado de hoy | 1 | 1 | 1 | 5 | 2 | 1 | 34 |

**El resultado es incómodo para la pregunta que lo originó, y por eso vale.** Para
los datos de referencia del cliente, **git puro (73) puntúa por encima de DVC
(70)**. La razón es simple: los artefactos de referencia son pequeños y son texto
—una tabla de rubros son unos miles de filas, las reglas son un YAML— y para eso
la maquinaria de DVC no compra nada que git no dé, mientras sí cobra fricción de
adopción en una organización donde introducir una herramienta nueva es un
proyecto. DVC recupera su lugar solo en U-4, donde el artefacto es un conjunto de
entrenamiento y un modelo, que es precisamente el caso para el que fue diseñado.

**La opción ganadora es una combinación**, y hay que decir su riesgo: mantener la
regla en un archivo versionado y además en tablas con vigencia son dos
representaciones de lo mismo, y dos representaciones de lo mismo se desincronizan.
Sería reproducir la enfermedad que le estamos diagnosticando. La mitigación es
una condición, no una recomendación: **las tablas se generan desde el archivo, no
se mantienen en paralelo.** El archivo es la fuente y la tabla es su despliegue.
Con eso, O7 no es un compromiso entre dos opciones sino una sola con dos caras.

### Análisis de sensibilidad

Qué pasaría con otros pesos. Es la prueba de si la conclusión aguanta.

| Variación | Gana | Segundo |
| --- | --- | --- |
| C3 sube de 4 a 6, si atacar H-2 pesara más | O7 (98) | O2 (83) |
| C4 baja de 3 a 1, si el costo de adopción no importara | O7 (82) | O5 (74) |
| C6 sube de 2 a 5, si se quisiera una sola herramienta para todo | O7 (100) | O2 (91) |
| Todos los pesos iguales a 1 | O7 (26) | O2 (24) |

O7 gana en las cuatro variaciones, incluida la de pesos iguales, que es la que
elimina por completo el juicio de quien armó la matriz. La conclusión es robusta.

Dos cosas que la sensibilidad sí revela:

- **Lo único que le impide ganar al catálogo gobernado es el costo de adopción.**
  Si el banco ya tiene la plataforma, O5 se vuelve la respuesta y hay que
  revisarla. Es una pregunta para el cliente, no una conclusión nuestra.
- **El orden entre DVC y git puro no se invierte en ninguna variación.** No es un
  empate fino: para datos de referencia pequeños, DVC agrega herramienta sin
  agregar capacidad.

## Recomendación para CS2

**DVC sí, solo el pilar de pipelines. Sin remoto y sin versionar los datos.**

Concretamente:

- `dvc init` y un `dvc.yaml` con las etapas del flujo medallón, leyendo
  parámetros de los dos YAML que ya existen.
- `data/processed/**` sigue fuera del repositorio por `.gitignore`, como está
  hoy, y no se agrega con `dvc add`.
- Sin `dvc remote` ni `dvc push`. Nadie tiene que aprovisionar nada.
- `dvc.lock` sí se confirma: es el registro de qué versión de cada parámetro
  produjo la corrida que se reportó, y ocupa kilobytes.
- El hash de cada capa se escribe en el `dvc.lock` por la propia herramienta, lo
  que cubre gratis la contramedida del párrafo anterior.

Qué se gana, en una frase: el notebook deja de ser la única forma de ejecutar el
flujo, y el diagrama de flujo del entregable deja de poder mentir.

Qué cuesta: una dependencia de desarrollo más y un archivo que hay que mantener
al día cuando cambie una etapa. Si se abandona, se borra `dvc.yaml` y los
scripts siguen corriendo solos, porque las etapas son comandos de Python
normales. La salida no tiene costo, y eso es la mitad del argumento para
entrar.

**Alternativa si la respuesta es no:** un `Makefile` con las mismas etapas, como
CS1. Se pierde la ejecución incremental y el grafo derivado del código; no se
pierde la reproducibilidad, porque esa la da la semilla y el entorno fijado.
Lo que **no** es aceptable es seguir sin ninguna de las dos, que es el estado de
hoy.

## La otra mitad: qué de esto va en la propuesta al cliente

Aquí DVC no es la respuesta, y decirlo importa porque es la tentación obvia. El
cliente es un banco con un core de depósitos, un autorizador de tarjetas y un
motor de campañas. No tiene un repositorio git con archivos de datos: tiene
sistemas transaccionales. DVC es una herramienta para el ciclo de desarrollo, no
para una plataforma de producción bancaria.

Pero la **lección** sí se traslada, y se traslada directo a dos hallazgos:

- **H-7 dice que hay una vía de acreditación que no se puede reconstruir.** Los
  puntos de sorteo no son función de ningún dato del cliente, así que si su
  registro se pierde no hay desde dónde rederivarlos. Eso es exactamente el
  problema que el versionado resuelve: la salida existe y la entrada que la
  produjo no quedó guardada.
- **H-4 dice que el tipo de cambio de acumulación no es público**, y hay algo
  peor que no sea público: que no se guarde. Si cada acreditación guarda los
  puntos resultantes pero no la tasa con la que se convirtió, entonces el saldo
  no es reproducible **ni teniendo las reglas en la mano**. El banco no puede
  auditar su propio motor hacia atrás.

De ahí sale una recomendación concreta y del tamaño correcto para el cliente:
**que cada lote acreditado guarde los parámetros con los que se acreditó**, no
solo el resultado. Tipo de cambio aplicado y su fecha, versión de la tabla de
rubros, identificador de la campaña o del sorteo, estado de elegibilidad
consultado en ese momento. Es un puñado de columnas más en el ledger, y convierte
un sistema que hoy solo se puede creer en uno que se puede verificar.

Ese es el vocabulario del curso: es linaje. Y es el único lugar del caso donde
una decisión de plataforma —Delta Lake, Unity Catalog o el equivalente que ya
tenga el banco— entra con justificación propia en vez de como moda. El
desarrollo completo va en
[`architecture/README.md`](architecture/README.md) y en
[`proposal/ml-ai-llm.md`](proposal/ml-ai-llm.md), porque un modelo que lee del
ledger hereda lo que el ledger no guardó.

## Lo que hace falta decidir

| # | Decisión | Recomendación | Respaldo | Qué bloquea |
| --- | --- | --- | --- | --- |
| D-1 | ¿Entra DVC en el POC, solo como pipeline? | Sí | Matriz A: 88 contra 69 del `Makefile` | El paso 4 del plan: entorno y motor del POC |
| D-2 | ¿Los datos sintéticos se versionan o se regeneran? | Se regeneran, con hash registrado | [origen-de-los-datos.md](origen-de-los-datos.md), matriz C | Lo mismo que D-1 |
| D-4 | ¿Qué se le recomienda al cliente para versionar sus datos de referencia? | Tablas con vigencia generadas desde un archivo versionado. **No DVC** | Matriz B: 88, y git puro (73) por encima de DVC (70) | La propuesta y las conclusiones |

Ninguna de las dos bloquea la escritura del reporte, los diagramas ni las
referencias. Si la respuesta a D-1 es no, se sustituye por un `Makefile` y el
resto del plan no cambia una línea.
