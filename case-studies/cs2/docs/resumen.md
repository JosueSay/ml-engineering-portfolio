# Resumen del caso: qué es, cómo vamos y cómo entra DVC

Documento de orientación. Condensa todo el caso en una lectura seguida, para
tener el panorama completo sin abrir ocho archivos. No es un entregable al
cliente: es el mapa.

Si buscas el detalle de un punto concreto, el índice está en
[README.md](README.md). Si buscas el inventario de tareas con su orden, está en
[work-plan.md](work-plan.md). Este documento explica **por qué** las cosas son
como son.

## El caso en cinco minutos

Corporación BI quiere optimizar su programa de lealtad, Puntos Bi. La
restricción que define todo el trabajo es una sola frase del encargo: **quienes
diseñaron e implementaron el programa ya no trabajan en la empresa.** No hay
documentación interna, no hay a quién preguntarle, y no hay acceso al sistema.

Eso invierte el orden natural del trabajo. No se puede empezar proponiendo
optimizaciones porque no se sabe qué se estaría optimizando. Hay que empezar
estableciendo **qué hace el sistema**, reconstruyéndolo desde fuera con lo que el
banco publica, y dejando escrito con qué evidencia se sostiene cada afirmación.

El cliente espera cinco cosas: un reporte con hallazgos y documentación del
sistema, un diagrama de la arquitectura de datos, una réplica en miniatura de esa
arquitectura en un notebook, una propuesta para meter un modelo de ML o un LLM en
el pipeline, y el diagnóstico con propuestas de optimización. El reporte tiene un
formato pedido explícitamente: resumen de la situación, código de una prueba
funcional, conclusiones, referencias y enlace al repositorio.

## Por qué este caso no se parece a CS1

En CS1 la trazabilidad iba del dato a la imagen de la que salió. Cada precio
declaraba si fue leído de una foto, interpolado o imputado, y eso viajaba hasta
el modelo.

Aquí la trazabilidad cambia de objeto: va **de la afirmación a la fuente que la
respalda.** No hay un dato que rastrear porque no hay acceso a los datos. Lo que
hay que poder defender ante el cliente es cada frase del reporte, y por eso el
artefacto central del caso no es una base de datos sino un catálogo de reglas
donde cada entrada dice de dónde salió.

Ese catálogo es [`config/assumptions.yaml`](../config/assumptions.yaml), y es del
que salen todos los demás documentos. Son nueve secciones y unas 850 líneas.

## Las tres reglas que explican casi todo

Cualquier decisión del caso sale de una de estas tres, y vale la pena tenerlas
presentes porque son lo que hace que el entregable valga.

**Nada se afirma sin nivel de confianza.** Público si se cita de una fuente de
Corporación BI, inferido si se deduce de algo que sí lo está, supuesto si lo
eligió el equipo. Es la única forma de que el cliente pueda separar lo que su
propio banco ya publica de lo que nosotros dedujimos.

**La ausencia de información es información.** Cuando una fuente no dice algo que
debería decir, se registra como ausencia verificada, con la fuente donde se
buscó. Eso permite afirmar que cuatro categorías de tarjeta publican su tope
anual y el resto no, en vez de insinuarlo.

**Lo que no se sabe se convierte en pregunta, no en supuesto conveniente.** Hay
trece preguntas abiertas y son parte de la entrega. Un diagnóstico que rellena
sus huecos con estimaciones plausibles le traslada el riesgo al cliente sin
avisarle.

De esa tercera regla sale un detalle de diseño que conviene entender: hay **dos**
archivos de configuración, no uno.
[`assumptions.yaml`](../config/assumptions.yaml) documenta el sistema y se
detiene cuando algo no es público.
[`poc-parameters.yaml`](../config/poc-parameters.yaml) tiene los números que el
código necesita para correr, y cada uno declara qué pregunta abierta está
sustituyendo. Así el catálogo de evidencia no se contamina con valores
inventados, y cualquier resultado del notebook que dependa de uno de esos
números lo dice en la propia tabla.

## Qué encontramos

Ocho hallazgos. Siete se sostienen sobre fuentes públicas del propio emisor: no
hizo falta acceso al sistema, solo leer con cuidado lo que el banco ya publica.
El detalle está en [report/03-hallazgos.md](report/03-hallazgos.md).

| ID | En una línea | Severidad |
| --- | --- | --- |
| H-2 | La regla que gobierna el sistema no está escrita en ningún lado. Vive repartida en notas al pie | Crítica |
| H-4 | La regla está en dólares, el consumo en quetzales, y el tipo de cambio no es público | Crítica |
| H-5 | El portal de puntos admite contraseñas de cuatro caracteres | Crítica |
| H-1 | Los puntos no son intercambiables entre sí, y seis canales muestran el saldo como si lo fueran | Alta |
| H-3 | La vigencia real va de 13 a 25 meses y se comunica como "dos años" a todos | Alta |
| H-6 | La penalización de diez a uno cae sobre supermercado y gasolinera, y se comunica en un asterisco | Alta |
| H-7 | Hay una vía de acreditación que no se puede reconstruir desde las transacciones | Media |
| H-8 | Hay tres canales de canje y el cliente solo conoce uno | Media |

Tres de los ocho no son defectos de implementación sino de **comunicación de la
regla**: el sistema hace una cosa y el material publicado dice otra, o no dice
nada. Ese patrón es lo que justifica que H-2 sea crítica: no es documentación
faltante, es un defecto que se reproduce en cada área del sistema.

Y hay un dato que ordena el resto: el programa devuelve del orden de **0.8% del
consumo en su tasa buena y 0.08% en supermercado y gasolinera.** Las dos cifras
son ilustrativas porque dependen del tipo de cambio que el banco no publica, pero
el orden de magnitud no se mueve.

## Cómo se ve el sistema desde los datos

El banco comunica ocho formas de ganar puntos. Vistas desde los datos colapsan
en **cuatro orígenes**, y esos cuatro no se parecen en nada entre sí:

- El **autorizador de tarjetas** reacciona a un evento por consumo. Por ahí
  entran seis de las ocho vías comerciales.
- El **core de depósitos** no reacciona a un evento sino a un cierre de mes:
  premia mantener saldo, no gastar.
- El **motor de campañas** aplica reglas temporales con vigencia y topes propios,
  y en un caso documentado sustituye la tasa y le cambia la moneda.
- Los **sorteos** acreditan puntos que no se derivan de ningún consumo.

Dos consecuencias que cambian el diseño y no son evidentes desde el folleto:

**La elegibilidad no viaja en la transacción.** Membresía vigente, Bi Móvil
activo, padrón de inscritos y afiliación Mastercard son estados que viven en
otros sistemas. Una acreditación no es función del consumo: es función del
consumo y de cuatro estados externos consultados en ese instante.

**Dos de los cuatro orígenes no se pueden rederivar.** El saldo promedio llega
por lote y sin tasa pública; el sorteo acredita desde un canal externo. Si se
pierde su registro, esos puntos no se pueden recalcular. El resto del sistema sí
es reproducible, y esa asimetría es el corazón de la propuesta técnica.

## Cómo entra DVC

La pregunta es legítima y la respuesta corta es: **entra por el lado de los
pipelines, no por el de los datos.** El desarrollo completo, con siete
alternativas comparadas, está en
[versionado-de-datos.md](versionado-de-datos.md). Lo esencial:

DVC son tres herramientas, no una. Versiona datos, declara pipelines y registra
experimentos, y se pueden adoptar por separado. La decisión es distinta en cada
pilar.

**Versionar los datos aquí sobra.** El dato de CS2 no existe: se genera con un
simulador determinista desde una semilla y una configuración. Si el dataset es
función de la configuración, versionar la configuración ya versiona el dato, y
meter el archivo al repositorio solo agrega peso. Es la lección que CS1 pagó
cuando cinco fotografías resultaron ser el 84% del historial.

**Declarar el pipeline sí aporta**, y aporta tres cosas concretas:

- `poc-parameters.yaml` promete que cuando el cliente responda las preguntas
  abiertas se cambian los valores y el POC vuelve a correr sin tocar código. Hoy
  eso es una intención escrita en un comentario. Con las etapas declaradas, la
  herramienta lo demuestra: cambias el tipo de cambio, corres `dvc repro`, y
  vuelve a ejecutar limpieza y acumulación pero **no** la simulación, porque DVC
  sabe que ese parámetro no la alimenta.
- El grafo del flujo se genera desde el código con `dvc dag`. Un diagrama
  dibujado a mano se desincroniza el primer día que alguien agrega una etapa.
  En un caso cuyo hallazgo crítico es que la documentación de un sistema no
  coincide con el sistema, entregar un diagrama derivado del código es coherente
  con lo que le estamos recomendando al cliente.
- Verifiqué el punto que decidía la compatibilidad: DVC lee parámetros de un
  archivo con nombre propio usando el prefijo `archivo:clave`. Los dos YAML de
  `config/` se quedan donde están, con los nombres que tienen. No hay que partir
  ni renombrar nada.

**Y hay una segunda entrada, que es la que más vale para el cliente.** DVC no es
la respuesta para un banco: el cliente tiene sistemas transaccionales, no un
repositorio con archivos. Pero la lección se traslada directo a dos hallazgos.
H-7 dice que hay puntos que no se pueden reconstruir porque la entrada que los
produjo no quedó guardada. H-4 dice que el tipo de cambio no es público, y hay
algo peor que eso: que no se guarde. Si cada acreditación registra los puntos
resultantes pero no la tasa con la que se convirtió, el saldo no es reproducible
**ni teniendo las reglas en la mano**, y el banco no puede auditar su propio
motor hacia atrás.

De ahí sale una recomendación del tamaño correcto: que cada lote acreditado
guarde los parámetros con los que se acreditó, no solo el resultado. Tipo de
cambio y su fecha, versión de la tabla de rubros, identificador de campaña o
sorteo, estado de elegibilidad consultado. Es un puñado de columnas más en el
ledger y convierte un sistema que hoy solo se puede creer en uno que se puede
verificar. En el vocabulario del curso: es linaje.

## Cómo vamos

| Entregable | Estado | Qué falta |
| --- | --- | --- |
| Investigación y catálogo de evidencia | Terminado | Nada. 850 líneas, 13 preguntas abiertas |
| E-1 Reporte escrito | **Los seis documentos escritos** | Los enlaces profundos de las referencias, y el notebook del cliente |
| E-2 Diagrama de arquitectura | **`.drawio` hecho, más tres en Mermaid** | Exportar a PNG, que es un paso manual. Retirar el PDF viejo cuando el equipo acuerde |
| E-3 Réplica en notebook | Sin empezar | Entorno, motor, simulador, capas, tests, y el notebook |
| E-4 Propuesta de ML o LLM | **Escrita** | Nada. Depende del POC solo para ilustrarse |
| E-5 Diagnóstico y optimización | **Hallazgos y conclusiones escritos** | Las magnitudes que salen del POC |
| Decisiones de herramientas | **Tres documentos con matriz ponderada** | Que respondas D-1 a D-4 |
| Sitio del portafolio | Tarjeta en "Pendiente" | Página de detalle y sus claves de traducción |

Lo que está hecho es la parte que no se puede apurar: la investigación. Lo que
falta es en buena medida transcripción del catálogo y construcción del POC.

Tres cosas que conviene tener presentes porque no se ven en la tabla:

- **El índice de documentación apunta a archivos que no existen.** Se escribió
  como plan, no es documentación perdida. Cada documento que escribimos cierra
  una fila.
- **No hay `pyproject.toml` ni `Makefile`.** Hoy nada de CS2 es reproducible, que
  es justo el problema que le estamos diagnosticando al cliente. Es la deuda que
  hay que pagar antes de la primera celda del notebook.
- **El PDF de arquitectura contradice el catálogo en cuatro puntos.** Dice "tasa
  por tier (14-15 pts/US$10)" cuando la categoría no cambia la tasa sino el tope;
  dice 1595 puntos por el certificado de Q100 cuando son 1615; y presenta como
  hechos el nombre de un sistema interno y un stack de nube que ninguna fuente
  pública confirma. Si el `.drawio` se dibuja copiando el PDF, hereda los cuatro.

## Qué sigue, en orden

El orden no es arbitrario: cada paso desbloquea al siguiente.

1. `01-situacion.md`, `02-reglas-del-programa.md` y `05-referencias.md`. Salen
   del catálogo casi por transcripción.
2. `investigacion-y-supuestos.md`, la bitácora. Cierra las preguntas P-7 a P-11,
   que hoy se citan y no están escritas: el cuestionario al cliente tiene ocho de
   trece.
3. Entorno reproducible y motor del POC. Aquí entra la decisión de DVC.
4. Simulador y las tres capas medallón.
5. Tests, antes del notebook y no después.
6. El notebook de la réplica.
7. Los diagramas y el `.drawio`. Van después del POC a propósito: el código
   revela el flujo real y evita dibujar lo que se supuso.
8. La propuesta de ML, las conclusiones, el notebook del cliente.
9. Página del sitio y merge a `main`.

## Qué necesito que decidas

Tres cosas. Ninguna bloquea el paso 1 ni el 2, así que puedo seguir con el
reporte mientras las piensas.

| # | Decisión | Mi recomendación | Bloquea |
| --- | --- | --- | --- |
| D-1 | ¿Entra DVC, solo como pipeline? | Sí. Si es no, un `Makefile` como CS1 y el plan no cambia | Paso 3 |
| D-2 | ¿Los datos sintéticos se versionan o se regeneran? | Se regeneran, con el hash de cada capa registrado | Paso 3 |
| D-3 | El PDF de José: ¿se redibuja desde cero en draw.io o se corrige? | Redibujar desde el catálogo. Es trabajo de otra persona, así que es conversación de equipo antes que decisión técnica | Paso 7 |

Y una cosa que no es decisión pero sí coordinación: el renombre de la carpeta a
`cs2` mueve la raíz del caso. Quien tenga trabajo sin subir en la ruta vieja debe
subirlo antes de traer el renombre.
