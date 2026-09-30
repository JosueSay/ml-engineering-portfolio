# Hallazgos

Los ocho hallazgos del diagnóstico del sistema de puntos Club Bi, con su
evidencia y su severidad. Es el documento central del reporte: las
conclusiones de [04-conclusiones.md](04-conclusiones.md) salen de aquí, y cada
afirmación se puede rastrear hasta
[`config/assumptions.yaml`](../../config/assumptions.yaml), que a su vez cita la
fuente pública en [05-referencias.md](05-referencias.md).

Ninguno de los ocho es una opinión sobre cómo debería funcionar el programa.
Todos son cosas que el sistema hace, o que no dice, verificadas contra lo que
Corporación BI publica.

## Cómo se asignó la severidad

La severidad responde a una sola pregunta: **qué cuesta convivir con el
hallazgo**. No mide qué tan difícil es arreglarlo.

| Severidad | Criterio |
| --- | --- |
| **Crítica** | Afecta el saldo de todos los clientes, o expone el sistema a un tercero. No hay forma de convivir con ella |
| **Alta** | Le cuesta puntos al cliente, o cambia una decisión que el cliente toma con información incompleta |
| **Media** | No daña al cliente hoy, pero limita la operación, la auditoría o el uso de algo que ya está construido |

Se declara además el nivel de confianza de la evidencia, con la misma escala
que gobierna todo el caso: **público** si se cita de una fuente de Corporación
BI, **inferido** si se deduce de algo que sí lo está.

## Resumen

| ID | Hallazgo | Severidad | Evidencia |
| --- | --- | --- | --- |
| [H-2](#h-2-la-regla-que-gobierna-el-sistema-no-está-escrita-en-ningún-lado) | La regla que gobierna el sistema no está escrita en ningún lado | Crítica | Público |
| [H-4](#h-4-la-regla-está-en-dólares-el-consumo-en-quetzales-y-el-tipo-de-cambio-no-es-público) | La regla está en dólares, el consumo en quetzales y el tipo de cambio no es público | Crítica | Inferido |
| [H-5](#h-5-el-portal-de-puntos-admite-contraseñas-de-cuatro-caracteres) | El portal de puntos admite contraseñas de cuatro caracteres | Crítica | Público |
| [H-1](#h-1-los-puntos-no-son-intercambiables-entre-sí-y-el-saldo-se-muestra-como-si-lo-fueran) | Los puntos no son intercambiables entre sí, y el saldo se muestra como si lo fueran | Alta | Público |
| [H-3](#h-3-la-vigencia-efectiva-va-de-13-a-25-meses-y-se-comunica-como-dos-años) | La vigencia efectiva va de 13 a 25 meses y se comunica como dos años | Alta | Público |
| [H-6](#h-6-la-penalización-de-diez-a-uno-cae-sobre-el-gasto-recurrente-y-se-comunica-en-un-asterisco) | La penalización de diez a uno cae sobre el gasto recurrente y se comunica en un asterisco | Alta | Público |
| [H-7](#h-7-hay-una-vía-de-acreditación-que-no-se-puede-reconstruir) | Hay una vía de acreditación que no se puede reconstruir | Media | Público |
| [H-8](#h-8-hay-tres-canales-de-canje-y-el-cliente-solo-conoce-uno) | Hay tres canales de canje y el cliente solo conoce uno | Media | Público |

El reparto ya es un resultado. Siete de los ocho se sostienen sobre fuentes
públicas del propio emisor: no hacía falta acceso al sistema para encontrarlos,
solo leer con cuidado lo que el banco ya publica. Y tres de los ocho no son
defectos de implementación sino de **comunicación de la regla**: el sistema hace
una cosa y el material publicado dice otra, o no dice nada.

## H-2. La regla que gobierna el sistema no está escrita en ningún lado

**Severidad: crítica. Evidencia: pública.**

No existe ninguna fuente, del banco ni de nadie, que enuncie la regla de
acumulación completa de una sola vez. La regla existe, es pública y funciona;
lo que no existe es el documento.

La tasa base vive en las páginas de producto de cada tarjeta, enunciada producto
por producto:

> acumulas Puntos Bi por cada dólar de compra

La excepción vive en una nota al pie con asterisco, idéntica en cuatro páginas
de tarjeta distintas:

> \*Por cada 10 dólares de compra en supermercados, gasolineras, tiendas de
> conveniencia, entidades de beneficencia y centros educativos acumulas 1 punto.

La página del programa no menciona ninguna de las dos. Reconstruir la regla
completa exigió cruzar cuatro páginas de producto, las preguntas frecuentes de
Club Bi, el portal de puntos, una infografía de blog y las bases de tres
promociones.

El hallazgo tiene cuatro manifestaciones independientes, y es lo que lo hace
crítico en vez de anecdótico:

- **De las ocho vías de acumulación, una sola publica su tasa.** La de tarjetas
  Visa. Las otras siete —débito Mastercard, crédito Mastercard afiliada,
  Divídelo Todo, saldo promedio, comercios aliados, prepago y campañas— acreditan
  puntos sin que ninguna fuente diga cuántos.
- **La única vía sin tasa pública en ninguna parte es la de saldo promedio**, y
  el banco reconoce por escrito que ahí no hay una regla sino tres, una por tipo
  de cuenta, sin publicar ninguna: *"Cada Cuenta tiene su propia Regla de
  Acumulación"*. Se sabe desde qué saldo se empieza a acumular y no se sabe
  cuánto se acumula, que es justo la mitad que le sirve al cliente.
- **Cuatro categorías de tarjeta publican su tope anual y el resto no.** Visa
  Clásica, Visa Platinum, Mastercard Standard, Platinum y Black, y las tarjetas
  de débito solo dicen que acumulan. Es una ausencia verificada, no una búsqueda
  incompleta.
- **Dos fuentes del mismo emisor se contradicen sobre un multiplicador de dos.**
  Las preguntas frecuentes de Club Bi dicen que la membresía da dobles puntos en
  la Súper Cuenta de Ahorros; la página de Bi Puntos dice que es con la cuenta
  monetaria. Un cliente que paga la membresía para duplicar sus puntos no puede
  saber en cuál de sus cuentas conviene dejar el saldo.

**Por qué importa.** Es la causa raíz del encargo. Si los responsables del
diseño se van y la regla no está escrita, el conocimiento se va con ellos: es
exactamente la situación que este diagnóstico vino a atender. Mientras la regla
viva repartida en notas al pie, cualquier cambio al programa es un cambio a
ciegas, y cada equipo que herede el sistema va a repetir el trabajo de
reconstruirla.

**Qué haría falta para cerrarlo.** Un documento único de reglas del programa,
versionado, del que salgan las páginas de producto en vez de al revés. No es
una decisión de negocio: es la que menos negociación necesita de las ocho.

**Preguntas abiertas relacionadas:** P-2, P-6, P-12, P-13.

## H-4. La regla está en dólares, el consumo en quetzales y el tipo de cambio no es público

**Severidad: crítica. Evidencia: inferida, con la ausencia verificada.**

La tasa se enuncia por dólar de compra. El consumo en Guatemala se liquida en
quetzales. El motor tiene que convertir moneda antes de aplicar la tasa, y
ninguna fuente pública dice con qué tipo de cambio ni de qué fecha: el de la
autorización, el del cierre del ciclo o uno institucional fijo.

**Por qué importa.** Es el parámetro del que cuelga el saldo entero. No afecta a
un subconjunto de clientes ni a un tipo de transacción: multiplica cada consumo
de cada cliente. A la tasa base, la diferencia entre dos tipos de cambio
razonables mueve los puntos de todos, y el cliente no tiene forma de verificar
su propio saldo porque no sabe con qué se convirtió.

Y hay un efecto de segundo orden que importa más de lo que parece: cualquier
intento de expresar el retorno del programa como porcentaje del consumo —lo que
haría falta para compararlo con cualquier otro programa de lealtad de la
región— depende de este número. Sin él, ni el banco ni el cliente pueden decir
cuánto devuelve el programa.

**Qué haría falta para cerrarlo.** Publicar la política de conversión. Es una
línea de texto, y convierte un supuesto en un dato verificable por el cliente.

**Preguntas abiertas relacionadas:** P-3.

## H-5. El portal de puntos admite contraseñas de cuatro caracteres

**Severidad: crítica. Evidencia: pública.**

El portal `bipuntos.bi.com.gt` tiene alta de usuario y recuperación de
contraseña propias, distintas de las de Bi en Línea. Exige mayúsculas,
minúsculas, números y caracteres especiales, y a la vez admite un mínimo de
**cuatro caracteres**.

**Por qué importa.** La composición obligatoria no compensa la longitud, y aquí
juega en contra: con cuatro posiciones, obligar a que aparezcan cuatro clases
distintas fuerza a que cada posición sea de una clase distinta, lo que **reduce**
el conjunto de contraseñas válidas en vez de ampliarlo. El requisito que parece
endurecer la contraseña la debilita.

Lo que hay detrás de esa contraseña no es un perfil: es saldo canjeable por
bienes, y el portal ofrece canje en línea. Además es una superficie de
autenticación **separada** de la banca en línea, lo que significa que el
endurecimiento que se haya hecho en Bi en Línea no protege aquí.

**Qué haría falta para cerrarlo.** Es el único de los ocho que se arregla sin
decidir nada de negocio, sin preguntarle al cliente y sin tocar el motor de
puntos: subir el mínimo de longitud. Por eso es el primero de la lista de
acciones, aunque no sea el de mayor impacto económico.

**Preguntas abiertas relacionadas:** ninguna. No hace falta preguntar nada para
actuar.

## H-1. Los puntos no son intercambiables entre sí, y el saldo se muestra como si lo fueran

**Severidad: alta. Evidencia: pública.**

El portal de millas declara que la conversión a LifeMiles

> puede variar según el producto con el que acumules Bi Puntos

Es decir: dos puntos con el mismo número en el mismo saldo pueden comprar
cantidades distintas de millas según qué producto los generó. La tasa concreta
por producto no es pública.

Al mismo tiempo, **seis canales muestran el saldo** —App Club Bi, Bi en Línea
web, el portal de puntos, los centros de canje, el PBX 1717 y el estado de
cuenta— y los seis muestran un número único.

**Por qué importa.** Un número único sobre un saldo que no es homogéneo no
alcanza para decidir un canje. Dos clientes con 50,000 puntos no tienen el mismo
poder de compra si uno los acumuló con crédito Visa y el otro con saldo
promedio, y ninguno de los dos puede saberlo desde ninguno de los seis canales.

La consecuencia técnica es más profunda que la comercial: si el valor de canje
depende del origen, entonces **el origen es parte del dato** y el saldo no se
puede representar como un entero. Tiene que ser un conjunto de lotes con
procedencia, y eso cambia el modelo de datos del ledger, no solo la pantalla.

Sobre la magnitud: el punto tiene un valor monetario público en el catálogo de
premios —1,615 puntos por un certificado de regalo de Q100, leído el 22 de
septiembre de 2026— pero las tasas de millas por producto no lo tienen. Así que
de este hallazgo se puede afirmar la forma y no la magnitud, y ningún entregable
del caso reporta magnitud.

**Qué haría falta para cerrarlo.** Dos cosas distintas: publicar las tasas por
producto, y mostrar el saldo desglosado por origen en los canales de consulta.
La segunda no se puede hacer sin la primera.

**Preguntas abiertas relacionadas:** P-5, P-1.

## H-3. La vigencia efectiva va de 13 a 25 meses y se comunica como dos años

**Severidad: alta. Evidencia: pública.**

La regla publicada es:

> Los Bi Puntos tienen una vigencia de dos años y vencen el 5 de febrero de cada
> año los acumulados dos años antes.

Las dos mitades de esa frase no dicen lo mismo. La primera describe un
vencimiento rodante por punto; la segunda describe un **corte anual en fecha
fija por año de acumulación**. Es la segunda la que gobierna.

La consecuencia aritmética es directa: un punto ganado en enero vence 25 meses
después, y un punto ganado en diciembre del mismo año vence 13 meses después.
Los dos se comunican como "dos años".

| Punto ganado el | Vence el | Vigencia efectiva |
| --- | --- | --- |
| 2 de enero de 2024 | 5 de febrero de 2026 | 25 meses |
| 15 de junio de 2024 | 5 de febrero de 2026 | 20 meses |
| 30 de diciembre de 2024 | 5 de febrero de 2026 | 13 meses |

La vigencia se mide desde el día de la transacción, no desde el mes: es lo que
hace que el extremo inferior sea 13 y no 14. Los tres puntos de la tabla vencen
el mismo día porque se acumularon el mismo año, que es el único criterio que el
corte usa.

**Por qué importa.** La diferencia es de casi el doble, y cae sobre el cliente
sin que pueda anticiparla desde la regla publicada. Un cliente que planifica un
canje contando con dos años de vigencia puede perder puntos que creía vigentes
once meses más.

Hay un agravante que no se puede medir desde fuera: al canjear, no se sabe qué
lote se consume primero. Con un corte anual fijo, el orden es dinero. Si se
consumen primero los puntos más nuevos, un cliente que canjea con regularidad
puede aun así perder el lote viejo entero, sin haber dejado de usar el programa
ni un mes.

**Qué haría falta para cerrarlo.** Comunicar la vigencia como lo que es —una
fecha de vencimiento por lote, visible en el saldo— en vez de como una duración
uniforme. El sistema ya tiene que conocer la fecha de cada lote para poder
vencerlo, así que el dato existe; lo que falta es mostrarlo.

**Preguntas abiertas relacionadas:** P-4.

## H-6. La penalización de diez a uno cae sobre el gasto recurrente y se comunica en un asterisco

**Severidad: alta. Evidencia: pública.**

La tasa base es 1 punto por US$1. En cinco categorías es 1 punto por US$10: una
penalización de diez a uno. Las cinco categorías son supermercados, gasolineras,
tiendas de conveniencia, entidades de beneficencia y centros educativos.

Esas cinco no son un conjunto arbitrario. Son las categorías con tasa de
intercambio regulada o reducida: el programa **traslada su propia economía al
cliente**, lo cual es una decisión legítima. Lo que no es legítimo es cómo se
comunica, porque son también el gasto recurrente típico de una tarjeta. La regla
con más impacto sobre el saldo de un cliente promedio es la que vive en la nota
al pie.

Sobre la magnitud, con la aritmética del propio programa: a Q0.0619 por punto
—el valor del certificado de regalo, que es público— y a un tipo de cambio de
referencia de 7.70, el retorno queda en el orden de **0.8% del consumo a tasa
base y 0.08% en las cinco categorías**. Las dos cifras son ilustrativas y no
datos del sistema, porque el tipo de cambio de acumulación no es público (H-4);
pero mover el tipo de cambio dentro de un rango razonable no cambia el orden de
magnitud. El programa devuelve menos del uno por ciento en su tasa buena, y
menos de una décima de punto porcentual en supermercado y gasolinera.

**Por qué importa.** Un cliente que usa la tarjeta principalmente en
supermercado y gasolinera —el caso más común— está en un programa que le
devuelve una décima parte de lo que cree. La asimetría entre el impacto de la
regla y la prominencia con que se publica es el hallazgo, no la tasa en sí.

Hay además un riesgo operativo del lado del motor: la decisión de qué tasa
aplicar depende de clasificar el comercio, y esa clasificación no es parte de la
regla publicada. Un comercio clasificado en la categoría equivocada acumula la
décima parte, o diez veces más. El mapa de códigos de rubro importa tanto como
la tasa, y no es público.

**Qué haría falta para cerrarlo.** Publicar la tasa reducida con la misma
prominencia que la base, en la página del programa y no en una nota al pie de
las páginas de producto. Si además se quiere mejorar el programa y no solo su
comunicación, es aquí donde se decide.

**Preguntas abiertas relacionadas:** P-3 para la magnitud, P-13 para el efecto
de los comercios aliados sobre la misma tasa.

## H-7. Hay una vía de acreditación que no se puede reconstruir

**Severidad: media. Evidencia: pública.**

Los sorteos acreditan puntos que no se derivan de ningún consumo. La mecánica
documentada, de una promoción con bases públicas, acredita 48 horas después de
una notificación por SMS, con premios de 500 a 50,000 puntos y ganadores
diarios, semanales y mensuales.

Una aclaración importante, porque es donde el diagnóstico se corrigió a sí
mismo: **el retardo no es el hallazgo**. Ninguna vía del sistema es síncrona. El
banco publica que la acreditación tarda entre 48 y 72 horas hábiles en todos los
casos, lo que descarta la lectura intuitiva de un motor que reacciona a cada
autorización y confirma que la acumulación se resuelve por lotes. El retardo de
48 horas del sorteo no lo distingue de nada.

Lo que lo distingue es que **no se puede rederivar**. Todo el resto del sistema
es reproducible: dado el registro de transacciones y las reglas, los puntos se
pueden volver a calcular. Los puntos de un sorteo no: se originan en un canal
externo, no son función de ningún dato del cliente, y si su registro se pierde
no hay nada desde donde reconstruirlos.

**Por qué importa.** Es un punto ciego de auditoría en un sistema que por lo
demás es auditable. No le cuesta puntos al cliente hoy, y por eso es media y no
alta; pero es la única parte del saldo que no tiene una segunda fuente de
verdad. Un cliente que reclama que le faltan puntos de sorteo no tiene forma de
demostrarlo, y el banco no tiene forma de verificarlo.

La vía de saldo promedio tiene una versión más leve del mismo problema: llega
por lote mensual y su tasa no es pública, así que hoy tampoco se puede rederivar
desde fuera. La diferencia es que ahí el dato de origen existe y es la tasa la
que falta; en el sorteo no hay dato de origen.

**Qué haría falta para cerrarlo.** Que la acreditación por sorteo deje un
asiento con su propia trazabilidad —identificador del sorteo, del premio y de
la notificación— de modo que el punto tenga una procedencia verificable aunque
no sea derivable.

**Preguntas abiertas relacionadas:** P-2 para la vía de saldo promedio.

## H-8. Hay tres canales de canje y el cliente solo conoce uno

**Severidad: media. Evidencia: pública.**

Toda la documentación pública describe el mostrador:

> Visita un centro de canje y presenta tu Tarjeta Club Bi física y tu documento
> de identificación.

Pero existen tres canales de ejecución, y dos no están documentados:

| Canal | Alcance | Cómo se supo |
| --- | --- | --- |
| Centros de canje, presencial | Todo el catálogo | Documentado |
| Portal de puntos, en línea | No publicado | Por la entrada de menú "Canje en línea" y el aviso de que hay que iniciar sesión para canjear |
| PBX 1717, telefónico | Conversión a millas | Por el portal de millas: "Para canjear tus puntos llama al 1717" |

El canje en línea existe —el portal tiene la funcionalidad y el aviso— y
ninguna fuente dice qué parte del catálogo admite.

**Por qué importa.** No es un daño al cliente, es capacidad construida que nadie
usa. El banco pagó por desarrollar un canje en línea y lo comunica como si solo
existiera el mostrador, que es además el canal más caro de operar y el que exige
que el cliente se presente con tarjeta física y documento de identificación.

Es otra manifestación de H-2 en un dominio distinto: la regla que gobierna una
funcionalidad **que ya existe y funciona** no está escrita. Ahí está el patrón
del caso, y es lo que justifica la severidad crítica de H-2: no es un problema de
documentación faltante, es un problema que se reproduce en cada área del sistema.

**Qué haría falta para cerrarlo.** Documentar el alcance de cada canal. Y si el
canje en línea cubre todo el catálogo, decirlo es probablemente la mejora de
costo operativo más barata del programa.

**Preguntas abiertas relacionadas:** P-8, en
[investigacion-y-supuestos.md](../investigacion-y-supuestos.md).

## Qué no quedó como hallazgo, y por qué

Tres cosas que aparecieron en la investigación y no tienen número propio. Se
registran aquí para que no se lean como omisiones.

**Las contradicciones entre fuentes del mismo emisor** —el multiplicador de la
membresía, y las tres listas distintas de comercios aliados— quedaron dentro de
H-2. No son hallazgos independientes: son el mismo defecto de comunicación de la
regla, visto en dos lugares más. Contarlas por separado inflaría el número de
hallazgos sin agregar nada que el cliente pueda accionar por separado.

**Que la elegibilidad no viaje en la transacción** —membresía vigente, Bi Móvil
activo, padrón de inscritos y afiliación Mastercard son estados que viven en
otros sistemas y que el motor tiene que consultar en el instante de acreditar—
es una observación de arquitectura, no un defecto. Explica por qué una
acreditación no es función solo del consumo, y por eso vive en
[architecture/README.md](../architecture/README.md) y no aquí.

**Que la unificación familiar acredite al cónyuge con acta matrimonial** deja
fuera la unión de hecho, figura reconocida por la legislación guatemalteca. Es un
criterio de elegibilidad discutible, pero es una decisión de política del
programa y no un defecto del sistema, y calificarlo excede lo que un diagnóstico
técnico puede sostener con evidencia pública. Queda registrado en el catálogo de
reglas.
