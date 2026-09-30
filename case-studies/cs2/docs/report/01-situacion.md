# Resumen de la situación

Qué pidió el cliente, con qué se contaba al empezar, y cómo se levantó un
diagnóstico de un sistema al que no hay acceso.

## El encargo

Corporación BI quiere optimizar Puntos Bi, su programa de lealtad. El encargo
incluye una restricción que no es un detalle administrativo sino la condición que
define todo el trabajo:

> Los responsables de diseñar e implementar el sistema ya no trabajan en la
> empresa.

No hay documentación interna, no hay a quién preguntarle y no hay acceso al
sistema. Eso invierte el orden natural del trabajo. No se puede empezar
proponiendo optimizaciones, porque no se sabe qué se estaría optimizando. Hay que
empezar estableciendo **qué hace el sistema**.

De ahí salen cinco entregables:

| # | Entregable | Dónde está |
| --- | --- | --- |
| E-1 | Reporte con hallazgos y documentación del sistema | Este reporte, y el notebook del cliente |
| E-2 | Diagrama de la arquitectura de datos | [`architecture/`](../architecture/README.md) |
| E-3 | Réplica en miniatura de la arquitectura | `notebooks/` |
| E-4 | Propuesta para integrar ML, IA o LLM en el pipeline | [`proposal/ml-ai-llm.md`](../proposal/ml-ai-llm.md) |
| E-5 | Diagnóstico y propuestas de optimización | [03-hallazgos.md](03-hallazgos.md) y [04-conclusiones.md](04-conclusiones.md) |

## Qué se sabía al empezar

Nada verificado. El equipo tenía la misma información que cualquier cliente del
banco: que existe un programa de puntos, que la tarjeta los acumula y que se
canjean por premios.

Vale registrar que el equipo **empezó con dos ideas equivocadas**, porque cómo se
descubrieron es la mejor descripción del método:

- Se creyó que participar en el programa de puntos costaba Q180 al año. Es falso,
  y el banco publica lo contrario: acumular y canjear no cuesta nada. Son dos
  programas distintos que comparten nombre comercial, tarjeta física y usuario del
  portal. La membresía de Q15 mensuales es del programa de beneficios y descuentos.
- Se creyó que había un solo canal de canje, el presencial. Hay tres, y dos no
  están documentados.

Las dos ideas venían de leer el material comercial como si fuera un manual. Se
corrigieron al cruzar fuentes en lugar de aceptar la primera. Las dos correcciones,
con su fecha y su fuente, están en la bitácora
[`investigacion-y-supuestos.md`](../investigacion-y-supuestos.md).

## Cómo se levantó el diagnóstico

Tres rondas de investigación sobre fuentes públicas de Corporación BI: ocho páginas
de producto de tarjetas, tres de cuentas de depósito, el portal de puntos, el
portal de millas, las preguntas frecuentes de dos programas distintos, la página de
Club Bi, las bases de tres promociones y una infografía del blog corporativo. El
inventario completo, con qué aportó cada una, está en
[05-referencias.md](05-referencias.md).

Sobre eso se construyó el artefacto central del caso:
[`config/assumptions.yaml`](../../config/assumptions.yaml), un catálogo donde cada
regla declara tres cosas.

| Campo | Qué dice |
| --- | --- |
| `valor` | La regla |
| `confianza` | `publico`, `inferido` o `supuesto` |
| `fuente` | Dónde se verifica, o por qué se eligió |

Tres reglas de trabajo gobiernan el catálogo y, por lo tanto, todo el reporte.

**Nada se afirma sin nivel de confianza.** Es la única forma de que el cliente
pueda separar lo que su propio banco ya publica de lo que este equipo dedujo. Un
diagnóstico donde las dos cosas se mezclan obliga al cliente a verificarlo entero
o a creerlo entero.

**La ausencia de información es información.** Cuando una fuente no dice algo que
debería decir, se registra como ausencia verificada, con la fuente donde se buscó.
Eso permite afirmar que cuatro categorías de tarjeta publican su tope anual y el
resto no, en vez de insinuarlo.

**Lo que no se sabe se convierte en pregunta, no en supuesto conveniente.** Hay
trece preguntas abiertas y son parte de la entrega. Un diagnóstico que rellena sus
huecos con estimaciones plausibles le traslada el riesgo al cliente sin avisarle.

De esa tercera regla sale una decisión de diseño que conviene explicar, porque el
cliente la va a ver en el repositorio: **hay dos archivos de configuración, no
uno.** `assumptions.yaml` documenta el sistema y se detiene cuando algo no es
público. [`config/poc-parameters.yaml`](../../config/poc-parameters.yaml) tiene los
números que el código necesita para poder ejecutarse, y cada uno declara qué
pregunta abierta está sustituyendo. Así el catálogo de evidencia no se contamina, y
cualquier cifra del notebook que dependa de un supuesto lo dice en la propia tabla.

## Alcance

**Dentro:** Guatemala, tarjetas y cuentas de persona individual.

**Fuera:** las tarjetas empresariales y las operaciones de Bi Bank Panamá, que
tienen sus propias condiciones y no se revisaron.

**Fuera también, y es la limitación de fondo:** cualquier afirmación sobre la
implementación. No se puede saber qué base de datos usa el motor, en qué lenguaje
está escrito ni sobre qué infraestructura corre. El diagnóstico describe **qué hace
el sistema y qué estructura de datos exige lo que hace**, no cómo está construido.
Es una distinción que el borrador inicial del diagrama de arquitectura no respetaba,
y se corrigió.

## Qué no se puede responder desde fuera

Trece preguntas, ordenadas por cuánto cambia la respuesta el resto del
diagnóstico. Las seis primeras están en el catálogo; las demás en la bitácora. Las
cuatro que más consecuencias tienen:

- **¿El tope anual se aplica por tarjeta, por cliente o por grupo familiar?** Las
  tres respuestas dan saldos distintos para el mismo consumo, y cambian el modelo
  de datos del acumulador.
- **¿Cuál es la tasa de acumulación por saldo promedio?** Es el único mecanismo sin
  cifra pública. Sin él no se puede saber si el programa premia gastar o ahorrar.
- **¿Con qué tipo de cambio, y de qué fecha, se convierte el consumo a dólares?**
  Mueve el saldo de todos los clientes en todas las transacciones.
- **¿Al canjear, qué lote de puntos se consume primero?** Con un corte anual fijo,
  el orden decide cuántos puntos pierde un cliente que canjea con regularidad.

El POC no las responde: **muestra cuánto cambia el resultado según la respuesta.**
Esa es la única forma honesta de reportar sobre un sistema cuyos parámetros no se
conocen, y convierte cada pregunta abierta en un argumento para que el cliente la
conteste.

## Cómo leer este reporte

- [02-reglas-del-programa.md](02-reglas-del-programa.md) — qué hace el sistema,
  en prosa
- [03-hallazgos.md](03-hallazgos.md) — los ocho hallazgos, con severidad y
  evidencia
- [04-conclusiones.md](04-conclusiones.md) — qué hacer, en qué orden y por qué
- [05-referencias.md](05-referencias.md) — cada fuente y qué aportó

Quien quiera verificar una regla concreta puede ir directo al catálogo: cada
entrada trae su fuente.
