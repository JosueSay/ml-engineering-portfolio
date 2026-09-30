# Las reglas del programa

Cómo se ganan, se conservan y se pierden los Puntos Bi. Es la reconstrucción en
prosa de [`config/assumptions.yaml`](../../config/assumptions.yaml), que es donde
vive la fuente de cada afirmación.

Cada regla lleva su nivel de confianza: **público** si se cita de una fuente de
Corporación BI, **inferido** si se deduce de algo que sí lo está. Donde no hay
ninguno de los dos, se dice que no es público y se remite a la pregunta abierta
correspondiente. Ninguna regla de este documento es un supuesto del equipo.

**Alcance:** Guatemala, tarjetas y cuentas de persona individual. Quedan fuera las
tarjetas empresariales y las operaciones de Bi Bank Panamá.

## 1. Cómo se ganan puntos

### 1.1 Hay ocho vías, y el consumo con tarjeta es solo una

El programa premia el uso de productos Bi, no solo el consumo. La enumeración más
completa que publica el banco no está en la página del programa: está en las
preguntas frecuentes de Club Bi, que es un programa distinto.

| # | Vía | Qué la dispara | Publica su tasa |
| --- | --- | --- | --- |
| 1 | Tarjetas de crédito y débito **Visa** | Consumo | **Sí** |
| 2 | Tarjetas de **débito Mastercard** | Consumo | No |
| 3 | Tarjetas de **crédito Mastercard** | Consumo, solo si se solicita | No |
| 4 | **Divídelo Todo** | Consumo | No |
| 5 | **Saldo promedio** en tres cuentas de depósito | Cierre de mes | No |
| 6 | **Comercios aliados** | Consumo con Tarjetas Bi en ciertos comercios | No |
| 7 | **Tarjeta Prepago Club Bi** | Consumo en más de 1,000 puntos de venta Visa | No |
| 8 | **Campañas y sorteos** | Promoción vigente | Sí, por campaña |

Confianza: **público**. Una sola de las ocho publica su tasa, y ese es H-2 en su
forma más cruda: no es que el programa esconda sus reglas, es que solo escribió una
de ocho.

### 1.2 La tasa de consumo, y la excepción que importa más

**La tasa base es 1 punto por cada US$1 de compra.** Confianza: público, citado de
las páginas de producto de Tarjetas Bi.

**La excepción es 1 punto por cada US$10** en cinco categorías: supermercados,
gasolineras, tiendas de conveniencia, entidades de beneficencia y centros
educativos. Confianza: público, citado de una nota al pie idéntica en cuatro
páginas de producto.

Es una penalización de diez a uno, y las cinco categorías no son un conjunto
arbitrario: son las de tasa de intercambio regulada o reducida. El programa
traslada su propia economía al cliente, lo cual es legítimo; lo que no lo es es que
esas cinco sean el gasto recurrente típico de una tarjeta y que la regla viva en un
asterisco. Es H-6.

**Hay una conversión de moneda que ninguna fuente describe.** La tasa se enuncia por
dólar y el consumo en Guatemala se liquida en quetzales, así que el motor convierte
antes de aplicar la tasa. Con qué tipo de cambio y de qué fecha no es público.
Confianza: la necesidad de convertir es **inferida**; la ausencia de la política es
una ausencia verificada. Es H-4 y la pregunta P-3.

### 1.3 La categoría de tarjeta no cambia la tasa: cambia el techo

| Categoría | Tope anual |
| --- | --- |
| Mastercard Gold Internacional | 180,000 puntos |
| Visa Premier | 180,000 puntos |
| Visa Signature | 360,000 puntos |
| Visa Infinite | 420,000 puntos |

Confianza: **público**, citado de las páginas de producto.

Es una decisión de diseño distinta de la habitual en la región, donde la categoría
multiplica la tasa. Aquí todos ganan lo mismo por dólar y las categorías altas solo
pueden seguir ganando durante más tiempo antes de topar.

**Las demás categorías no publican tope alguno**: Visa Clásica, Visa Platinum,
Mastercard Standard, Platinum y Black, y las tarjetas de débito. Sus páginas solo
dicen que acumulan puntos canjeables en establecimientos afiliados. Confianza:
ausencia verificada sobre las ocho páginas de producto.

**Y no se sabe a qué se aplica el tope.** Por tarjeta, por cliente o por grupo
familiar unificado son tres respuestas que dan saldos distintos para el mismo
consumo. Es P-1, la primera pregunta del cuestionario al cliente.

### 1.4 Tener dinero guardado también acumula

Es la vía que menos se comunica y la que más cambia la naturaleza del sistema: no
premia gastar, premia **mantener saldo**. Y no reacciona a una transacción sino a un
cierre de mes.

El banco es explícito en que los movimientos no cuentan: "los depósitos a tus
cuentas no acumulan Bi Puntos, acumulas Bi Puntos por los saldos promedio que
mantienes". Depositar y retirar el mismo día no genera nada.

| Cuenta | Saldo promedio mensual desde el que acumula |
| --- | --- |
| Súper Cuenta de Ahorro | más de Q500.00 |
| Súper Cuenta Monetaria | más de Q1,000.00 |
| Cuenta de Ahorro 5 Estrellas | a partir de Q1,000.00 |

Confianza: **público**, cada umbral en la página de su producto.

**La tasa no es pública para ninguna de las tres.** Y el banco agrava el hueco al
reconocer por escrito que no hay una regla sino tres: "Cada Cuenta tiene su propia
Regla de Acumulación". Se sabe desde dónde se empieza a acumular y no cuánto se
acumula, que es justo la mitad que le sirve al cliente para decidir.

Sin esa tasa no se puede responder algo básico: **¿el programa premia gastar o
premia ahorrar?** Es P-2.

**Hay además un multiplicador por membresía.** Pagar la membresía Club Bi duplica
los puntos que genera el saldo. Confianza: público, pero las dos fuentes del emisor
no coinciden en cuál cuenta recibe el doble: las preguntas frecuentes de Club Bi
dicen Súper Cuenta de Ahorros y la página de Bi Puntos dice cuenta monetaria. Es
P-12.

La periodicidad es **inferida**: "saldo promedio" solo tiene sentido sobre un
periodo cerrado, y el ciclo natural de una cuenta de depósito es el mes.

### 1.5 Las vías que el banco nombra sin cuantificar

**Comercios aliados.** Consumir con Tarjetas Bi en ciertos comercios da puntos
adicionales a los de la tarjeta. Es una vía distinta y no una variante del consumo,
porque el premio lo origina el comercio: eso implica un acuerdo comercial y una
regla por comercio dentro del motor. Ninguna fuente publica cuánto, y las tres que
existen no coinciden en la lista. Es P-13.

**Tarjeta Prepago Club Bi.** Acumula en más de 1,000 establecimientos con punto de
venta Visa. Rompe el supuesto de que acumular exige una relación de crédito o una
cuenta de depósito. Tasa no publicada.

**Crédito Mastercard.** No acumula de forma automática: hay que solicitarlo por
agencia o Contact Center. La conversión no se deshace sin emitir una tarjeta nueva,
y excluye la Mastercard UEFA Champions League. Confianza: público.

Aquí hay algo que no es una regla del programa pero afecta a quien quiera usarlo:
las cuatro páginas de producto Mastercard listan exactamente los mismos beneficios
que las Visa **menos** la línea de acumulación de puntos. No dicen que no acumulan,
y tampoco dicen que se puede solicitar. Un cliente que compara productos en el
sitio del banco no tiene forma de enterarse. Ver P-10.

### 1.6 Campañas y sorteos: una capa entera de reglas temporales

Es la parte del sistema que más maquinaria exige y la menos documentada. Tres
mecánicas observadas en bases públicas:

- **Un multiplicador que no multiplica.** Una promoción documentada otorga un punto
  por quetzal, cerca de ocho veces la tasa base. No multiplica la tasa: la
  **sustituye y le cambia la moneda**. El motor tiene que soportar que la unidad de
  la regla cambie, no solo su coeficiente.
- **Una bonificación con padrón de inscritos.**
- **Un sorteo.** Vigencia definida, consumo mínimo de Q100, premios diarios,
  semanales y mensuales de 500 a 50,000 puntos, acreditación 48 horas después de una
  notificación por SMS, exigencia de Bi Móvil activo, y exclusión de empleados de la
  corporación. Acredita puntos que no se derivan de ningún consumo. Es H-7.

Confianza: **público**, de las bases de tres promociones concretas.

### 1.7 Lo que no acumula, y el problema de esa lista

Las dos únicas exclusiones publicadas son **retiros de efectivo** y
**extrafinanciamientos**. Confianza: público, pero con un matiz que importa: están
enunciadas dentro de las bases de una promoción concreta, no como regla general del
programa. El listado completo de exclusiones no es público. Es P-6.

### 1.8 La elegibilidad no viaja en la transacción

Cuatro estados condicionan si una acreditación ocurre, y ninguno es un dato de la
transacción:

- membresía Club Bi vigente, para las promociones que la exigen
- servicio Bi Móvil activo
- inscripción previa al padrón de la promoción
- afiliación Mastercard solicitada

Confianza: **público**. Son predicados que viven en otros sistemas: estado de una
membresía, estado de un servicio digital, pertenencia a un padrón. El motor tiene
que consultarlos en el momento de acreditar, contra sistemas que no son el
autorizador.

La consecuencia es de diseño y no de comunicación: **una acreditación no es función
del consumo.** Es función del consumo y de cuatro estados externos en ese instante,
lo que significa que la misma transacción puede acreditar distinto según cuándo se
procese.

### 1.9 Nada es inmediato

La acreditación tarda **entre 48 y 72 horas hábiles**. Confianza: público, citado de
las preguntas frecuentes del portal.

Eso descarta la lectura intuitiva de un motor que reacciona a cada autorización y
confirma que la acumulación se resuelve por lotes. Para el cliente, 48 a 72 horas
hábiles pueden ser una semana de calendario.

## 2. Cómo se conservan

### 2.1 La vigencia es un corte anual, no una duración

La regla publicada es: "Los Bi Puntos tienen una vigencia de dos años y vencen el 5
de febrero de cada año los acumulados dos años antes". Confianza: público.

Las dos mitades de esa frase no dicen lo mismo. La primera describe un vencimiento
rodante por punto; la segunda, un corte anual en fecha fija por año de acumulación.
Es la segunda la que gobierna, y por eso la vigencia efectiva va de 13 a 25 meses
según el mes en que se ganó el punto. Es H-3.

**Al canjear, qué lote se consume primero no es público.** Con un corte anual fijo,
el orden es dinero del cliente. Es P-4.

### 2.2 El saldo pertenece a un grupo, no a una persona

Existe la unificación familiar: el traslado total de los puntos de varias personas a
un solo saldo. Confianza: público.

- Parentescos admitidos: padre, madre, hermanos y cónyuge, este último comprobado
  con acta matrimonial.
- La unificación debe permanecer como mínimo un año.
- **Solo el titular de la unificación puede canjear.**

Esa última línea tiene una consecuencia analítica que conviene subrayar: cualquier
análisis por cliente cuenta puntos que ese cliente no puede canjear. El grano real
del saldo es el grupo.

Nota: exigir acta matrimonial deja fuera la unión de hecho, figura reconocida por la
legislación guatemalteca. Es una decisión de política del programa, no un defecto
del sistema, y se registra sin calificarla.

## 3. Cómo se usan y cómo se pierden

### 3.1 Seis canales muestran el saldo

App Club Bi, Bi en Línea web, el portal de puntos, los centros de canje, el PBX
1717 y el estado de cuenta Bi Puntos. Confianza: público.

Los seis muestran un número único.

### 3.2 Tres canales lo ejecutan, y dos no están documentados

| Canal | Alcance | Confianza |
| --- | --- | --- |
| Centros de canje, presencial | Todo el catálogo | Público y documentado |
| Portal de puntos, en línea | No publicado | Existe; el alcance es P-8 |
| PBX 1717, telefónico | Conversión a millas | Público, en el portal de millas |

El presencial exige Tarjeta Club Bi física y documento de identificación. Para un
tercero hacen falta carta de autorización firmada por el titular, copia de su
documento y la tarjeta física; para una empresa, documento del representante legal,
nombramiento y la tarjeta.

El problema no es que haya un solo canal: es que hay tres y el cliente conoce uno.
Es H-8.

### 3.3 Qué vale un punto

**1,615 puntos equivalen a un certificado de regalo de Q100**, es decir Q0.0619 por
punto. Confianza: público, leído el 22 de septiembre de 2026 en la portada del
portal.

Es el único valor monetario del punto en todo el caso. Y trae advertencia de
vigencia: el catálogo de premios cambia, y hay que releer esta cifra antes de
reutilizarla.

Expresar el retorno como porcentaje del consumo exige el tipo de cambio, que no es
público, así que cualquier porcentaje es ilustración y no dato. Con un tipo de
cambio de referencia, el orden de magnitud es **0.8% del consumo a tasa base y
0.08% en las cinco categorías reducidas**.

### 3.4 La conversión a millas: el hallazgo central

El socio es LifeMiles, el canje se pide por el 1717, y la conversión "puede variar
según el producto con el que acumules Bi Puntos". Confianza: público.

**Cuánto varía no es público.** Es P-5.

Si el valor de canje depende del producto que generó el punto, entonces los puntos
no son intercambiables entre sí, y el número único que muestran los seis canales de
consulta no alcanza para decidir un canje. Es H-1, y su consecuencia técnica es más
profunda que la comercial: el origen es parte del dato, así que el saldo no se puede
representar como un entero.

### 3.5 Hay más de 50 comercios afiliados

Confianza: público.

## 4. Cuánto cuesta participar

**Acumular y canjear no cuesta nada.** Confianza: público, citado de las preguntas
frecuentes del portal: el programa de Bi Puntos "es ajeno al Programa de beneficios
que otorga Club Bi al pagar tu membresía".

**La membresía Club Bi cuesta Q15.00 mensuales**, Q180 al año, y corresponde al
programa de beneficios y descuentos. Confianza: público.

Tres matices que sí se sostienen:

- La Tarjeta Club Bi física es obligatoria para canjear, porque "en ella se
  depositan todos tus Bi Puntos".
- Varias promociones exigen membresía vigente.
- La membresía duplica los puntos del saldo promedio, así que compra un
  multiplicador permanente sobre una vía de acumulación y no solo acceso a
  promociones.

La pregunta económica deja de ser "vale la pena pagar Q180 al año por descuentos" y
pasa a ser "vale la pena por descuentos más el doble de puntos sobre el saldo
promedio", que no se puede responder porque la tasa base de esa vía no es pública.

## 5. Identidad y acceso

El portal de puntos tiene alta de usuario y recuperación de contraseña **propias**,
distintas de las de Bi en Línea. Confianza: público.

Exige mayúsculas, minúsculas, números y caracteres especiales, y a la vez admite un
mínimo de **cuatro caracteres**. Confianza: público. Es H-5.

## 6. Las reglas en una tabla

| Regla | Valor | Confianza |
| --- | --- | --- |
| Tasa base | 1 punto por US$1 | Público |
| Tasa en cinco categorías | 1 punto por US$10 | Público |
| Denominación | Dólar, con consumo en quetzales | Inferido |
| Tipo de cambio | No publicado | Ausencia verificada |
| Topes anuales | 180,000 a 420,000 en cuatro categorías | Público |
| Topes en las otras seis categorías | No publicados | Ausencia verificada |
| Grano del tope | Desconocido | P-1 |
| Umbrales de saldo promedio | Q500, Q1,000 y Q1,000 | Público |
| Tasa por saldo promedio | No publicada, y son tres reglas | P-2 |
| Multiplicador por membresía | 2x, sobre cuál cuenta se contradice | P-12 |
| Latencia de acreditación | 48 a 72 horas hábiles | Público |
| Vigencia | Corte el 5 de febrero, 13 a 25 meses efectivos | Público |
| Orden de consumo de lotes | Desconocido | P-4 |
| Unificación familiar | Solo el titular canjea, mínimo un año | Público |
| Valor del punto | 1,615 puntos por Q100 | Público, con vigencia |
| Conversión a millas | Varía por producto, tasa no publicada | P-5 |
| Exclusiones | Retiros y extrafinanciamientos, lista incompleta | P-6 |
| Costo de participar | Gratuito | Público |
| Membresía Club Bi | Q15 mensuales, otro programa | Público |
| Longitud mínima de contraseña | 4 caracteres | Público |
