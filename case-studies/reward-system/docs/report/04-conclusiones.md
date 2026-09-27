# 4. Conclusiones

Parte del reporte; el índice está en [README.md](../README.md).

## Lo que se encontró, en cuatro frases

**El programa funciona.** Acumula, expira y canja, lleva años operando con
campañas encima y soporta mecánicas que no son triviales: topes con cuatro
ventanas distintas, padrones de inscritos, acreditación diferida. Nada de lo que
sigue es un reporte de fallos.

**Lo que se degradó es la capacidad de explicarlo.** La regla que decide cuántos
puntos gana un cliente es pública, pero no existe ningún documento que la
enuncie completa. Está repartida en notas al pie de las páginas de producto y
en las bases de promociones viejas. Reconstruirla fue el trabajo de esta
semana.

**Hay decisiones de diseño razonables que se comunican mal.** El corte anual de
vigencia, la penalización de diez a uno en el gasto recurrente y la
no-intercambiabilidad de los puntos son las tres. Ninguna está mal tomada;
las tres están mal contadas.

**Y hay un hueco que no es de comunicación.** La acreditación por sorteo no se
puede reconstruir desde ninguna otra fuente. Es el único punto del sistema donde
un problema de respaldo se convierte en puntos perdidos de clientes reales.

## Qué hacer, en orden

El orden no es por severidad: es por dependencia y por costo. Lo primero que
hay que hacer es lo que desbloquea a lo demás.

### Ahora · Responder seis preguntas

Están listadas al final de
[`config/assumptions.yaml`](../../config/assumptions.yaml). No requieren
proyecto: requieren una reunión con quien opere hoy el motor.

Cuatro de los ocho hallazgos no se pueden dimensionar sin esas respuestas, y
dos de ellas —el tipo de cambio de acumulación (P-3) y el grano del tope
(P-1)— determinan si el saldo de la cartera está bien calculado o no. Mientras
no se respondan, cualquier optimización es afinar un instrumento desafinado.

### Después · Tres cambios que no tocan el motor

Los tres son de comunicación y configuración. Se pueden hacer en paralelo y
ninguno exige tocar el cálculo.

| Cambio | Cierra | Costo |
|---|---|---|
| Mostrar la fecha de vencimiento por lote en lugar de «dos años» | H-3 | Bajo. El dato ya existe |
| Subir la longitud mínima de contraseña del portal de puntos | H-5 | Bajo. Es configuración |
| Sacar la tasa reducida del asterisco y enunciar las dos tasas con el mismo peso | H-6 | Bajo. Es contenido |

El segundo conviene no dejarlo esperando a un proyecto. Cuatro caracteres
protegiendo un activo canjeable es lo más barato de arreglar de toda la lista.

### Luego · Un catálogo de reglas, versionado

Es el cierre de H-2 y la inversión que más rinde a largo plazo, porque es la
que evita que el problema del encargo vuelva a ocurrir.

Una sola fuente donde viva cada regla con su vigencia y su justificación, y que
el motor la lea en vez de tenerla incrustada. El archivo `assumptions.yaml` de
este caso es una primera versión hecha desde fuera; la versión buena se hace
desde dentro, con acceso a lo que el motor realmente aplica.

La prueba de que está bien hecho es simple: ante cualquier saldo, se puede
señalar qué reglas lo produjeron y desde cuándo están vigentes.

### En paralelo · Blindar la vía de sorteos

H-7. Tratar el registro de sorteos como fuente primaria, con el mismo respaldo y
retención que el ledger, y conciliar notificaciones enviadas contra puntos
acreditados. Con 48 horas y un SMS de por medio, esa diferencia no es cero y
hoy nadie sabe de qué tamaño es.

### Cuando lo anterior esté · El desglose del saldo y los modelos

H-1 pide desglosar el saldo por origen en los canales de consulta. Es un cambio
de producto, no de infraestructura, pero solo tiene sentido una vez que se
confirme que el ledger guarda el origen por lote.

Y los tres injertos de ML de la [propuesta](../proposal/ml-ai-llm.md) van al
final por una razón: dos de ellos observan el sistema, y conviene que el sistema
ya esté bien antes de observarlo. El tercero, M1, corrige un cálculo que hoy
puede estar mal, y ese sí adelanta posiciones en cuanto se responda P-3.

## Lo que este equipo haría distinto con una semana más

Tres cosas, en orden de cuánto cambiarían el reporte.

**Medir en lugar de deducir.** Todo lo cuantitativo de este diagnóstico sale de
un POC sobre datos sintéticos. Con acceso a una muestra anonimizada de
transacciones, tres de los ocho hallazgos pasarían de «esto ocurre» a «esto
ocurre en el N% de los casos», que es lo que hace falta para priorizar de
verdad.

**Hablar con operaciones antes que con tecnología.** Las bases de promociones
resultaron ser la fuente más reveladora del diagnóstico, por encima del
reglamento y de la página del programa. Quien redacta esas bases sabe qué
soporta el motor, porque tiene que enunciarlo. Sería la primera entrevista.

**Instrumentar el canje.** Ocho hallazgos y ninguno tiene un número de negocio
detrás, porque no hay forma pública de saber qué proporción de los puntos
emitidos se canja y cuál expira. Ese único número reordenaría las prioridades de
esta lista, y probablemente subiría H-8 varios puestos.

## Una nota sobre el encargo

El enunciado dice que los responsables de diseñar el sistema ya no están en la
empresa, y lo plantea como el obstáculo del trabajo. Después de la semana, la
lectura de este equipo es otra: **eso no es el obstáculo, es el hallazgo.**

Un sistema sobrevive a la salida de su equipo en la medida en que sus reglas
están escritas en algún lugar que no sea el código y la memoria de alguien.
Puntos Bi no lo estaba, y por eso documentarlo exigió una investigación. La
recomendación de fondo, la que engloba a las otras, es que el próximo cambio al
programa no deje al siguiente equipo en la misma posición.
