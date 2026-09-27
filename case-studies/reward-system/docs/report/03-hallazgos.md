# 3. Hallazgos

Parte del reporte; el índice está en [README.md](../README.md).

Ocho hallazgos, ordenados por severidad. Cada uno trae la evidencia que lo
sostiene, la consecuencia concreta y qué haría falta para cerrarlo.

Ninguno es un fallo de funcionamiento. El programa acumula, expira y canja, y
lleva años haciéndolo con promociones encima. Lo que estos hallazgos describen
son problemas de **explicabilidad, gobierno de reglas y exactitud**, que es
lo que se degrada cuando el equipo que diseñó un sistema ya no está.

| # | Hallazgo | Severidad | Tipo |
|---|---|---|---|
| H-1 | Los puntos no son intercambiables, pero se presentan como un saldo único | Alta | Funcional |
| H-2 | No existe ninguna fuente que enuncie completa la regla de acumulación | Alta | Gobierno |
| H-3 | «Dos años» de vigencia son entre 13 y 25 meses según el mes de compra | Alta | Transparencia |
| H-4 | La tasa se define en dólares, el consumo se liquida en quetzales | Alta | Exactitud |
| H-5 | El portal de puntos tiene identidad propia, admite contraseñas de 4 caracteres y consulta saldos sin autenticar | Alta | Seguridad |
| H-6 | La penalización de 10 a 1 cae sobre el gasto recurrente y se comunica en un asterisco | Media | Transparencia |
| H-7 | La acreditación por sorteo no se puede reconstruir | Media | Auditoría |
| H-8 | El canje tiene tres vías y el cliente solo conoce una | Media | Valor percibido |

---

## H-1 · Los puntos no son intercambiables, pero se presentan como un saldo único

**Severidad: alta.** Funcional.

### Qué se observó

El portal de millas advierte que la conversión de Puntos Bi a millas LifeMiles
«puede variar según el producto con el que acumules Bi Puntos».

### Por qué importa

Si el valor de canje de un punto depende del producto que lo generó, entonces
un punto ganado con una Visa Signature y un punto ganado por saldo promedio
**no son la misma cosa**, aunque los dos se llamen «punto» y se sumen en el
mismo número.

Ese número único es lo que muestran los seis canales de consulta.

La consecuencia práctica: dos clientes con 10,000 puntos pueden no poder
comprar el mismo premio, y ninguno de los dos tiene forma de saberlo antes de
llegar al mostrador. Un mismo cliente tampoco puede saber qué le conviene
canjear primero, porque el sistema no le dice de qué está compuesto su saldo.

Ahora se puede poner una referencia concreta a esa decisión. El portal destaca
un certificado de regalo de **Q100 por 1,615 puntos**, lo que fija el punto en
**Q0.0619** por la vía del catálogo. Cualquier conversión a millas que rinda
menos que eso deja al cliente peor de lo que estaría canjeando certificados, y
hoy no tiene forma de compararlas: la tasa de millas no es pública y depende
del producto que generó cada punto.

Desde la arquitectura, esto obliga a algo concreto: el saldo **no puede ser un
contador**. Tiene que ser un conjunto de lotes, cada uno con su origen, porque
el origen determina el valor. Es la misma lección que aparece en cualquier
sistema con trazabilidad: la procedencia de un dato no es metadato, es una
entrada.

### Qué hacer

1. Publicar la tabla de conversión por producto de origen. Es la petición
   mínima y no requiere tocar ningún sistema.
2. Desglosar el saldo por origen en los canales de consulta, aunque siga
   mostrándose un total.
3. Verificar que el ledger efectivamente guarda el origen por lote. Si no lo
   guarda, la conversión diferenciada se está resolviendo en otro lado y es
   urgente saber dónde.

### Qué falta por averiguar

Pregunta **P-5**: cuáles son las tasas de conversión por producto de origen.

---

## H-2 · No existe ninguna fuente que enuncie completa la regla de acumulación

**Severidad: alta.** Gobierno de reglas.

### Qué se observó

La regla de acumulación es pública, pero está repartida:

- La tasa base (1 punto por US$1) aparece en las páginas de producto, una por
  una.
- La tasa reducida (1 punto por US$10) aparece en una nota al pie con
  asterisco, repetida en cuatro páginas de producto.
- Los topes anuales aparecen en esas mismas páginas, y solo en cuatro de ellas.
- La acumulación por saldo promedio publica su **umbral** en cada página de
  cuenta (Q500 / Q1,000 / Q1,000) y **no publica su tasa** en ninguna parte.
- Las exclusiones aparecen dentro de las bases de promociones concretas, no
  como regla general.
- **La página del programa no menciona ninguna de estas cosas.**

Reconstruir la regla exigió cruzar cuatro páginas de producto distintas, tres
páginas de cuenta, tres bases de promoción, un boletín del blog y dos juegos de
preguntas frecuentes.

**La forma más cruda de decirlo:** el programa tiene ocho vías de acumulación y
**una sola publica su tasa.**

| Vía | ¿Publica su tasa? |
|---|---|
| Tarjetas Visa de crédito y débito | **Sí** |
| Tarjetas de débito Mastercard | No |
| Tarjetas de crédito Mastercard, previa solicitud | No |
| Divídelo Todo | No |
| Saldo promedio en tres cuentas | Solo el umbral |
| Comercios aliados | No |
| Tarjeta Prepago Club Bi | No |
| Campañas y sorteos | Sí, por campaña |

La **única fuente que enumera las ocho en un solo lugar** no está en la página
del programa ni en el reglamento: está en las preguntas frecuentes de Club Bi,
que es un programa distinto, con otro nombre y otro costo.

A esto se suma que las fuentes del propio emisor se contradicen entre sí en al
menos cuatro puntos: cuántos establecimientos afilia el programa (40 contra 50),
cuántos puntos cuesta el certificado de Q100 (1,595 contra 1,615), qué cuenta
recibe los dobles puntos por membresía (ahorros contra monetaria) y qué
comercios son aliados (tres listas distintas).

### Por qué importa

Este es el síntoma característico del problema que el encargo describe. Las
reglas siguen operando correctamente en el motor, pero **el documento que las
explicaba no existe o dejó de mantenerse**. Mientras el equipo original estuvo,
eso no se notaba: alguien sabía. Ahora nadie sabe, y la única forma de
responder «¿por qué mi saldo dice esto?» es leer código de producción.

El riesgo inmediato no es que el motor calcule mal. Es que cualquier cambio
futuro —una categoría nueva, un tope nuevo, una integración nueva— se haga sin
saber contra qué se está cambiando.

### Qué hacer

1. Constituir un **catálogo único de reglas versionado**, con la regla, su
   vigencia y su fuente. El archivo
   [`config/assumptions.yaml`](../../config/assumptions.yaml) de este caso es
   una primera versión, hecha desde fuera; la versión buena se hace desde
   dentro.
2. Que la página del programa enuncie la regla completa, y que las páginas de
   producto la referencien en vez de repetirla. Hoy pasa lo contrario, y por eso
   hay categorías que publican tope y categorías que no.
3. Tratar ese catálogo como la entrada del motor, no como documentación
   paralela. Una regla que vive en dos lugares se desincroniza; es cuestión de
   cuándo.

### Qué falta por averiguar

Pregunta **P-6**: si existe internamente el listado completo de exclusiones del
programa, fuera de las bases de cada promoción.

---

## H-3 · «Dos años» de vigencia son entre 13 y 25 meses según el mes de compra

**Severidad: alta.** Transparencia.

### Qué se observó

La regla pública:

> Los Bi Puntos tienen una vigencia de dos años y vencen el 5 de febrero de
> cada año los acumulados dos años antes.

Eso no es un vencimiento rodante de 24 meses desde el consumo. Es un **corte
anual en fecha fija** que se lleva todo lo acumulado durante un año calendario.

### Por qué importa

| Punto ganado en | Vence el | Vida efectiva |
|---|---|---|
| Enero de 2024 | 5 de febrero de 2026 | ~25 meses |
| Junio de 2024 | 5 de febrero de 2026 | ~20 meses |
| Diciembre de 2024 | 5 de febrero de 2026 | ~13 meses |

Doce meses de diferencia en el derecho de uso entre dos clientes a los que se
les comunicó lo mismo. El cliente que compró en diciembre recibe poco más de la
mitad de la vigencia que el que compró en enero, y el programa le dice «dos
años» a los dos.

No hay nada incorrecto en el cálculo: el corte anual es una decisión legítima y
frecuente, porque simplifica enormemente la operación. Lo que falla es la
comunicación, y es fácil de arreglar.

### Qué hacer

1. Mostrar en los canales de consulta **la fecha de vencimiento de cada lote**,
   no una vigencia genérica. El dato ya existe: cada lote nace con su fecha.
2. Cambiar el mensaje de «dos años» a «vencen el 5 de febrero de [año]», que es
   a la vez más simple y verdadero.
3. Avisar antes del corte. Un recordatorio en enero tiene un efecto directo
   sobre el uso del programa, y es donde entra el modelo de propensión de la
   [propuesta](../proposal/ml-ai-llm.md).

### Qué falta por averiguar

Pregunta **P-4**: qué lote se consume primero al canjear. Con un corte anual
fijo, gastar primero los puntos más nuevos puede hacer que un cliente que canja
todos los meses pierda igualmente el lote viejo completo.

---

## H-4 · La tasa se define en dólares, el consumo se liquida en quetzales

**Severidad: alta.** Exactitud.

### Qué se observó

La tasa pública se enuncia por dólar de compra. El consumo en Guatemala se
liquida en quetzales. Ninguna fuente pública dice con qué tipo de cambio se
convierte, ni de qué fecha.

### Por qué importa

El motor tiene que convertir moneda **antes** de aplicar la tasa, y esa
conversión admite al menos tres respuestas razonables y distintas:

- el tipo de cambio del momento de la autorización,
- el del cierre del ciclo de facturación,
- un tipo institucional fijo del banco.

A la tasa base de 1 punto por dólar, la diferencia entre dos de esas respuestas
mueve el saldo de **todos** los clientes en **todas** sus transacciones. No es
un caso borde: es el camino principal del sistema.

Hay un efecto de segundo orden: el
redondeo. Si los puntos se truncan por transacción, la fracción perdida en cada
compra depende del tipo de cambio aplicado. Sobre una cartera entera y un año,
eso deja de ser un decimal.

### Qué hacer

1. Fijar y documentar el tipo de cambio de acumulación: cuál, de qué fuente y
   de qué fecha.
2. Publicarlo. Es la única forma de que un cliente pueda verificar su propio
   saldo.
3. Revisar dónde se redondea. Truncar una vez por ciclo en lugar de una vez por
   transacción da el mismo resultado contable con menos pérdida para el
   cliente, y suele ser un cambio pequeño.

### Qué falta por averiguar

Pregunta **P-3**: con qué tipo de cambio y de qué fecha se convierte.

---

## H-5 · El portal de puntos tiene identidad propia, admite contraseñas de 4 caracteres y consulta saldos sin autenticar

**Severidad: alta.** Seguridad.

### Qué se observó

Tres cosas, y la combinación es peor que cada una por separado.

**Identidad separada.** El portal `bipuntos.bi.com.gt` tiene su propia alta de
usuario y su propia recuperación de contraseña, distintas de las de Bi en Línea.
Esa identidad **se comparte con Club Bi** —«*si ya te registraste en Club Bi,
puedes ingresar a Bi Puntos con el mismo usuario*»— así que no son dos juegos de
credenciales sino uno, el de los dos portales del programa, separado del de la
banca en línea.

**Política de contraseña.** El validador publicado del portal dice, literal:

> *El campo de contraseña es obligatorio, debe contener mayúscula, minúscula,
> número, carácter especial y un largo de 4 caracteres como mínimo.*

Exige cuatro clases de carácter y admite una **longitud mínima de 4**.

**Consulta de saldo sin autenticación.** El formulario «Consulta tus Bi Puntos»
del portal pide tipo de cliente (individual o empresarial), tipo de documento
(DPI, NIT o pasaporte) y número de documento, y devuelve «Puntos Disponibles» y
«Puntos a vencer». No pide contraseña.

### Por qué importa

Cuatro caracteres con composición obligatoria no es una contraseña fuerte: es
una contraseña corta con restricciones. La composición obligatoria no compensa
la longitud y **reduce** el conjunto de contraseñas válidas en vez de
ampliarlo, porque obliga a que las cuatro posiciones alojen cuatro clases
distintas. Es lo contrario del efecto buscado.

Lo que protege ese portal no es trivial: un saldo de puntos es un activo
canjeable, y el portal expone catálogo y canje en línea.

La identidad separada agrava el problema por dos vías. Primero, multiplica la
superficie: hay un segundo flujo de recuperación y un segundo almacén de
credenciales. Segundo, hace que las protecciones de la banca en línea —que
presumiblemente son mucho más estrictas— no apliquen aquí.

La consulta sin autenticación abre una pregunta aparte: un saldo canjeable
consultable contra un **identificador nacional** descansa en que ese
identificador sea secreto, y el DPI guatemalteco no lo es. Aparece en facturas,
contratos y formularios de todo tipo.

Hay también una asimetría de protección. El sitio corporativo
`www.corporacionbi.com` está detrás de un WAF que bloquea cualquier acceso
programático. El portal donde vive el saldo canjeable, no. La superficie mejor
protegida es la de marketing.

### Qué hacer

1. Elevar la longitud mínima. Es un cambio de configuración y es lo más barato
   de esta lista.
2. Determinar qué controles protegen la consulta de saldo. Es la pregunta P-11,
   y la respuesta decide si este punto es una observación de diseño o algo que
   atender con prioridad.
3. Unificar la identidad con Bi en Línea, o al menos federarla. Un programa de
   lealtad no justifica un tercer sistema de autenticación.
4. Mientras tanto, revisar el flujo de recuperación de contraseña del portal,
   que en un esquema separado suele ser el eslabón más débil.
5. Retirar `humans.txt` del portal. Publica el inventario de tecnología y los
   nombres del equipo que construyó el sistema; no aporta nada y cuesta un
   borrado.

### Nota sobre el alcance

Esto se observó desde fuera, como usuario anónimo, **sin probar nada**. No se
envió ninguna consulta de saldo, no se usó ningún número de documento, no se
intentó ningún acceso y no se evaluó la robustez real de nada. Puede
perfectamente existir un control que la página no muestra —un CAPTCHA, un límite
de intentos, una verificación posterior al envío—. Lo que aquí se afirma es
únicamente lo que las páginas publicadas declaran. Es una observación de
política publicada, no una prueba de penetración; el cliente debería
confirmarla internamente antes de dimensionarla.

---

## H-6 · La penalización de 10 a 1 cae sobre el gasto recurrente y se comunica en un asterisco

**Severidad: media.** Transparencia.

### Qué se observó

La nota al pie, idéntica en cuatro páginas de producto:

> ***Por cada 10 dólares de compra en supermercados, gasolineras, tiendas de
> conveniencia, entidades de beneficencia y centros educativos acumulas 1
> punto.**

Frente a la tasa base de 1 punto por US$1, eso es **una décima parte**.

Ahora se puede decir cuánto es en dinero. Con el punto valuado en Q0.0619
—1,615 puntos por un certificado de Q100, del propio portal— y usando un tipo de
cambio de referencia de ~Q7.70/US$ como **ilustración**, no como dato del
sistema:

| Tasa | Retorno aproximado sobre el consumo |
|---|---|
| Base, 1 punto por US$1 | ≈ **0.80 %** |
| Reducida, 1 punto por US$10 | ≈ **0.08 %** |

El tipo de cambio de acumulación no es público (P-3), así que estas cifras son
órdenes de magnitud. Pero el orden de magnitud es el mensaje: en supermercado y
gasolinera, el programa devuelve **menos de una décima de punto porcentual** de
lo que el cliente gasta.

### Por qué importa

Las cinco categorías no son arbitrarias: son las de tasa de intercambio
regulada o reducida, donde el emisor gana menos por transacción. Trasladar esa
economía al cliente es una decisión defendible desde el negocio, y casi todos
los programas de la región hacen algo parecido.

El problema es dónde se comunica. Supermercado y gasolinera no son categorías
marginales: son **el gasto recurrente típico de una tarjeta**. Para muchos
clientes, la mayor parte de su consumo cae en la tasa reducida, y lo que
acumulan es un orden de magnitud menos de lo que la comunicación principal
sugiere.

Hay un efecto que este equipo no puede medir desde fuera, pero que
hay que levantar: si la clasificación de comercio se resuelve mal —un
supermercado que no se reconoce como tal, o un comercio general clasificado
como gasolinera— la diferencia para el cliente es de diez veces. En cualquier
otro programa, un error de categoría cuesta un porcentaje; aquí cuesta un
orden de magnitud. Eso eleva la exactitud de la clasificación de comercio de
detalle técnico a control de negocio, y es la razón por la que la
[propuesta de ML](../proposal/ml-ai-llm.md) la pone en primer lugar.

### Qué hacer

1. Sacar la regla del asterisco. Enunciar las dos tasas con el mismo peso
   visual: es lo que un cliente necesita para decidir con qué tarjeta paga.
2. Medir qué proporción del consumo de la cartera cae en tasa reducida. Si es
   mayoritaria, la comunicación principal del programa está describiendo un
   caso minoritario.
3. Medir la exactitud de la clasificación de comercio, y tratarla como métrica
   con umbral, no como estadística de curiosidad.

---

## H-7 · La acreditación por sorteo no se puede reconstruir

**Severidad: media.** Auditoría y continuidad.

### Qué se observó

De las bases de la promoción «Gana hasta 50,000 Bi Puntos»: ganadores
seleccionados aleatoriamente, notificación por SMS, y **acreditación 48 horas
después de la notificación**.

### Por qué importa

Las otras tres vías de acumulación son funciones de datos que persisten en
otros sistemas. Si el ledger se corrompe, los puntos de consumo se pueden
recalcular desde el autorizador y los de saldo promedio desde el core de
depósitos.

Los puntos de sorteo, no. No se derivan de ninguna transacción: se derivan de
un sorteo que ocurrió, se notificó por un canal externo y se acreditó con
retardo. **Si se pierde ese registro, el saldo del cliente no se puede
reconstruir desde ninguna otra fuente.**

Hay que precisar qué hace único a este caso, porque es fácil señalar
lo equivocado. **No es el retardo.** El programa publica que *toda* acreditación
tarda entre 48 y 72 horas hábiles, así que esperar dos días no distingue al
sorteo de nada. Lo que lo distingue es que **es la única vía del sistema que no
es reproducible**: las otras tres son funciones de datos que persisten en otro
lado, y esta es función de un evento que solo existió en el registro del sorteo.

Es también la más difícil de conciliar, porque entre el evento y el asiento hay
un sistema de mensajería de por medio.

### Qué hacer

1. Tratar el registro de sorteos como fuente primaria, con el mismo respaldo y
   retención que el ledger, no como bitácora de una campaña terminada.
2. Conciliar explícitamente notificaciones enviadas contra puntos acreditados.
   Con 48 horas y SMS de por medio, la diferencia entre ambos conjuntos no va a
   ser cero, y hoy no hay forma de saber de qué tamaño es.
3. Registrar cada acreditación de sorteo con su identificador de sorteo y de
   notificación, de modo que el asiento apunte a su causa.

---

## H-8 · El canje tiene tres vías y el cliente solo conoce una

**Severidad: media.** Valor percibido.

### Qué se observó

Consultar el saldo se puede desde seis lugares: App Club Bi, Bi en Línea, el
portal de puntos, los centros de canje, el PBX 1717 y el estado de cuenta.

Canjear se puede de tres maneras, documentadas de forma muy desigual:

| Vía | Qué permite | Qué tan documentada está |
|---|---|---|
| Centro de canje, presencial | Todo el catálogo | Requisitos completos, repetidos en varias fuentes |
| Portal, tras iniciar sesión | **No público** | Solo existe la entrada de menú «Canje en línea» |
| PBX 1717 | Conversión a millas LifeMiles | «Para canjear tus puntos llama al 1717» |

La vía presencial exige la Tarjeta Club Bi **física** y documento de
identificación. Para terceros hace falta también carta de autorización y copia
del DPI del titular; para empresas, nombramiento del representante legal.

### Por qué importa

El diagnóstico inicial de este caso decía que había un solo canal de canje y que
era presencial. Es más interesante que eso: **hay tres, y dos de ellos no están
documentados**. Un cliente que quiera canjear busca en el sitio del banco,
encuentra los requisitos del mostrador, y no tiene forma de saber que existe una
alternativa digital ni qué puede hacer con ella.

Eso convierte a H-8 en una variante de H-2. El problema no es que falte
funcionalidad: es que **la regla que gobierna la funcionalidad existente no está
escrita**. La consecuencia práctica es la misma que si no existiera, porque una
capacidad que el cliente no conoce no se usa.

Sobre la vía presencial, el requisito de tarjeta física sigue siendo el detalle
que peor envejece: un programa cuya consulta es digital de punta a punta y cuyo
canje principal exige un plástico está sosteniendo dos modelos de servicio a la
vez.

Hay un efecto medible sobre el pasivo: cuanto más cuesta canjear,
más puntos llegan al corte del 5 de febrero sin usarse. Eso reduce el gasto
contable a corto plazo y erosiona la percepción de valor a largo plazo, que es
justamente lo que el programa existe para construir.

### Qué hacer

1. **Documentar el canje en línea que ya existe.** Es lo más barato de esta
   lista y no requiere construir nada: decir qué parte del catálogo admite canje
   digital y cómo se hace. Es la pregunta P-8.
2. Cuantificar. Qué proporción de los puntos emitidos se canja y qué proporción
   expira, abierto por vía y por tipo de premio. Sin ese número, cualquier
   inversión en canje digital es una apuesta.
3. Ampliar el canje digital a lo que no tenga logística física: certificados y
   conversión a millas. La conversión a millas es la candidata obvia, y hoy
   exige una llamada telefónica.
4. Revisar el requisito de tarjeta física. Si existe por identificación, hay
   alternativas; si existe por contrato con los centros de canje, es una
   negociación y no un problema técnico.

---

## Lo que este diagnóstico no puede afirmar

Se cierra con lo que queda fuera, porque un informe que no marca sus
límites invita a que lo usen para más de lo que aguanta.

- **No se observó ningún sistema.** Todo sale de material público. Lo que aquí
  se llama «arquitectura» es la arquitectura que las reglas públicas obligan a
  que exista, no la que se verificó en producción.
- **No hay datos de clientes.** Ninguna afirmación sobre volúmenes, tasas de
  canje o comportamiento está respaldada por datos reales, y ninguna se hace.
  Donde hacía falta un número para ilustrar un mecanismo, se usó el POC, y el
  POC corre sobre datos sintéticos declarados como tales.
- **Once preguntas siguen abiertas.** Están listadas al final de
  [`config/assumptions.yaml`](../../config/assumptions.yaml). Cinco de los ocho
  hallazgos dependen de la respuesta a alguna de ellas para poder dimensionarse.
- **El diagnóstico se corrigió a sí mismo una vez.** La segunda ronda de
  investigación tumbó tres afirmaciones de la primera, y están registradas en
  [`investigacion-y-supuestos.md`](../investigacion-y-supuestos.md). Se deja
  constancia porque es la forma en que este informe espera ser tratado: si el
  cliente muestra que algo aquí no es así, se corrige.
