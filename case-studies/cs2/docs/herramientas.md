# Herramientas del caso: de la causa raíz a la decisión

Este documento existe para que ninguna herramienta de CS2 entre por moda. Cada
una se deriva de una causa raíz identificada con los **cinco porqués**, y al
final hay una tabla que conecta cada causa con la herramienta que la atiende.

Las decisiones de versionado y de origen de los datos tienen su propio documento,
con matrices ponderadas: [versionado-de-datos.md](versionado-de-datos.md) y
[origen-de-los-datos.md](origen-de-los-datos.md). Aquí está el marco que las
ordena y el resto del stack.

## El método, y su debilidad

Los cinco porqués consisten en preguntar por la causa de la causa hasta llegar a
algo que, si se corrigiera, evitaría el problema entero. A veces se llega en tres;
lo que importa no es el número sino dejar de parar en el primer síntoma.

Su debilidad es conocida: **la cadena se desvía si cada porqué se responde con lo
primero que viene a la mente.** Cinco pasos de especulación encadenada producen una
causa raíz falsa que suena profunda. La contramedida que se aplica aquí es que
**cada eslabón cita evidencia del caso** —un hallazgo, una fuente del catálogo o un
hecho verificado— y donde no hay evidencia se dice que el eslabón es una
inferencia. Es la misma regla que gobierna el resto del diagnóstico.

## Cadena 1: ¿por qué el cliente necesita que alguien de fuera le explique su propio sistema?

1. **¿Por qué?** Porque nadie dentro de la empresa sabe con precisión qué hace el
   sistema de puntos. *Es el encargo, literalmente.*
2. **¿Por qué?** Porque quienes lo diseñaron e implementaron se fueron y no
   dejaron documentación interna. *Es el encargo.*
3. **¿Por qué no había documentación?** Porque la regla nunca vivió en un
   documento. Vive repartida en notas al pie de las páginas de producto, en las
   preguntas frecuentes de dos programas distintos y en las bases de cada
   promoción. *Es H-2, con evidencia pública.*
4. **¿Por qué vivió repartida?** Porque no existía un artefacto único del que
   salieran a la vez el motor y la comunicación. Cada área escribió su versión de
   la regla para su propio material. *Inferencia, sostenida por dos fuentes del
   emisor que se contradicen sobre el multiplicador de la membresía y por tres
   listas distintas de comercios aliados.*
5. **¿Por qué no existía ese artefacto?** Porque el programa creció por adiciones
   —ocho vías de acumulación, campañas temporales, unificación familiar, tres
   canales de canje— y ninguna adición obligó a consolidar la regla en un solo
   lugar. *Inferencia.*

**Causa raíz.** La regla del programa nunca fue un artefacto versionado del que
dependieran el motor y la publicación.

**Qué se sigue.** La respuesta no es escribir un manual: un manual se desincroniza
del motor en el primer cambio, que es la enfermedad que el cliente ya tiene. La
respuesta es **configuración ejecutable y versionada**: que el motor lea la regla
de un archivo legible, de modo que documentación y configuración sean el mismo
objeto. Nuestro POC lo hace así, y por eso la recomendación se puede mostrar
corriendo en vez de argumentar.

## Cadena 2: ¿por qué no se puede reconstruir el saldo de un cliente a una fecha pasada?

1. **¿Por qué?** Porque no se puede saber con qué tipo de cambio se convirtió cada
   consumo. *Es H-4: ninguna fuente publica la política de conversión.*
2. **¿Por qué no se puede saber?** Porque el motor guarda el resultado de la
   acreditación, no las entradas con las que la calculó. *Inferencia, sostenida
   por H-7: hay una vía cuyos puntos no se pueden rederivar.*
3. **¿Por qué guarda solo el resultado?** Porque la acreditación se diseñó como un
   cálculo y no como un asiento con procedencia. *Inferencia.*
4. **¿Por qué se diseñó así?** Porque los parámetros se consideraron estables: una
   tasa "es" la tasa, un mapa de rubros "es" el mapa. No se los trató como datos
   que tienen vigencia. *Inferencia.*
5. **¿Por qué no se los trató como datos con vigencia?** Porque no existía la
   distinción entre datos de referencia y datos transaccionales. Todo lo que no
   era una transacción era una constante del sistema. *Inferencia.*

**Causa raíz.** Los parámetros que gobiernan la acumulación se trataron como
constantes del código y no como datos con vigencia.

**Qué se sigue.** Dos cosas, y las dos están cuantificadas en la matriz B de
[versionado-de-datos.md](versionado-de-datos.md): tablas de referencia con
vigencia para lo que el motor consulta, generadas desde el archivo versionado de
la cadena 1; y columnas de procedencia en el ledger, para que cada lote acreditado
diga con qué tipo de cambio, qué versión del mapa de rubros y qué estado de
elegibilidad se acreditó.

Nótese que esta cadena y la primera llegan al mismo lugar por caminos distintos.
Eso es lo que da confianza en la causa raíz: no es una sola línea de razonamiento.

## Cadena 3: ¿por qué nuestro propio POC podría no ser reproducible?

Vale correr el método contra nosotros mismos, porque el caso pierde autoridad si
le diagnostica al cliente un problema que tiene en casa.

1. **¿Por qué?** Porque hoy CS2 no declara su entorno: no hay `pyproject.toml` ni
   versiones fijadas. *Hecho verificado.*
2. **¿Por qué importa, si el simulador tiene semilla?** Porque una semilla no
   garantiza la misma secuencia entre versiones de la librería.
3. **¿Por qué no la garantiza?** Porque NumPy congeló por política el generador
   antiguo, pero para el moderno se reserva el derecho de cambiar el flujo en
   versiones de característica. *Verificado contra la política de NumPy.*
4. **¿Por qué nadie lo fijó todavía?** Porque el caso arrancó por la
   investigación y el código aún no existe. *Hecho.*
5. **¿Por qué eso es un riesgo y no solo una tarea pendiente?** Porque el
   entregable es un notebook con cifras, y una cifra que no se puede volver a
   producir es una afirmación sin evidencia, que es justo lo que este caso se
   prohíbe. *Inferencia directa de la regla del caso.*

**Causa raíz.** La reproducibilidad de una corrida depende del entorno y del
pipeline declarados, no de la semilla sola.

**Qué se sigue.** `pyproject.toml` con versiones fijadas, `dvc.yaml` con las
etapas declaradas, y el hash de cada capa registrado en `dvc.lock`. Los tres
juntos, porque cada uno cubre una parte distinta: el entorno fija la librería, el
pipeline fija el orden y los parámetros, el hash detecta la edición manual.

## De la causa raíz a la herramienta

| Causa raíz | Qué exige | Herramienta | Dónde vive |
| --- | --- | --- | --- |
| La regla nunca fue un artefacto versionado | Configuración legible que el motor lea | YAML en `config/`, leído por el motor | Ya existe: `assumptions.yaml` y `poc-parameters.yaml` |
| Los parámetros se trataron como constantes | Vigencia y procedencia | Columnas de procedencia en el ledger del POC, y tablas con vigencia en la recomendación al cliente | `src/` y la propuesta |
| La reproducibilidad no depende de la semilla | Entorno, pipeline y verificación | `pyproject.toml`, `dvc.yaml`, `dvc.lock` | Por construir |

## El stack de CS2

Cada línea dice por qué, no solo qué.

| Herramienta | Para qué | Por qué esta |
| --- | --- | --- |
| Python 3.12 | El POC | Continuidad con CS1. El equipo ya tiene el entorno |
| pandas | Las tres capas | El volumen es del orden de cientos de miles de filas. Nada justifica un motor distribuido |
| Parquet | Formato de bronze, silver y gold | Preserva tipos. Un CSV convierte la fecha en texto y el caso depende de fechas para el vencimiento por lote |
| `pyproject.toml` con hatchling | Entorno declarado | Mismo backend que CS1. Las versiones fijadas son requisito de la cadena 3 |
| DVC, solo pipelines | Etapas, parámetros por clave, grafo | Matriz A: 88 contra 69 del `Makefile`. La discriminante es que `make` reacciona a fechas de archivo y no a valores de parámetro |
| pytest | Tests del motor | Estándar, y CS1 ya lo usa |
| ruff | Linter y formato | Ya en uso en CS1 |
| Jupyter | Los dos notebooks | Es el formato que pide el cliente para el reporte |
| draw.io | El diagrama de arquitectura del cliente | Por tamaño. El `.drawio` es texto, así que versiona bien y se puede revisar en un diff |
| Mermaid | Los diagramas de detalle | Se leen dentro del documento y no exigen abrir una herramienta |
| YAML | Configuración | Ya establecido, y DVC lee parámetros por clave desde archivos con nombre propio |

Y lo que **no** lleva, porque decidir que algo no entra también es una decisión:

| Descartado | Por qué |
| --- | --- |
| Spark o Databricks | Cientos de miles de filas. Sería infraestructura sin carga. Sí aparece en la recomendación al cliente, que sí tiene volumen |
| Delta Lake en el POC | Mismo motivo. Su viaje en el tiempo resuelve un problema que el POC no tiene |
| DVC con remoto | Matriz A: 76 contra 88. Los datos son regenerables y el remoto es infraestructura sin dueño |
| Git LFS | No aporta pipeline ni parámetros, y el problema de CS2 no es el tamaño |
| Generador entrenado tipo CTGAN | Matriz C: 50 de 106. No hay datos reales de los que aprender, y no entrega etiqueta de los defectos |
| DuckDB | Considerado para las consultas de la capa gold. pandas alcanza, y una dependencia que no se necesita es deuda |
| Base de datos | CS1 la necesitaba por el linaje de imágenes. Aquí el grano es pequeño y el entregable es un notebook |
| `.env` y `keys/` | CS2 no consume ninguna API ni credencial. Toda la configuración vive en los dos YAML |

## Qué de esto va en la propuesta al cliente

La distinción es la misma que rige todo el caso: lo que sirve para nuestro ciclo
de desarrollo no es lo que sirve para una plataforma bancaria en producción.

- **Sí se traslada la idea:** configuración versionada de la que dependa el motor,
  vigencia en los datos de referencia, procedencia en el ledger.
- **No se traslada la herramienta:** DVC es del ciclo de desarrollo. Para el banco,
  las tablas con vigencia y, si ya tiene la plataforma, un catálogo gobernado. La
  matriz B lo cuantifica, incluido el resultado incómodo de que para datos de
  referencia pequeños git puro puntúa por encima de DVC.

El desarrollo va en [proposal/ml-ai-llm.md](proposal/ml-ai-llm.md) y en
[architecture/README.md](architecture/README.md).
