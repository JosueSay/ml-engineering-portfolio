# Plan de trabajo CS2 — Sistema de puntos Club Bi

Este documento es el inventario y el pendiente del caso. La visión general está
en el [README del caso](../README.md) y el índice de la documentación en
[docs/README.md](README.md).

## 1. El encargo en una página

Corporación BI quiere optimizar su programa de lealtad. La restricción que
define el trabajo es que **quienes lo diseñaron e implementaron ya no están en
la empresa**: no hay documentación interna ni a quién preguntarle. Por eso el
caso no empieza proponiendo mejoras, empieza reconstruyendo qué hace el sistema
y con qué evidencia se sostiene cada afirmación.

El cliente espera cinco entregables:

| # | Entregable | Formato |
|---|---|---|
| E-1 | Reporte con hallazgos y documentación del sistema | Notebook o documento |
| E-2 | Diagrama de la arquitectura de datos | Herramienta de diagramación real |
| E-3 | Réplica en miniatura de la arquitectura | Notebook ejecutable |
| E-4 | Propuesta para integrar ML, IA o LLM en el pipeline | Documento |
| E-5 | Diagnóstico y propuestas de optimización | Parte del reporte |

El reporte tiene un formato pedido explícitamente, y es el contrato de entrega:

1. Resumen de la situación
2. Código o procedimiento de una prueba funcional (POC) del sistema de puntos
3. Conclusiones
4. Referencias
5. Enlace al repositorio de GitHub

La sección 7 de este documento verifica que cada una de las cinco tenga dueño.

### Marco metodológico

El caso se ordena con lo que el curso ya estableció: CRISP-DM para el ciclo,
arquitectura medallón para las capas de datos, y la distinción entre pipeline de
datos y pipeline de ML para saber dónde entra un modelo. La diferencia con CS1
es que aquí las fases de entendimiento del negocio y de los datos se ejecutan
**sin acceso al sistema**, solo con fuentes públicas, y eso cambia la naturaleza
del entregable: la trazabilidad no va del dato a la imagen de la que salió, va
de la afirmación a la fuente que la respalda.

## 2. Qué existe hoy

Lo que está terminado es la fase de investigación, y es la parte pesada del
caso.

| Artefacto | Estado | Qué contiene |
|---|---|---|
| [`config/assumptions.yaml`](../config/assumptions.yaml) | Completo | Catálogo de reglas del programa, nueve secciones, cada entrada con valor, nivel de confianza y fuente. Trece preguntas abiertas |
| [`config/poc-parameters.yaml`](../config/poc-parameters.yaml) | Completo | Los parámetros que el banco no publica y el POC necesita. Cada uno declara qué pregunta abierta sustituye. Incluye los parámetros del simulador |
| [`README.md`](../README.md) | Completo | Visión general, las ocho vías de acumulación, los cuatro orígenes técnicos y el diagrama de arquitectura en Mermaid |
| [`docs/README.md`](README.md) | Completo | Índice y ruta de lectura |
| `docs/architecture/diagrams/*.pdf` | Borrador de tercero | Primer diagrama de arquitectura. Ver problema 4.1 |

Todo lo demás son carpetas vacías con `.gitkeep`.

## 3. Qué falta

### 3.1 El reporte escrito

**Escrito, los seis.** El índice de `docs/README.md` ya no apunta a nada que
falte.

| Documento | Qué contiene | Líneas |
|---|---|---|
| [`report/01-situacion.md`](report/01-situacion.md) | Qué se pidió, qué se sabía al empezar, y las dos ideas equivocadas con que arrancó el equipo | 139 |
| [`report/02-reglas-del-programa.md`](report/02-reglas-del-programa.md) | Las reglas en prosa, cada una con su nivel de confianza, y el resumen en una tabla de veinte filas | 337 |
| [`report/03-hallazgos.md`](report/03-hallazgos.md) | Los ocho hallazgos H-1 a H-8, con severidad, evidencia y qué haría falta para cerrarlos | 388 |
| [`report/04-conclusiones.md`](report/04-conclusiones.md) | Doce recomendaciones en tres niveles por dependencia, y qué no se puede concluir desde fuera | 260 |
| [`report/05-referencias.md`](report/05-referencias.md) | Las nueve fuentes, qué aportó cada una y qué se buscó en ella sin encontrarlo | 202 |
| [`investigacion-y-supuestos.md`](investigacion-y-supuestos.md) | La bitácora, con las tres correcciones de la segunda ronda y las preguntas P-7 a P-11 | 242 |

Con la bitácora escrita, el cuestionario al cliente ya son las trece preguntas
completas: seis en `assumptions.yaml`, cinco en la sección 7 de la bitácora y dos
que nacieron en la tercera ronda.

**Pendiente de esta parte:** los enlaces profundos de `05-referencias.md`. El
documento registra las nueve fuentes y qué aportó cada una, pero los enlaces a
cada página concreta los tiene que anotar quien hizo la consulta. No se inventan:
una cita fabricada que resulta no existir invalida la fuente y con ella el
hallazgo que se apoyaba en ella.

### 3.2 La arquitectura de datos

| Pendiente | Herramienta | Nota |
|---|---|---|
| `architecture/README.md` | Markdown | Los diagramas y cómo leerlos |
| Arquitectura de datos completa | draw.io | El entregable E-2. Por tamaño no cabe en Mermaid |
| Flujo del dato | Mermaid | Origen, ingesta, capas, consumo |
| Ciclo de vida del punto | Mermaid | Acumular, acreditar, vencer, canjear. El vencimiento es un asiento, no un borrado |
| Modelo de datos | Mermaid ER | Grano del ledger: grupo familiar por periodo por origen |
| Exportaciones PNG | draw.io | `docs/architecture/exports/`, para que el reporte no dependa del archivo fuente |

El criterio de herramienta es el que ya rige en el portafolio: Mermaid para los
diagramas que se leen dentro de un documento, `.drawio` para el grande, que es
el que el cliente recibe suelto. La referencia de estilo son los `.drawio` del
curso de Administración y Mantenimiento de Sistemas.

### 3.3 El POC

`src/`, `tests/` y `scripts/` están vacíos. Lo que hace falta:

- **Motor de acumulación.** Lee los dos YAML de `config/` y no tiene ninguna
  constante incrustada. Es una promesa explícita de `poc-parameters.yaml`:
  cuando el cliente responda P-2 a P-5 se cambian los valores y el POC vuelve a
  correr sin tocar código.
- **Simulador de datos sintéticos.** Los parámetros ya están decididos: semilla
  20260922, 700 clientes, 240 grupos familiares, 30 meses desde enero de 2024.
  Y siete defectos reproducidos a propósito, porque un POC sobre datos limpios
  no demuestra nada: 3% de duplicados por reintento del autorizador, 2% de
  reversas como fila aparte, 12% de consumos sin código de rubro, 8%
  liquidados en dólares, 5% fuera de orden, más los estados de elegibilidad
  ausentes.
- **Las tres capas.** `data/processed/bronze|silver|gold` existen y están
  vacías. Bronze recibe el crudo del simulador, silver deduplica, aplica
  reversas, resuelve el rubro faltante y convierte moneda; gold es el ledger de
  lotes y los agregados.
- **Tests.** Al mínimo: que un duplicado no acredite dos veces, que una reversa
  descuente, que el tope anual corte, que FIFO consuma el lote más viejo y que
  un lote vencido deje asiento en vez de desaparecer.
- **Entorno reproducible.** CS2 no tiene `pyproject.toml`, ni `requirements`, ni
  `Makefile`. Sin eso el notebook no se puede volver a ejecutar en otra máquina,
  que es justo el problema que este caso está diagnosticando en el cliente.

### 3.4 Los notebooks

Dos, no uno, y con reparto claro para que no se dupliquen:

- `notebooks/01-replica-arquitectura.ipynb` — el entregable E-3. Recorre
  extracción, limpieza, filtrado, acumulación, ledger y canje sobre los datos
  sintéticos. Es técnico y muestra el mecanismo.
- `notebooks/02-reporte-cliente.ipynb` — el entregable E-1 en el formato de las
  cinco secciones. Importa del módulo de `src/`, no copia código, y su sección 2
  es la POC ejecutada.

La regla que gobierna ambos: cualquier tabla cuyo resultado dependa de un valor
de `poc-parameters.yaml` lo declara en la propia tabla. Es una demostración de
mecánica, no una medición del programa real.

### 3.5 La propuesta de ML, IA o LLM

`docs/proposal/ml-ai-llm.md`, el entregable E-4. No es un catálogo de
posibilidades: es una propuesta con punto de entrada en el pipeline, dato de
entrenamiento, métrica de éxito y criterio de descarte. Los candidatos que el
propio diagnóstico ya justifica:

- **Clasificación del rubro cuando el código de comercio falta.** El simulador
  lo pone en 12% y `poc-parameters.yaml` ya advierte que ahí vive el riesgo:
  un comercio mal clasificado acumula la décima parte. Es supervisado, con
  etiqueta disponible del 88% restante, y su métrica es directamente dinero.
- **Detección de duplicados y reversas** que las reglas no atrapan.
- **Propensión al canje**, para dimensionar el pasivo de puntos por vencer.
- **Un LLM sobre el corpus de reglas dispersas.** Es la respuesta directa a
  H-2: la regla existe pero vive repartida en notas al pie de páginas de
  producto. Es el caso de uso más defendible porque el problema es de
  recuperación sobre texto disperso, que es exactamente lo que un LLM con
  recuperación resuelve, y porque el propio equipo tuvo que hacerlo a mano.

Cada candidato tiene que responder qué pasa si el modelo se equivoca. Un error
de clasificación de rubro le quita puntos a un cliente real.

### 3.6 Sitio y cierre

- La tarjeta de CS2 ya existe en `pages/case-studies.html` con estado
  "Pendiente" y las claves `case.cs2.*` de `assets/i18n/`. Falta la página de
  detalle `pages/cs2-club-bi-puntos.html` y sus claves, y quitar el estado
  pendiente. CS1 tiene unas veinticinco claves de detalle como referencia.
- El README raíz no menciona los casos en su sección de estructura.
- Flujo de integración continua de CS2. Opcional, pero la lección de CS1 fue
  que un notebook que no se ejecuta en CI deja de ejecutarse: basta con
  ejecutarlo y validar los YAML.
- Merge a `main` al terminar.

## 4. Problemas detectados

### 4.1 El PDF de arquitectura contradice el catálogo de evidencia

`docs/architecture/diagrams/Arquitectura de Datos - Puntos Bi (Banco
Industrial) .pdf` es un primer borrador útil como mapa de cajas, pero presenta
como hechos cuatro cosas que el catálogo no respalda:

| Lo que dice el PDF | Lo que dice la evidencia |
|---|---|
| "Motor de reglas: tasa por tier (14-15 pts/US$10)" | La categoría de tarjeta **no cambia la tasa, cambia el tope anual**. La tasa es 1 punto por US$1, o 1 por US$10 en cinco rubros |
| "1595 pts = Q100" | 1615 puntos por el certificado de Q100, leído el 2026-09-22. `assumptions.yaml` ya registra la discrepancia |
| "NeoNet: autorización y liquidación Visa/Mastercard" | Nombre de sistema interno que ninguna fuente pública confirma |
| "Motor de campañas ML (AWS/Azure/Spark/Python)" | Stack no público. Presentarlo como hecho rompe la regla de niveles de confianza del caso |

Si el `.drawio` se dibuja copiando el PDF, hereda los cuatro y el entregable
principal queda con errores que el propio catálogo del caso ya desmiente. El
diagrama nuevo se dibuja desde `assumptions.yaml`, y lo inferido se marca como
inferido.

### 4.2 El índice de documentación apunta a archivos que no existen

`docs/README.md` enlaza ocho documentos y ninguno está creado. No es un error de
escritura: el índice se escribió como plan. Queda registrado aquí para que no se
confunda con documentación perdida.

### 4.3 No hay forma de volver a ejecutar nada

Sin `pyproject.toml` ni `Makefile`, el POC no es reproducible. Es la deuda que
hay que pagar antes de escribir la primera celda del notebook, no después.

## 5. Decisiones tomadas

- **La carpeta se llama `cs2`.** El sitio ya usaba las claves `case.cs2.*`
  mientras la carpeta se llamaba `reward-system`, y el espacio de nombres de la
  integración continua y de las etiquetas ya es `cs1-*`. Se renombró con solo
  cinco archivos dentro, que era el momento más barato. La rama conserva su
  nombre.
- **Dos notebooks, no uno.** El técnico y el del cliente tienen audiencias
  distintas y mezclarlos obliga a elegir a quién decepcionar.
- **draw.io para el diagrama grande, Mermaid para los de detalle.**
- **CS2 no lleva `.env` ni `keys/`.** No consume ninguna API ni credencial: la
  investigación fue sobre fuentes públicas y el POC corre sobre datos
  sintéticos. Toda la configuración vive en los dos YAML de `config/`. Si más
  adelante entra una fuente autenticada, la credencial va a `keys/` y la
  configuración al YAML, nunca al revés.
- **Ninguna cifra sin nivel de confianza**, en todos los entregables, incluido
  el diagrama.

## 6. Orden de trabajo

El orden no es arbitrario: cada paso desbloquea al siguiente.

| # | Paso | Por qué va aquí |
|---|---|---|
| 1 | `03-hallazgos.md` | Es lo más citado y nada lo bloquea. Mientras no exista, veinte referencias del catálogo apuntan al vacío |
| 2 | `01-situacion.md`, `02-reglas-del-programa.md`, `05-referencias.md` | Salen del catálogo casi por transcripción |
| 3 | `investigacion-y-supuestos.md` | Cierra P-7 a P-11 y completa el cuestionario de trece |
| 4 | Entorno reproducible y motor del POC | Todo lo ejecutable depende de esto |
| 5 | Simulador y las tres capas | Da los datos sobre los que corre el resto |
| 6 | Tests | Antes del notebook, no después |
| 7 | `01-replica-arquitectura.ipynb` | E-3 |
| 8 | Diagramas y `.drawio` | Después del POC: el código revela el flujo real y evita dibujar lo que se supuso |
| 9 | `ml-ai-llm.md` | E-4. Se apoya en los defectos que el simulador ya reprodujo |
| 10 | `04-conclusiones.md` | Necesita hallazgos, POC y propuesta |
| 11 | `02-reporte-cliente.ipynb` | E-1. Es lo último porque consolida todo |
| 12 | Página del sitio, README raíz, merge a `main` | Cierre |

## 7. Correspondencia con el formato pedido

Verificación de que las cinco secciones del reporte tengan dueño.

| Sección pedida | Dónde se entrega |
|---|---|
| Resumen de la situación | `02-reporte-cliente.ipynb` §1, desde `01-situacion.md` |
| Código o procedimiento de la POC | `02-reporte-cliente.ipynb` §2, ejecutando `src/` |
| Conclusiones | `02-reporte-cliente.ipynb` §3, desde `04-conclusiones.md` |
| Referencias | `02-reporte-cliente.ipynb` §4, desde `05-referencias.md` |
| Enlace al repositorio | `02-reporte-cliente.ipynb` §5 |

El diagrama, la réplica y la propuesta van como entregables aparte y el reporte
los enlaza.

## 8. Coordinación

La rama `reward-system-case-study` la trabajan tres personas. Dos cosas que
evitan choques:

- El renombre a `cs2` mueve la raíz de todo el caso. Quien tenga trabajo sin
  confirmar en `case-studies/reward-system/` debe subirlo antes de traer el
  renombre, o sus archivos van a quedar en una ruta que ya no existe.
- Los documentos de la sección 6 son independientes entre sí dentro de cada
  bloque. Dos personas pueden escribir dos documentos del reporte a la vez sin
  tocar el mismo archivo; lo que no conviene es que dos toquen
  `assumptions.yaml`, que es la fuente de la que salen todos.
