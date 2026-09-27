# 2. Cómo se ganan, se conservan y se pierden los puntos

Parte del reporte; el índice está en [README.md](../README.md).

Este documento es la reconstrucción en prosa del sistema. El catálogo
estructurado, con la fuente exacta de cada regla, está en
[`config/assumptions.yaml`](../../config/assumptions.yaml). Cuando aquí se dice
«público», ahí está la cita.

---

## 2.1 Cómo se acumula

Hay dos preguntas que se confunden todo el tiempo: **con qué
productos** se ganan puntos, y **por qué tubería** entran esos puntos al
sistema. La primera es comercial y tiene ocho respuestas; la segunda es técnica
y tiene cuatro.

### Los ocho productos que acumulan

La enumeración más completa que publica el banco está en las preguntas
frecuentes de Club Bi:

> ***¿Cómo acumulas Puntos Bi?** Utilizando las tarjetas de crédito y débito
> Visa, tarjetas débito MasterCard, Saldo promedio en Super Cuenta Monetaria y
> Ahorro, Cuenta Ahorro 5 Estrellas, todos los consumos que realizados con
> Divídelo Todo, consumiendo en comercios aliados (La Torre, Cemaco), Tarjetas
> de crédito MasterCard se deberá de solicitar por medio de agencia o Contact
> Center para acumular.*

Cruzada con la infografía del boletín y con las páginas de producto:

| # | Vía | ¿Tasa pública? |
|---|---|---|
| 1 | Tarjetas de crédito y débito **Visa** | **Sí** |
| 2 | Tarjetas de **débito Mastercard** | No |
| 3 | Tarjetas de **crédito Mastercard**, previa solicitud | No |
| 4 | **Divídelo Todo** | No |
| 5 | **Saldo promedio** en tres cuentas de depósito | Solo el umbral |
| 6 | **Comercios aliados** | No |
| 7 | **Tarjeta Prepago Club Bi** | No |
| 8 | **Campañas y sorteos** | Sí, por campaña |

**De ocho vías, una sola publica su tasa.** Es H-2 en su forma más cruda: no es
que el programa esconda sus reglas, es que solo escribió una de ocho.

### Las cuatro tuberías

Vistas desde los datos, esas ocho colapsan en cuatro orígenes. No son variantes
de lo mismo: tienen disparadores, relojes y grados de reconstruibilidad
diferentes.

| Vía | Disparador | Reloj | ¿Se puede rederivar? |
|---|---|---|---|
| Consumo con tarjeta | Transacción autorizada | 48 a 72 horas hábiles | Sí |
| Saldo promedio | Cierre de cuenta de depósito | Mensual | Sí, si se guarda el saldo |
| Promoción | Consumo + campaña vigente + inscripción | Ventana de campaña | Solo con el padrón histórico |
| Sorteo | Selección aleatoria + notificación SMS | +48 horas | **No** |

Las vías 1, 2, 3, 4, 6 y 7 entran todas por el autorizador de tarjetas. Eso
significa que la diferencia entre ellas **no está en la tubería sino en el motor
de reglas**: es un atributo del producto y del comercio, resuelto en el momento
de acreditar. Es una buena noticia de diseño —cambiar la tasa de una vía no
obliga a tocar las otras— y a la vez la razón por la que el motor de reglas es
el componente crítico de todo el sistema.

**Ninguna vía del sistema es síncrona.** El propio programa lo publica:

> ***¿Mis Bi Puntos se acreditan inmediatamente al haber realizado una compra?**
> No, el proceso de acreditación de Bi Puntos puede variar y en la mayoría de
> los casos tarda entre 48 y 72 horas (días hábiles).*

Eso descarta la lectura más intuitiva del sistema —un motor que reacciona a cada
autorización— y confirma que la acumulación se resuelve **por lotes**. También
tiene un efecto que el programa no comunica: 48 a 72 horas *hábiles* pueden ser
una semana de calendario con un fin de semana y un feriado de por medio, y
durante esa semana el cliente ve un saldo que no incluye lo que compró, sin
ninguna indicación de que falta algo.

La última fila sigue siendo el problema, pero por una razón distinta de la
latencia: ahora que todo el sistema acredita con retardo, **lo que hace único al
sorteo es que no se puede rederivar**. Un punto de sorteo no es una función del
consumo: es una función de un sorteo que ocurrió y se notificó por SMS. Si ese
registro se pierde, el saldo del cliente no se puede reconstruir desde ninguna
otra fuente.

### Consumo con tarjeta

La regla base, público:

> **1 punto por cada US$1 de compra.**

Su excepción, publicada como nota al pie con asterisco en las páginas de
producto:

> ***Por cada 10 dólares de compra en supermercados, gasolineras, tiendas de
> conveniencia, entidades de beneficencia y centros educativos acumulas 1
> punto.**

En esas cinco categorías se gana **1 punto por cada US$10**: una penalización
de diez a uno.

Las cinco categorías no son arbitrarias. Son las que tienen tasa de intercambio
regulada o reducida, donde el emisor gana menos por
transacción. El programa traslada esa economía al cliente. La decisión es
defendible desde el negocio; lo que no lo es tanto es que se comunique en un
asterisco, cuando supermercado y gasolinera son precisamente el gasto
recurrente típico de una tarjeta.

**La moneda importa.** La tasa se enuncia por dólar, pero el consumo en
Guatemala se liquida en quetzales. Eso obliga al motor a convertir moneda antes
de aplicar la tasa, y ninguna fuente pública dice con qué tipo de cambio ni de
qué fecha: ¿el de la autorización, el del cierre del ciclo, uno institucional
fijo? A la tasa base, la diferencia entre dos tipos de cambio razonables mueve
el saldo de todos los clientes en todas sus transacciones.

### Topes anuales: la categoría cambia el techo, no la tasa

| Categoría de tarjeta | Tope anual |
|---|---|
| Mastercard Gold Internacional | 180,000 puntos |
| Visa Premier | 180,000 puntos |
| Visa Signature | 360,000 puntos |
| Visa Infinite | 420,000 puntos |

Esto es lo más interesante del diseño: **la
categoría de tarjeta no multiplica la tasa.** Un cliente Infinite y un cliente
Premier ganan exactamente lo mismo por dólar. Lo que cambia es cuánto pueden
ganar antes de topar.

Es una decisión distinta de la habitual en la región, donde la categoría alta
suele traer un multiplicador. Tiene sentido económico —el techo protege el
pasivo del emisor— pero significa que el beneficio de subir de categoría solo
se materializa para quien consume lo suficiente como para chocar con el techo
anterior. Para todos los demás, subir de categoría no cambia nada en puntos.

**Cuatro categorías publican su tope. El resto no.** Visa Clásica, Visa
Platinum, toda la línea Mastercard de débito y las tarjetas de débito Visa solo
dicen «Acumulas Bi Puntos por compras, canjeables en establecimientos
afiliados». Sin tasa y sin tope. Esto es una *ausencia verificada*: se buscó en
sus páginas y no está.

Queda una pregunta que desde fuera no se puede responder: **¿el tope se
aplica por tarjeta, por cliente o por grupo familiar unificado?** Con
unificación familiar y varias tarjetas por persona, las tres respuestas dan
saldos distintos para el mismo consumo. Es la pregunta P-1 del cuestionario al
cliente.

### Mastercard de crédito: acumular es opcional y cuesta

Las tarjetas de crédito Mastercard **no acumulan Puntos Bi por defecto.** Hay
que solicitarlo —por agencia o por el Contact Center, PBX 1717— y la solicitud
tiene tres propiedades poco habituales:

- **Cambia las condiciones del crédito.** Al afiliarse, la tasa mensual queda en
  2.5% (Standard y Gold Internacional), 2.2% (Platinum) o 2.0% (Black).
- **Es irreversible** sin emitir una tarjeta nueva.
- **Excluye** la Mastercard UEFA Champions League.

Con la primera hay que ser preciso, porque es fácil leer de más. La fuente
—una entrada de blog de enero de 2022— enuncia esas tasas como las vigentes «al
momento de realizar la gestión», **sin decir contra qué se comparan**. Frente al
tarifario actual, 2.5% mensual sobre una Mastercard Standard es *menos* que el
36% anual que hoy publica ese producto. No hay evidencia de que
afiliarse encarezca el crédito, ni de que lo abarate; las dos cifras son de años
distintos y no son comparables limpiamente. Lo que está sostenido es que
**cambia las condiciones de forma irreversible**, y que esa decisión se toma por
teléfono. Es la pregunta **P-7**.

**Hay una ausencia verificada que agrava el asunto.** Las cuatro páginas de
producto Visa listan «Acumulas Bi Puntos por compras» entre sus beneficios. Las
cuatro Mastercard listan exactamente los mismos beneficios **menos esa línea**.
No dicen que no acumulan: el beneficio simplemente no aparece, y tampoco aparece
que se pueda solicitar. Un cliente que compara una Visa Clásica con una
Mastercard Standard en el sitio del banco no tiene forma de enterarse de que la
segunda puede acumular. Ese dato vive únicamente en un blog de 2022.

Es el patrón de H-2 otra vez: la regla existe, es pública, y está donde nadie la
va a buscar.

### Comercios aliados y tarjeta prepago

Dos vías que el caso no había recogido y que no son variantes del consumo con
tarjeta.

**Comercios aliados.** Consumir con Tarjetas Bi en ciertos comercios otorga
puntos **adicionales** a los que da la tarjeta. Aquí el premio
lo origina el comercio, no el producto bancario, lo que implica un acuerdo
comercial y una regla por comercio que el motor tiene que resolver. Ninguna
fuente publica cuánto, y las tres que existen no coinciden en la lista:

| Fuente | Comercios |
|---|---|
| Infografía del boletín | Cemaco, La Torre, Electrónica Panamericana, La Curacao |
| Página de Bi Puntos | Max, Cemaco, La Torre |
| Preguntas frecuentes de Club Bi | La Torre, Cemaco |

Tres listas distintas del mismo emisor, en el mismo momento. Va más allá de la
redacción: si el motor aplica un factor por comercio, saber qué comercios son es
parte de la regla.

**Tarjeta Prepago Club Bi.** Acumula en «más de 1,000 establecimientos que
cuenten con POS Visa». Es relevante porque rompe el supuesto de que acumular
exige una relación de crédito o una cuenta: un instrumento prepago, recargable
en agencias y en puntos «Tu Bi Aquí», también genera saldo de puntos. Sin tasa
publicada.

### Saldo promedio de cuentas de depósito

Público: acumulan **Súper Cuenta Monetaria, Súper Cuenta de Ahorro y Cuenta de
Ahorro 5 Estrellas**, por saldo promedio.

Es la vía que menos se comunica y la que más cambia la naturaleza del programa.
Las demás premian gastar; esta premia **no gastar**. Un cliente que nunca usa
una tarjeta puede acumular puntos simplemente dejando dinero quieto en su
cuenta.

Dos precisiones que el propio programa publica y que acotan el mecanismo:

> ***¿Si realizo depósitos a mis cuentas Monetarias o de Ahorros, acumulo Bi
> Puntos?** No, recuerda que los depósitos a tus cuentas no acumulan Bi Puntos,
> acumulas Bi Puntos por los saldos promedio que mantienes en tu Súper Cuenta de
> Ahorros, Súper Cuenta de Monetarios y tu Cuenta de Ahorros 5 estrellas\*.*
>
> *\* Cada Cuenta tiene su propia Regla de Acumulación*

La primera descarta que esta vía reaccione a movimientos: **los depósitos no
acumulan nada**. Reacciona únicamente a un cierre de periodo. La segunda es más
importante de lo que aparenta: el banco reconoce por escrito que **no hay una
regla, hay tres**, una por tipo de cuenta.

**Lo que sí es público es el umbral.** Cada página de producto publica desde qué
saldo promedio mensual empieza a acumular su cuenta:

| Cuenta | Saldo promedio mensual desde el que acumula | Dónde lo dice |
|---|---|---|
| Súper Cuenta de Ahorro | más de **Q500.00** | Página del producto |
| Súper Cuenta Monetaria | más de **Q1,000.00** | Página del producto |
| Cuenta de Ahorro 5 Estrellas | a partir de **Q1,000.00** | Página del producto |

Que los umbrales sean distintos confirma desde fuera lo que el asterisco admite:
son tres reglas, no una.

**Lo que no es público es la tasa.** Ninguna fuente dice cuántos puntos genera
un saldo promedio de cuánto, para ninguna de las tres cuentas. Se sabe desde
dónde se empieza a acumular y no se sabe cuánto se acumula, que es la
mitad que le sirve al cliente para decidir.

Sin esa cifra no se puede responder algo básico: **¿el programa premia gastar o
premia ahorrar?** La relación entre la tasa de consumo y la tasa de saldo es lo
que decide cuál de los dos comportamientos remunera más, y hoy es invisible
tanto para el cliente como para este diagnóstico. Es la pregunta P-2, y son tres
las cifras que faltan, no una.

**Hay también un multiplicador por membresía.** Tener la membresía Club Bi
activa duplica los puntos que genera el saldo. Las dos fuentes del banco no
coinciden en sobre qué cuenta aplica:

| Fuente | Qué dice |
|---|---|
| Preguntas frecuentes de Club Bi | dobles Bi Puntos en la **Súper Cuenta de Ahorros** |
| Página de Bi Puntos | dobles Bi Puntos con tu **cuenta monetaria** |

Es un dato con consecuencia directa sobre §2.5: la membresía de Q15 mensuales no
solo abre la capa promocional, compra un **multiplicador permanente** sobre una
vía de acumulación. Cuál, no está claro. Es la pregunta **P-12**.

Desde la arquitectura, este mecanismo es el que más pesa: no reacciona a un
evento sino a un cierre de mes. El saldo de puntos de un cliente es, por
diseño, la suma de un flujo en tiempo real y un lote mensual, y las dos mitades
no se pueden conciliar con el mismo reloj.

### Promociones

Encima de todo lo anterior hay una capa de reglas temporales. Las bases de tres
promociones reales dejan ver la maquinaria:

**Dobles y triples puntos (julio 2025).** Dobles puntos en todo consumo con
tarjetas Bi Visa. Triples los fines de semana, por rubro y fecha:
electrodomésticos el 5 y 6, restaurantes el 12 y 13, ropa el 19 y 20,
entretenimiento el 26 y 27. Tope de 1,500 puntos por cliente. Solo clientes
inscritos.

**Tus compras se transforman en Puntos Bi (2022).** 1 punto por cada quetzal
consumido, sobre compras de Q300 o más, con tope diario de 800 puntos y tope
mensual de 30,000. Requiere membresía Club Bi vigente y servicio Bi Móvil
activo.

**Gana hasta 50,000 Bi Puntos (2021).** Consumo mínimo de Q100 para participar.
100 ganadores diarios de 500 puntos, 50 ganadores diarios de 1,000, 10 premios
semanales de 10,000 y 5 premios mensuales de 50,000. Acreditación 48 horas
después de la notificación por SMS. No participan empleados de la corporación.

De esas tres bases se deduce qué tiene que existir en el motor:

- Multiplicadores generales y por categoría de comercio, con vigencia por
  fecha y hasta por día de la semana.
- **Acumuladores con ventana**: tope diario, tope mensual, tope por campaña y
  tope anual, todos conviviendo.
- **Ticket mínimo** por transacción (Q300) y **consumo mínimo** para participar
  (Q100).
- **Padrón de inscritos** por campaña.
- **Predicados de elegibilidad externos**: membresía vigente, Bi Móvil activo.
- Una vía de **acreditación asíncrona** con retardo de 48 horas.

Un detalle más: la promoción de 2022 daba **1 punto por cada
quetzal**, cuando la tasa base es 1 punto por dólar. No es un multiplicador: es
una regla que **cambia la unidad de la tasa**, no su coeficiente. El motor tiene
que soportar eso, lo que es bastante más que aplicar un factor.

---

## 2.2 Cómo se conservan: vigencia y expiración

Público:

> Los Bi Puntos tienen una vigencia de dos años y vencen el 5 de febrero de
> cada año los acumulados dos años antes.

Leído con cuidado, eso **no** dice «dos años desde el consumo». Dice que hay un
corte anual en fecha fija, y que ese corte se lleva todo lo acumulado durante
un año calendario determinado.

La consecuencia es medible y el programa no la comunica:

| Punto ganado en | Vence el | Vida efectiva |
|---|---|---|
| Enero de 2024 | 5 de febrero de 2026 | ~25 meses |
| Junio de 2024 | 5 de febrero de 2026 | ~20 meses |
| Diciembre de 2024 | 5 de febrero de 2026 | ~13 meses |

Dos clientes a los que se les dijo lo mismo —«dos años»— tienen doce meses de
diferencia en su derecho de uso, según el mes en que compraron. Está
desarrollado como hallazgo H-3.

Hay otra regla que no es pública y que es puro dinero del cliente: **¿qué
lote se consume primero al canjear?** Si se gastan primero los puntos más
antiguos, el cliente pierde menos en cada corte. Si se gastan primero los más
nuevos, un cliente que canjea todos los meses puede aun así perder el lote
viejo completo. Ninguna fuente lo dice. Es la pregunta P-4.

---

## 2.3 De quién es el saldo

No del cliente: del **grupo familiar**.

La unificación familiar permite trasladar el total de los puntos entre
miembros del círculo familiar —padre, madre, hermanos y cónyuge, este último
acreditado con acta matrimonial— y tiene dos condiciones públicas:

- **Solo el titular de la unificación puede canjear.**
- **La unificación debe permanecer como mínimo un año.**

Esto tiene tres consecuencias que atraviesan todo el caso:

- El grano natural del modelo de datos es el grupo, no la persona. Cualquier
  análisis por cliente cuenta puntos que ese cliente no puede canjear.
- Un grupo recién unificado tiene saldo visible y no puede ejercerlo durante
  doce meses. Es un estado que los canales de consulta no distinguen.
- Exigir acta matrimonial deja fuera la unión de hecho, que es una figura
  reconocida por la legislación guatemalteca. No es un problema técnico, pero
  sí una decisión de producto que el cliente debería tomar a conciencia.

---

## 2.4 Cómo se gastan: el canje

Aquí está la asimetría más visible del programa.

**Seis canales para consultar el saldo:** App Club Bi, Bi en Línea web, el
portal `bipuntos.bi.com.gt`, los centros de canje, el PBX 1717 y el estado de
cuenta Bi Puntos.

**Tres vías para ejecutar el canje, documentadas de forma muy desigual:**

| Vía | Qué permite | Qué tan documentada está |
|---|---|---|
| Centro de canje, presencial | Todo el catálogo | Requisitos completos, en varias fuentes |
| Portal, tras iniciar sesión | No público | Solo existe el menú «Canje en línea» |
| PBX 1717 | Conversión a millas LifeMiles | «Para canjear tus puntos llama al 1717» |

Hay tres vías y **el cliente solo
conoce una**. Toda la documentación pública del canje describe el mostrador. El
canje en línea existe —el portal tiene su entrada de menú— y no hay una sola
fuente que diga qué parte del catálogo admite. Es la pregunta **P-8**, y es otra
manifestación de H-2: la funcionalidad existe y la regla que la gobierna no está
escrita en ningún lado.

Los requisitos de la vía presencial, públicos:

| Quién canjea | Qué presenta |
|---|---|
| Cliente individual | Tarjeta Club Bi física + documento de identificación |
| Cliente empresarial | Tarjeta Club Bi **Empresarial** física + DPI del representante legal + copia de nombramiento vigente |
| Un tercero | Tarjeta Club Bi del titular + copia del DPI del titular + copia del DPI de quien canjea + carta de autorización |

En la segunda fila, **el titular de un saldo no es siempre una persona ni un
grupo familiar.** Puede ser una empresa, con representante legal y nombramiento
con su propia vigencia. Es una entidad que el modelo de datos tiene que
contemplar.

Sobre cuántos establecimientos afilia el programa, las fuentes del propio banco
no coinciden: el portal dice «más de **40**» y el blog corporativo «más de
**50**». Una de las dos está desactualizada y desde fuera no hay forma de saber
cuál.

### Cuánto vale un punto

El portal destaca en portada un premio que, por sí solo, le pone precio al
programa:

> **1,615 puntos** — Certificado de Regalo por Q100

De ahí sale, directamente: **Q0.0619 por punto**. Es el primer número del caso
que dice cuánto vale lo que se acumula, y no existía en la primera ronda del
diagnóstico.

Expresarlo como retorno sobre el consumo exige el tipo de cambio que el banco no
publica (pregunta P-3), así que lo siguiente es una **ilustración, no un dato**:
a un tipo de cambio de referencia de ~Q7.70/US$, el programa devuelve **alrededor
del 0.8% del consumo** en su tasa base y **alrededor del 0.08%** en las cinco
categorías reducidas. Mueva el tipo de cambio dentro de un rango razonable y el
orden de magnitud no cambia.

Es el número que permite dimensionar la penalización de 10 a 1 (H-6) y valorar
la conversión a millas (H-1) contra una referencia concreta. Hay que releerlo
antes de reutilizarlo: el catálogo de premios cambia, y esta cifra es del 22 de
septiembre de 2026.

### Conversión a millas

Existe conversión a millas LifeMiles, se gestiona por teléfono, y el propio
portal la acompaña de una advertencia que es el hallazgo central de este caso:

> la conversión «puede variar según el producto con el que acumules Bi Puntos»

Si el valor de canje de un punto depende del producto que lo generó, entonces
**los puntos no son intercambiables entre sí**. El saldo único que muestran los
seis canales de consulta es, en ese caso, una simplificación que no alcanza
para decidir un canje: dos clientes con 10,000 puntos pueden no poder comprar
lo mismo. Está desarrollado como hallazgo H-1.

---

## 2.5 Lo que cuesta participar

### Bi Puntos y Club Bi no son el mismo programa

Es la confusión más fácil de cometer, porque comparten nombre comercial, tarjeta
física y usuario del portal. Pero el propio banco los separa por escrito:

> ***¿Si no pago mi membresía de Club Bi, aún puedo canjear mis Bi Puntos?** Sí,
> aún puedes realizar el canje de tus Bi Puntos, ya que el Programa de Bi Puntos
> es ajeno al Programa de beneficios que otorga Club Bi al pagar tu membresía.*

| | **Bi Puntos** | **Club Bi** |
|---|---|---|
| Qué es | Programa de lealtad: acumular y canjear puntos | Programa de beneficios y descuentos |
| Costo | **Gratuito** | Q15.00 mensuales |
| Cómo se entra | Automático, por usar productos afiliados | Pagando la membresía |

**Participar en el programa de puntos no cuesta nada.** Tres matices que sí se
sostienen:

- **La tarjeta Club Bi física sigue siendo obligatoria para canjear**, porque
  «*en ella se depositan todos tus Bi Puntos*». El plástico es requisito; la
  membresía de pago, no.
- **Varias promociones sí exigen membresía Club Bi vigente.** La membresía no
  compra el acceso al programa base, pero condiciona el acceso a la capa
  promocional.
- **Y compra un multiplicador permanente.** La membresía activa da **dobles Bi
  Puntos** sobre la acumulación por saldo promedio (§2.1). Esto matiza lo
  anterior: no es solo acceso a promociones temporales, es una tasa distinta de
  forma sostenida sobre una de las ocho vías.

Con esto, «gratuito» sigue siendo cierto para acumular y canjear, pero la
pregunta económica cambia. Ya no es «¿vale la pena pagar Q180 al año por
descuentos?», es «¿vale la pena pagar Q180 al año por descuentos **más el doble
de puntos sobre mi saldo promedio**?». La segunda no se puede responder,
porque la tasa base de esa vía no es pública: duplicar una cifra desconocida
sigue siendo una cifra desconocida.

### El costo real está en el producto, no en el programa

Donde sí hay un costo es en la tarjeta que se usa para acumular. El tarifario
completo, público, producto por producto:

| Producto | Interés anual Q | Interés anual $ | Membresía | Extorno | ¿Acumula? |
|---|---|---|---|---|---|
| Visa Clásica | **60.00 %** | 33 % | Q420 | Q6,750 | **Sí** |
| Visa Premier | 48.60 % | 30 % | Q420 | Q20,700 | **Sí** |
| Visa Platinum | 47.40 % | 27 % | Q610 | Q54,000 | **Sí** |
| Visa Signature | 40.20 % | 24 % | Q1,200 | Q78,000 | **Sí** |
| Mastercard Standard | **36.00 %** | 36 % | Q420 | Q6,750 | No |
| Mastercard Gold Intl. | 32.00 % | 32 % | Q420 | Q3,500 | No |
| Mastercard Platinum | 27.00 % | 27 % | Q610 | Q54,000 | No |
| Mastercard Black | 24.00 % | 24 % | Q1,200 | Q78,000 | No |

Las dos marcas están emparejadas por nivel: misma membresía, mismo consumo para
extorno, mismo extrafinanciamiento. Lo único que cambia sistemáticamente entre
cada par es **la tasa en quetzales y la acumulación de puntos**.

El par de entrada lo muestra sin ambigüedad. Visa Clásica y Mastercard Standard
comparten membresía (Q420), extorno (Q6,750) y extrafinanciamiento (3.17%
mensual), y se separan en **60% contra 36% de interés anual en quetzales** — con
la que acumula puntos siendo la cara.

**Para un cliente que financia saldo, el programa no compensa.** Con el punto
valuado en Q0.0619, el retorno ronda el 0.8% del consumo; la diferencia de tasa
son 24 puntos porcentuales sobre el saldo financiado. No hay volumen de consumo
razonable que cierre esa brecha.

**Para un cliente que paga de contado, el razonamiento no aplica**: no paga
intereses, la tasa le da igual y los puntos son ganancia neta. El hallazgo es
condicional y hay que presentarlo así.

Lo que es incondicional: **el sitio del banco no ofrece ningún elemento para
hacer esta comparación**. Las tasas están en un micrositio de activación; el
valor del punto, en el portal de puntos; la posibilidad de afiliar una
Mastercard, en un blog de 2022. Tres dominios distintos para una sola decisión de
compra.

> **Alcance de la comparación.** Son tasas nominales anuales. No se consideraron
> comisiones, seguros ni los días de financiamiento sin intereses, que las
> fuentes mencionan sin detallar de forma comparable. La tabla sirve para ver la
> estructura, no para calcular el costo real de un cliente concreto.
