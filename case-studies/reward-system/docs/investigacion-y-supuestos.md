# Investigación de campo y supuestos

| Nivel | Qué significa |
|---|---|
| `público` | Citable literalmente de un dominio de Corporación BI |
| `inferido` | No publicado como tal, pero se deduce de algo que sí lo está |
| `supuesto` | Elegido por el equipo consultor; no se presenta como dato del sistema |

---

## 1. Alcance y método

Se consultó material público encontrado en las páginas web de corporación bi. **No se usó ninguna cuenta
de cliente, no se probó ninguna credencial, no se accedió a ningún sistema interno y
no se intentó rodear ninguna protección de los sitios consultados.**

Orígenes consultados:

| Origen | Qué es | ¿Legible? |
|---|---|---|
| `www.corporacionbi.com` | Sitio corporativo; galería de tarjetas y páginas de producto | **No** directamente |
| `tarjetasbi.com` | Micrositio de activación y tarifario por producto | Sí |
| `bipuntos.bi.com.gt` | Portal del programa de puntos | Sí |
| `blog.corporacionbi.com` | Blog corporativo; bases de promociones | Sí |

Los cuatro son dominios del propio emisor, así que las citas de los tres últimos
tienen el mismo valor probatorio que las del primero.

### Por qué la fuente que se pidió no se pudo leer directamente

El punto de partida de esta ronda fue la galería de tarjetas de crédito:

---

## 2. Hallazgos nuevos

Nueve. Están numerados `N-*` para no chocar con los `H-*` del
[reporte de hallazgos](report/03-hallazgos.md). Los que corrigen algo ya escrito lo
dicen en su fila.

| # | Hallazgo | Confianza | Corrige |
|---|---|---|---|
| N-1 | Bi Puntos y Club Bi son dos programas distintos; la membresía de Q15 no hace falta para acumular ni canjear | `público` | §2.5 del reporte |
| N-2 | La acreditación no es en tiempo real: tarda 48–72 horas hábiles | `público` | §2.1 y H-7 |
| N-3 | 1,615 puntos = certificado de regalo de Q100 ⇒ **Q0.0619 por punto** | `público` | — (dato nuevo) |
| N-4 | Las cuatro páginas Visa dicen «Acumulas Bi Puntos»; las cuatro Mastercard, no | `público` | — (corrobora) |
| N-5 | La consulta de saldo se hace **sin autenticar**, contra un número de documento | `público` | Amplía H-5 |
| N-6 | La cuenta del portal es compartida con Club Bi, no un segundo juego de credenciales | `público` | Matiza H-5 |
| N-7 | Cada tipo de cuenta tiene su propia regla de acumulación por saldo promedio | `público` | Amplía P-2 |
| N-8 | Existe cliente empresarial, con Club Bi Empresarial propia | `público` | Modelo de datos |
| N-9 | El portal lo construyó una agencia externa, y `humans.txt` lo publica | `público` | — (contexto) |

---

### N-1 · Bi Puntos y Club Bi son dos programas distintos

`público`. Fuente: FAQ de [`/about-bi-puntos`](https://bipuntos.bi.com.gt/about-bi-puntos#faqs).

> **¿Si no pago mi membresía de Club Bi, aún puedo canjear mis Bi Puntos?**
> Sí, aún puedes realizar el canje de tus Bi Puntos, ya que el Programa de Bi Puntos
> es **ajeno** al Programa de beneficios que otorga Club Bi al pagar tu membresía.

El complemento, en la misma página:

> **¿Al optar por un beneficio de Club Bi acumulo Bi Puntos?**
> No, la acumulación se da únicamente al momento de que realices una transacción con
> los productos afiliados.

**Esto corrige un error del reporte.** La sección 2.5 afirmaba que «el programa de
lealtad es una suscripción de pago» de Q180 al año. No lo es. Son dos programas que
comparten nombre comercial, tarjeta física y login:

| | Bi Puntos | Club Bi |
|---|---|---|
| Qué es | Programa de lealtad: acumular y canjear puntos | Programa de beneficios y descuentos |
| Costo | **Gratuito** | Q15.00 mensuales |
| Cómo se entra | Automático, por usar productos afiliados | Pagando la membresía |

Lo que **sí** se sostiene después de la corrección:

- **La tarjeta Club Bi física sigue siendo obligatoria para canjear.** «*…es necesario
  que presentes tu Tarjeta Club Bi, ya que en ella se depositan todos tus Bi Puntos*».
  El plástico es requisito; la membresía de pago, no.
- **Varias promociones sí exigen membresía Club Bi vigente.** La promoción de 2022 lo
  pedía explícitamente. Entonces la membresía no compra el acceso al programa base,
  pero sí condiciona el acceso a la capa promocional.

Para el diagnóstico, el costo de participar en el programa base
es cero, y eso cambia por completo el argumento sobre percepción de valor.

---

### N-2 · La acreditación tarda entre 48 y 72 horas hábiles

`público`. Misma fuente.

> **¿Mis Bi Puntos se acreditan inmediatamente al haber realizado una compra?**
> No, el proceso de acreditación de Bi Puntos puede variar y en la mayoría de los
> casos tarda entre **48 y 72 horas (días hábiles)**.

El reporte clasificaba el consumo con tarjeta como acumulación en «tiempo real». No lo
es. **Ninguna vía del sistema es síncrona**, y eso tiene dos consecuencias de
arquitectura que el caso no había recogido:

1. **El motor de acumulación es por lotes, no por evento.** El PDF de arquitectura ya
   lo dibuja así («ingesta batch y en tiempo real»); ahora hay una cita del propio
   banco que lo sostiene.
2. **El retardo del sorteo deja de ser excepcional.** El caso presentaba las 48 horas
   del sorteo como su rasgo distintivo. Con todo el sistema operando a 48–72 horas, lo
   que hace único al sorteo **no es la latencia sino que no se puede rederivar**. El
   argumento de H-7 había que afilarlo, no retirarlo.

Hay una consecuencia para el cliente que el programa no comunica: entre 48 y 72 horas
*hábiles* puede ser una semana de calendario si hay fin de semana y feriado de por
medio. Un cliente que consulta su saldo el lunes después de comprar el viernes ve un
número que todavía no incluye su compra, sin ninguna indicación de que falta algo.

---

### N-3 · El primer valor monetario del punto

`público`. Fuente: portada de [`bipuntos.bi.com.gt`](https://bipuntos.bi.com.gt/),
bloque «Premios destacados»:

> **1615 puntos** — Certificado de Regalo por Q100

Confirmado por la página del programa: «*Puedes obtener certificados de regalo desde
Q100*».

De ahí sale, directamente:

```
Q100 / 1,615 puntos = Q0.0619 por punto     (público, derivado de una sola cita)
```

Es el primer número de este caso que le pone precio a un punto. Hasta ahora todo el
diagnóstico razonaba sobre cuántos puntos se ganan, nunca sobre cuánto vale uno.

#### Lo que todavía no se puede afirmar

El retorno como porcentaje del consumo. Para calcularlo hay que convertir «1 punto por
US$1» a quetzales, y **el tipo de cambio de acumulación no es público** — es la
pregunta [P-3](../config/assumptions.yaml), ya abierta desde la primera ronda.

Así que la cifra siguiente es una **ilustración, `supuesto`**, no un dato del sistema:

| A un tipo de cambio de referencia de Q7.70/US$ | Retorno sobre el consumo |
|---|---|
| Tasa base (1 punto por US$1) | ≈ **0.80 %** |
| Cinco categorías reducidas (1 punto por US$10) | ≈ **0.08 %** |

Se presenta como orden de magnitud. Mueva el tipo de cambio dentro de un rango
razonable y el resultado no cambia de orden: el programa devuelve **menos del uno por
ciento** en su tasa buena y **menos de una décima de punto porcentual** en
supermercado y gasolinera.

Esto es lo que por fin permite **dimensionar** dos hallazgos que hasta ahora se
argumentaban sin cifras:

- **H-1** (los puntos no son intercambiables): ahora hay una referencia contra la cual
  comparar la conversión a millas. Si convertir a LifeMiles rinde menos de Q0.0619 por
  punto, el cliente está peor que canjeando certificados, y nadie se lo dice.
- **H-6** (la penalización de 10 a 1): deja de ser «una décima parte» en abstracto y
  pasa a ser *ocho centésimas de punto porcentual de retorno* sobre el gasto recurrente
  de una tarjeta.

**Advertencia de vigencia:** el catálogo de premios cambia. Esta cifra es del 22 de
septiembre de 2026 y hay que volver a leerla antes de reutilizarla. El PDF de
arquitectura registra 1,595 puntos para el mismo certificado, lo que probablemente
sea una lectura anterior del mismo catálogo — ver la sección 5.

---

### N-4 · Las páginas Visa mencionan los puntos; las Mastercard, no

`público`, **ausencia verificada**. Fuente: las ocho páginas de producto de
`tarjetasbi.com`.

Se leyó el bloque «BENEFICIOS» de las ocho. El resultado es limpio y sin excepciones:

| Producto | ¿Aparece «Acumulas Bi Puntos por compras»? |
|---|---|
| Visa Clásica | **Sí** |
| Visa Premier | **Sí** |
| Visa Platinum | **Sí** |
| Visa Signature | **Sí** |
| Mastercard Standard | **No** |
| Mastercard Gold Internacional | **No** |
| Mastercard Platinum | **No** |
| Mastercard Black | **No** |

Las cuatro páginas Mastercard listan exactamente los mismos cinco beneficios que las
Visa **menos** la línea de los puntos. No dicen que no acumulan; el
beneficio simplemente no aparece en la página.

Esto corrobora, desde una fuente independiente del blog, que las Mastercard de crédito
no acumulan por defecto. Pero deja algo peor a la vista: **la página de producto ni
siquiera menciona que la acumulación se puede solicitar.** Un cliente que compara una
Visa Clásica con una Mastercard Standard en el sitio del banco no tiene forma de
enterarse de que la segunda puede acumular llamando al 1717. Ese dato vive solo en una
entrada de blog de enero de 2022.

Es el patrón de H-2: la regla existe, es pública, y está en el lugar donde
nadie la va a buscar.

---

### N-5 · La consulta de saldo no exige autenticación

`público`. Fuente: [`/bi-puntos`](https://bipuntos.bi.com.gt/bi-puntos), formulario
«Consulta tus Bi Puntos».

El formulario pide tres cosas y devuelve el saldo:

- **Tipo de cliente**: Individual o Empresarial
- **Tipo de documento**: DPI, NIT o Pasaporte
- **Número de documento**

No hay contraseña. El resultado muestra «Puntos Disponibles» y «Puntos a vencer».

Un saldo canjeable consultable contra un identificador nacional, sin más factor, es una
decisión de diseño que merece estar en la conversación. El DPI guatemalteco no es un
secreto: aparece en facturas, contratos y formularios de todo tipo.

**Límites de esta observación, y son importantes.** Se leyó el formulario publicado.
**No se envió ninguna consulta, no se probó ningún número de documento y no se verificó
qué devuelve el sistema.** Es perfectamente posible que exista un control que el
formulario no muestra —un CAPTCHA, un límite de intentos, una verificación adicional
tras el envío—. Lo que aquí se afirma es únicamente que **los campos publicados no
incluyen ningún secreto compartido**. El cliente debe confirmarlo internamente antes
de darle cualquier dimensión.

---

### N-6 · La identidad del portal es compartida con Club Bi

`público`. Fuente: [`/register`](https://bipuntos.bi.com.gt/register).

> Recuerda que al crear tu cuenta en Bi Puntos también podrás ingresar a Club Bi en
> cualquier momento. Si ya te registraste en Club Bi, puedes ingresar a Bi Puntos con
> el mismo usuario.

Esto **matiza H-5**, no lo contradice. No hay dos juegos de credenciales: hay uno solo,
compartido entre los dos portales del programa, y **separado del de Bi en Línea**. La
conclusión de H-5 se mantiene —las protecciones de la banca en línea no aplican a este
almacén de credenciales— pero la descripción había que precisarla.

El alta pide: correo, contraseña, nombre, teléfono (opcional), tipo de cliente, número
de **Tarjeta Club Bi**, tipo y número de documento de identificación, y fecha de
nacimiento.

La política de contraseña, literal del validador publicado, que confirma H-5 palabra
por palabra:

> El campo de contraseña es obligatorio, debe contener mayúscula, minúscula, número,
> carácter especial y **un largo de 4 caracteres como mínimo**.

---

### N-7 · Cada tipo de cuenta tiene su propia regla de acumulación

`público`. Fuente: FAQ de `/about-bi-puntos`, incluida la nota al pie.

> **¿Si realizo depósitos a mis cuentas Monetarias o de Ahorros, acumulo Bi Puntos?**
> No, recuerda que los depósitos a tus cuentas no acumulan Bi Puntos, acumulas Bi
> Puntos por los **saldos promedio** que mantienes en tu Súper Cuenta de Ahorros,
> Súper Cuenta de Monetarios y tu Cuenta de Ahorros 5 estrellas\*.
>
> \* *Cada Cuenta tiene su propia Regla de Acumulación*

Dos cosas nuevas:

1. **Los depósitos no acumulan.** Solo el saldo promedio. Eso
   descarta la interpretación de que la vía de depósitos reaccione a transacciones:
   reacciona únicamente a un cierre de periodo.
2. **La regla es por tipo de cuenta, no una sola.** El banco reconoce por escrito que
   existen tres reglas distintas, y no publica ninguna de las tres.

Esto convierte la pregunta abierta **P-2** de una en tres: hace falta la regla de la
Súper Cuenta Monetaria, la de la Súper Cuenta de Ahorro y la de la Cuenta de Ahorro 5
Estrellas. También refuerza lo que ya decía el caso: es el único mecanismo de acumulación del
programa **sin una sola cifra pública** *(corregido en la tercera ronda, T-2: los
umbrales sí son públicos; lo que falta es la tasa)*, ahora agravado porque sabemos que son tres
cifras las que faltan, no una.

---

### N-8 · Existe cliente empresarial, con su propia tarjeta

`público`. Fuente: `/register` y `/about-bi-puntos`.

El registro y la consulta de saldo ofrecen «Cliente Individual» o «Cliente
Empresarial», y el canje empresarial tiene requisitos propios:

| Quién canjea | Qué presenta |
|---|---|
| Cliente Individual | Club Bi física + documento de identificación |
| **Cliente Empresarial** | **Club Bi Empresarial física** + DPI del Representante Legal + copia de nombramiento vigente |
| Canje de tercero | Club Bi del titular + copia del DPI del titular + copia del DPI de quien canjea + carta de autorización |

Consecuencia para el [modelo de datos](architecture/diagrams/03-modelo-de-datos.md): el
titular de un saldo **no es siempre un grupo familiar**. Puede ser una persona
jurídica, con representante legal y nombramiento con vigencia propia. El modelo actual
solo contempla `GRUPO_FAMILIAR`, y hay que ampliarlo.

---

### N-9 · El portal lo construyó una agencia externa, y lo publica

`público`. Fuente: [`bipuntos.bi.com.gt/humans.txt`](https://bipuntos.bi.com.gt/humans.txt).

El archivo está publicado, es legible sin autenticación, y dice:

```
/* the humans responsible */
/* MilknCookies */

/* TEAM */
    Developer: Luis Fernando Chavarria.
    Developer: Luis Fernando Barrera.
    Development: Carlos Molina.

/* SITE */
    Standards: HTML5, CSS3, Laravel.
    Components: jQuery, Foundation for sites, Slick Carousel.
    Software: Gulp, Bower, SASS, Photoshop, Sublime Text.
```

Dos lecturas, y las dos sirven al encargo.

**La primera es que confirma la premisa del caso.** El encargo dice que los
responsables de diseñar e implementar el sistema ya no trabajan en la empresa. El
portal lleva escrito, en un archivo público, que lo construyó un equipo externo. No es
una suposición del consultor: está publicado.

**La segunda es el stack.** Bower está descontinuado desde 2017 y Foundation for Sites
ya no tiene desarrollo activo. Sirve para fechar el portal, no para juzgarlo — que una
herramienta de construcción esté descontinuada no dice nada sobre si el sistema
funciona. Sí sugiere que **el portal no ha tenido una revisión de plataforma
en varios años**, lo que encaja con la política de contraseña de cuatro caracteres:
no es una decisión reciente, es una decisión antigua que nadie revisitó.

Publicar los nombres del equipo de desarrollo y el inventario de tecnología de un
sistema financiero es información que normalmente no se ofrece. Retirar el
archivo cuesta un `rm`.

---

## 3. Tarifario comparado de los ocho productos

`público`. Fuente: las ocho páginas de producto de `tarjetasbi.com`, bloque de
condiciones. Todas traen el mismo cuadro, así que la comparación es limpia.

| Producto | Interés anual Q | Interés anual $ | Membresía anual | Consumo p/ extorno | Extrafin. mensual | ¿Acumula puntos? |
|---|---|---|---|---|---|---|
| Visa Clásica | **60.00 %** | 33 % | Q420 | Q6,750 | 3.17 % | **Sí** |
| Visa Premier | 48.60 % | 30 % | Q420 | Q20,700 | 2.67 % | **Sí** |
| Visa Platinum | 47.40 % | 27 % | Q610 | Q54,000 | 2.17 % | **Sí** |
| Visa Signature | 40.20 % | 24 % | Q1,200 | Q78,000 | 1.83 % | **Sí** |
| Mastercard Standard | **36.00 %** | 36 % | Q420 | Q6,750 | 3.17 % | No |
| Mastercard Gold Intl. | 32.00 % | 32 % | Q420 | Q3,500 | 2.67 % | No |
| Mastercard Platinum | 27.00 % | 27 % | Q610 | Q54,000 | 2.17 % | No |
| Mastercard Black | 24.00 % | 24 % | Q1,200 | Q78,000 | 1.83 % | No |

### Lo que salta al comparar por pares

Las dos marcas están emparejadas por nivel: misma membresía, mismo consumo para
extorno, mismo extrafinanciamiento. **Lo único que cambia sistemáticamente entre el par
Visa y el par Mastercard es la tasa en quetzales y la acumulación de puntos.**

El par de entrada es el que más dice:

| | Visa Clásica | Mastercard Standard |
|---|---|---|
| Membresía anual | Q420 | Q420 |
| Consumo para extorno | Q6,750 | Q6,750 |
| Extrafinanciamiento | 3.17 % mensual | 3.17 % mensual |
| **Interés anual en quetzales** | **60.00 %** | **36.00 %** |
| **Acumula Bi Puntos** | **Sí** | No |

Veinticuatro puntos porcentuales de diferencia, con todo lo demás igual, y la que
acumula es la cara.

**Para un cliente que financia saldo, el programa no compensa.** Con el punto valuado
en Q0.0619 (N-3), el retorno ronda el 0.8 % del consumo; la diferencia de tasa es de
24 puntos porcentuales sobre el saldo financiado. No hay volumen de consumo razonable
que cierre esa brecha.

**Para un cliente que paga de contado, el razonamiento no aplica** — no paga intereses,
así que la tasa es irrelevante y los puntos son ganancia neta. El hallazgo es
**condicional**, y presentarlo sin esa condición sería deshonesto.

Lo incondicional es esto: **el sitio del banco no da ningún elemento para
hacer esta comparación.** Las tasas están en un micrositio de activación; el valor del
punto, en el portal de puntos; la posibilidad de afiliar una Mastercard, en un blog de
2022. Tres dominios distintos para una sola decisión de compra.

> **Nota de alcance.** Comparar tasas nominales anuales entre productos es una
> aproximación. No se consideraron comisiones, seguros, ni el efecto de los días de
> financiamiento sin intereses, que las fuentes mencionan pero no detallan de forma
> comparable. La tabla sirve para ver la estructura, no para calcular el costo real de
> un cliente concreto.

---

## 4. Contradicciones entre fuentes del propio banco

No son errores de este diagnóstico: son dos canales del emisor diciendo cosas
distintas sobre lo mismo. Cada una es, por sí sola, evidencia adicional de H-2.

| Dato | Una fuente dice | La otra dice |
|---|---|---|
| Establecimientos afiliados | «más de **40** establecimientos» — portal, `/about-bi-puntos` | «más de **50** establecimientos afiliados» — blog, entrada de Mastercard |
| Puntos por certificado de Q100 | **1,615** — portal, 22-09-2026 | **1,595** — PDF de arquitectura del equipo |
| Dónde vive la regla de acumulación | Nota al pie de cada página de producto | La página del programa no la menciona |

La primera es la más significativa. `assumptions.yaml` registraba «más de 50» tomándolo
del blog; el portal del propio programa dice «más de 40». Una de las dos está
desactualizada y no hay forma de saber cuál desde fuera. Ambas quedan registradas en el
catálogo con su fuente.

---

## 5. Discrepancias con el PDF de arquitectura

El [PDF](architecture/diagrams/) es el diagrama oficial de la entrega. Trae datos que
esta ronda no pudo verificar y algunos que contradicen lo documentado. **No se tocó el
PDF**; esto queda anotado para que lo reconcilie quien lo elaboró.

| El PDF dice | Lo que verificó esta ronda | Qué hacer |
|---|---|---|
| «tasa por tier (14-15 pts/US$10)» | 1 punto por US$**1**; 1 punto por US$10 solo en las cinco categorías reducidas | Discrepancia real. 14-15 pts/US$10 equivale a ~1.45 pts/US$, que ninguna fuente sostiene. Hay que revisar de dónde salió |
| «1595 pts = Q100» | 1,615 pts = Q100 (portal, 22-09-2026) | Probablemente una lectura anterior del mismo catálogo. Fechar ambas |
| «+40 centros de canje afiliados (POS)» | «más de 40» (portal) / «más de 50» (blog) | Coincide con el portal. Ver sección 4 |
| «NeoNet: autorización y liquidación Visa/Mastercard» | No verificado en esta ronda | Plausible como red de autorización regional; hace falta su fuente |
| «Motor de campañas ML … (Enciende tu Racha)» | No verificado en esta ronda | Si existe la campaña, hace falta su fuente; si el motor de ML es propuesta, hay que marcarlo como tal en el dibujo |
| «App Mi Club Bi» | Las fuentes leídas dicen «App Club Bi» | Probablemente el mismo producto; unificar el nombre |

La primera fila es la única que importa de verdad: **cambia la tasa base del sistema**,
que es el parámetro del que cuelga todo el diagnóstico y todo el POC.

---

## 6. Supuestos del equipo

Separados a propósito de todo lo anterior. **Ninguno de estos es un dato del sistema**,
y ningún entregable los presenta como tal. Cada uno lleva qué lo tumbaría.

| # | Supuesto | Por qué se eligió | Qué lo tumbaría |
|---|---|---|---|
| S-1 | Tipo de cambio de referencia ~Q7.70/US$ para las ilustraciones de retorno | Hace falta un número para expresar el retorno en porcentaje; sin él, N-3 no se puede comunicar | Que el banco publique su tipo de cambio de acumulación (P-3). Las conclusiones son robustas a cualquier valor razonable |
| S-2 | El certificado de Q100 es representativo del catálogo | Es el premio que el propio portal destaca en portada | Que el catálogo completo muestre tasas muy distintas por comercio. El PDF sugiere que las hay («tasas por comercio») |
| S-3 | Las tasas del blog de 2022 no son comparables con el tarifario de 2026 | Cuatro años de diferencia y ninguna indicación de vigencia en el blog | Que el banco confirme que las condiciones de afiliación siguen siendo esas |
| S-4 | La acreditación de 48–72 h aplica a todas las vías, no solo al consumo | La FAQ responde sobre compras, pero un motor por lotes difícilmente tendría dos relojes | Una fuente que documente latencias distintas por vía |
| S-5 | El «canje en línea» del portal ejecuta canjes reales, no solo reservas | Es lo que el nombre del menú indica | Requiere una cuenta para verificarlo, y no se usó ninguna |

---

## 7. Preguntas abiertas nuevas

Se añaden a las seis de
[`config/assumptions.yaml`](../config/assumptions.yaml). Mismo formato: qué se pregunta
y por qué cambia el diagnóstico la respuesta.

**P-7 · Al afiliar una Mastercard a Bi Puntos, ¿la tasa sube, baja o se mantiene?**
El blog de 2022 enuncia las tasas «al momento de realizar la gestión» (Standard y Gold
2.5 % mensual, Platinum 2.2 %, Black 2.0 %), pero no dice contra qué se comparan. Frente
al tarifario vigente, 2.5 % mensual es *menos* que el 36 % anual de la Standard actual.
El caso afirmaba que afiliarse encarece el crédito; la evidencia no lo sostiene en
ninguna dirección. Es un dato que un cliente necesita antes de tomar una decisión
irreversible por teléfono.

**P-8 · ¿Qué parte del catálogo admite canje en línea?**
El portal tiene un menú «Canje en línea» tras iniciar sesión, y a la vez toda la
documentación pública describe el canje como presencial. Si el canje digital existe y
funciona, el programa tiene un canal que no comunica. Si existe pero solo para parte
del catálogo, hace falta saber cuál.

**P-9 · ¿Cuál es la regla de acumulación de cada tipo de cuenta?**
El banco reconoce por escrito que son tres reglas distintas (N-7) y no publica ninguna.
Sin ellas no se puede responder si el programa premia gastar o ahorrar.

**P-10 · ¿Por qué las páginas de producto Mastercard no mencionan Bi Puntos?**
Ni para decir que no acumulan, ni para decir que se puede solicitar. Si es una decisión
comercial deliberada, hay que saberlo; si es una omisión, es un beneficio que el banco
ofrece y no vende.

**P-11 · ¿Qué controles protegen la consulta de saldo sin autenticación?**
Se observó el formulario, no su comportamiento (N-5). La pregunta no es retórica: la
respuesta decide si esto es una observación de diseño o algo que atender.

---

## 8. Qué cambió en el resto del caso

Esta ronda no solo añadió: corrigió. Las correcciones aplicadas a raíz de este
documento:

| Documento | Qué cambió | Por |
|---|---|---|
| [`report/02-reglas-del-programa.md`](report/02-reglas-del-programa.md) §2.5 | «El programa de lealtad es una suscripción de pago» → separación de Bi Puntos (gratuito) y Club Bi (Q15/mes) | N-1 |
| [`report/02-reglas-del-programa.md`](report/02-reglas-del-programa.md) §2.1 | Consumo con tarjeta: «tiempo real» → 48–72 h hábiles | N-2 |
| [`report/02-reglas-del-programa.md`](report/02-reglas-del-programa.md) | Afiliación Mastercard: se retira la afirmación de que encarece el crédito | P-7 |
| [`report/03-hallazgos.md`](report/03-hallazgos.md) H-5 | Identidad compartida, no duplicada; se añade la consulta sin autenticar | N-5, N-6 |
| [`report/03-hallazgos.md`](report/03-hallazgos.md) H-7 | El rasgo distintivo del sorteo es la irreproducibilidad, no la latencia | N-2 |
| [`report/03-hallazgos.md`](report/03-hallazgos.md) H-8 | «Un solo canal de canje» → tres vías con documentación desigual | P-8 |
| [`config/assumptions.yaml`](../config/assumptions.yaml) | Latencia, valor del punto, canales de canje, costos, reglas por cuenta, identidad, P-7 a P-11 | Todo lo anterior |

---

## 9. Índice de fuentes de esta ronda

Todas consultadas el **22 de septiembre de 2026**.

| Fuente | Qué aportó |
|---|---|
| [`bipuntos.bi.com.gt`](https://bipuntos.bi.com.gt/) | Valor del punto (1,615 = Q100); «más de 40 establecimientos» |
| [`/about-bi-puntos`](https://bipuntos.bi.com.gt/about-bi-puntos) | N-1, N-2, N-7, N-8. La FAQ es la fuente más densa del programa |
| [`/bi-puntos`](https://bipuntos.bi.com.gt/bi-puntos) | N-5: consulta de saldo sin autenticación |
| [`/register`](https://bipuntos.bi.com.gt/register) | N-6: identidad compartida; política de contraseña literal |
| [`/miles`](https://bipuntos.bi.com.gt/miles) | Conversión a millas por paquetes; canje telefónico al 1717; «puede variar según el producto» |
| [`/humans.txt`](https://bipuntos.bi.com.gt/humans.txt) | N-9: agencia externa y stack |
| `tarjetasbi.com` · 8 páginas de producto | Tarifario completo; N-4 (ausencia verificada en las cuatro Mastercard) |
| [Blog · Mastercard y Bi Puntos](https://blog.corporacionbi.com/productos-servicios/acumula-mas-bi-puntos-con-tus-tarjetas-de-credito-bi-mastercard) | Tasas al afiliar; irreversibilidad; «más de 50 establecimientos»; «la acumulación dependerá de la categoría de tarjeta y el lugar del consumo» |
| `www.corporacionbi.com` | **No legible programáticamente.** Topes anuales recuperados vía resultados indexados |

El resto de fuentes del caso, de la primera ronda, están en
[`report/05-referencias.md`](report/05-referencias.md).

---

# Tercera ronda · las vías de acumulación

Consultada el **22 de septiembre de 2026**. Esta ronda tuvo un objetivo
estrecho: **cerrar la pregunta de cómo se ganan puntos**, que las dos anteriores
habían dejado a medias. El reporte describía cuatro vías y resulta que el
programa comunica ocho.

Los hallazgos se numeran `T-*`.

| # | Hallazgo | Confianza | Corrige |
|---|---|---|---|
| T-1 | Son ocho vías de acumulación, no cuatro | `público` | §2.1 del reporte |
| T-2 | Los umbrales de saldo promedio **sí** son públicos: Q500 / Q1,000 / Q1,000 | `público` | §2.1, que afirmaba «no hay ni una cifra» |
| T-3 | La membresía Club Bi da **dobles puntos** sobre el saldo promedio | `público` | §2.5 y `costos` |
| T-4 | Los comercios aliados son una vía propia, con tres listas públicas que no coinciden | `público` | — (vía nueva) |
| T-5 | La Tarjeta Prepago Club Bi acumula | `público` | — (vía nueva) |
| T-6 | La afiliación Mastercard se pide por agencia **o** Contact Center | `público` | Matiza el canal |
| T-7 | Dos referencias cruzadas equivocadas en el reporte | — | §2.2 y §2.4 |

---

## T-1 · Son ocho vías, no cuatro

`público`. Fuente: [preguntas frecuentes de Club Bi](https://www.corporacionbi.com/gt/bancoindustrial/preguntas-frecuentes-club-bi/).

> ***¿Cómo acumulas Puntos Bi?** Utilizando las tarjetas de crédito y débito
> Visa, tarjetas débito MasterCard, Saldo promedio en Super Cuenta Monetaria y
> Ahorro, Cuenta Ahorro 5 Estrellas, todos los consumos que realizados con
> Divídelo Todo, consumiendo en comercios aliados (La Torre, Cemaco), Tarjetas
> de crédito MasterCard se deberá de solicitar por medio de agencia o Contact
> Center para acumular.*

Es la **única fuente que enumera todas las vías en un solo lugar**, y no está en
la página del programa: está en el FAQ de Club Bi, que es un programa distinto.
Evidencia adicional de H-2.

Corroborada por la infografía del boletín del blog, «Conoce los productos con lo
que puedes acumular Puntos Bi», que añade la prepago y amplía la lista de
comercios.

**Por qué el reporte decía cuatro.** Porque estaba contando *tuberías*, no
productos, y no lo decía. Las dos lecturas son correctas y responden preguntas
distintas; §2.1 ahora las separa explícitamente. Seis de las ocho vías entran
por el autorizador de tarjetas, así que lo que las diferencia no es la
infraestructura sino el motor de reglas.

---

## T-2 · Los umbrales de saldo sí son públicos

`público`. Fuentes: las tres páginas de producto.

| Cuenta | Cita literal |
|---|---|
| Súper Cuenta de Ahorro | «Ganas Bi Puntos sobre tu saldo promedio mensual mayor a **Q500.00**» |
| Súper Cuenta Monetaria | «Ganas Bi Puntos sobre tu saldo promedio mensual mayor a **Q1,000.00**» |
| Cuenta de Ahorro 5 Estrellas | «Puntos Bi por saldo promedio mensual a partir de **Q.1,000.00**» |

**Esto corrige el reporte.** §2.1 afirmaba: «*Y ahí se acaba lo público. No hay
ni una cifra.*» Sí la hay. Lo que no es público es la **tasa**, no el umbral.

La corrección no debilita el hallazgo, lo afila: se sabe desde dónde se empieza
a acumular y no se sabe cuánto se acumula, que es la mitad que le sirve al
cliente. Que los tres umbrales sean distintos **confirma desde fuera** lo que
el asterisco del FAQ admite: son tres reglas, no una.

Detalle lateral: el umbral de la Súper Cuenta Monetaria (Q1,000) coincide con su
depósito de apertura y con el saldo desde el que capitaliza intereses. Sugiere
que el umbral de puntos reutiliza un parámetro que ya existía en el producto, lo
que sería una decisión sensata y también una que nadie documentó.

---

## T-3 · La membresía duplica los puntos del saldo promedio

`público`, y con **contradicción entre fuentes del emisor**.

| Fuente | Qué dice |
|---|---|
| Preguntas frecuentes de Club Bi | hay que mantener la membresía activa para gozar de dobles Bi Puntos en la **Supercuenta de Ahorros** |
| [Página de Bi Puntos](https://www.corporacionbi.com/gt/bancoindustrial/bi-puntos/) | «Si tienes membresía Club Bi activa, acumulas dobles Bi Puntos con tu **cuenta monetaria**» |

**Corrige §2.5.** El reporte concluía que la membresía «no compra el acceso al
programa base, pero condiciona el acceso a la capa promocional». Es incompleto:
la membresía compra un **multiplicador permanente** sobre una vía de
acumulación, no solo acceso a promociones temporales.

La pregunta económica queda sin respuesta posible. Ya no es «¿vale la pena
pagar Q180 al año por descuentos?», es «¿vale la pena por descuentos **más el
doble de puntos sobre mi saldo promedio**?». No se puede contestar: duplicar una
tasa desconocida (T-2) sigue siendo desconocido. Es la pregunta **P-12**.

---

## T-4 · Comercios aliados: tres listas que no coinciden

`público`. Es una vía propia y no una variante del consumo con tarjeta: el
premio lo origina el comercio, lo que implica un acuerdo comercial y una regla
por comercio que el motor tiene que resolver.

> «Obtienes Puntos Bi **adicionales** al consumir con Tarjetas Bi en los
> comercios» — infografía del boletín

| Fuente | Comercios |
|---|---|
| Infografía del boletín | Cemaco, La Torre, Electrónica Panamericana, La Curacao |
| Página de Bi Puntos | Max, Cemaco, La Torre |
| Preguntas frecuentes de Club Bi | La Torre, Cemaco |

Tres listas distintas del mismo emisor, leídas el mismo día, y ninguna tasa.
Se suma a las contradicciones ya registradas en la sección 4 (40 contra 50
establecimientos; 1,595 contra 1,615 puntos). Es la pregunta **P-13**.

---

## T-5 · La Tarjeta Prepago Club Bi acumula

`público`. Fuente: [blog corporativo](https://blog.corporacionbi.com/productos-servicios/tu-club-bi-tambien-es-prepago).

> pagar con la prepago Club Bi y «acumular Bi Puntos, en más de **1,000
> establecimientos** que cuenten con POS Visa»

Importa porque rompe un supuesto implícito del caso: que acumular exige una
relación de crédito o una cuenta de depósito. Un instrumento prepago,
recargable en agencias y en puntos «Tu Bi Aquí», también genera saldo de puntos.
Sin tasa publicada.

---

## T-6 · La afiliación Mastercard no es solo telefónica

`público`. El FAQ de Club Bi dice «por medio de **agencia o Contact Center**».
El blog de 2022 solo mencionaba el 1717. No cambia ninguna conclusión —la
decisión sigue siendo irreversible y sigue sin aparecer en las páginas de
producto (N-4)— pero el canal estaba descrito de menos.

---

## T-7 · Dos referencias cruzadas equivocadas

No es investigación, es revisión. Al cotejar el reporte contra
[`report/03-hallazgos.md`](report/03-hallazgos.md) aparecieron dos remisiones a
hallazgos que no son los que dicen:

| Dónde | Decía | Debe decir |
|---|---|---|
| §2.2, vigencia de 13 a 25 meses | «hallazgo H-2» | **H-3** |
| §2.4, los puntos no son intercambiables | «hallazgo H-4» | **H-1** |

Las dos están corregidas. Se deja anotado porque, en un reporte que se apoya en
remitir al hallazgo correcto, una referencia cruzada mal puesta manda al lector
a un argumento distinto del que sostiene la frase.

---

## Lo que esta ronda buscó y no encontró

Se buscó específicamente la **tasa de acumulación por saldo promedio** —cuántos
puntos por cada cuánto de saldo— en: las tres páginas de producto, el FAQ del
portal, el FAQ de Club Bi, la página de Bi Puntos del sitio principal, el
boletín del blog y su infografía, y el portal de puntos. **No está publicada en
ninguna.** La pregunta P-2 sigue abierta, ahora mejor acotada: falta la tasa,
no el umbral.

También se intentó leer la infografía del boletín como imagen, porque el lector
de páginas no transcribe texto embebido. Se leyó completa y se transcribió su
contenido arriba: enumera productos, no tasas.

## Fuentes de esta ronda

Todas consultadas el **22 de septiembre de 2026**.

| Fuente | Qué aportó |
|---|---|
| [FAQ de Club Bi](https://www.corporacionbi.com/gt/bancoindustrial/preguntas-frecuentes-club-bi/) | T-1, T-3, T-6. La enumeración completa de vías |
| [Página de Bi Puntos](https://www.corporacionbi.com/gt/bancoindustrial/bi-puntos/) | T-3, T-4. Dobles puntos por membresía |
| [Súper Cuenta Ahorro](https://www.corporacionbi.com/gt/bancoindustrial/super-cuenta-ahorro/) | T-2. Umbral de Q500 |
| [Súper Cuenta Monetaria](https://www.corporacionbi.com/gt/bancoindustrial/super-cuenta-monetaria/) | T-2. Umbral de Q1,000 |
| [Ahorro 5 Estrellas](https://www.corporacionbi.com/gt/bancoindustrial/cuentas-de-ahorro-personales/ahorro-5-estrellas/) | T-2. Umbral de Q1,000 |
| [Boletín «¿Cómo acumulas Puntos Bi?»](https://blog.corporacionbi.com/productos-servicios/boletin-como-acumular-bi-puntos) | T-1, T-4. Infografía de productos |
| [«Tu Club Bi también es Prepago»](https://blog.corporacionbi.com/productos-servicios/tu-club-bi-tambien-es-prepago) | T-5 |

Nota de método: en esta ronda `www.corporacionbi.com` **sí** respondió a lectura
programática, a diferencia de la segunda ronda, donde devolvía el marco de
bloqueo de Imperva (sección 1). La protección parece aplicarse de forma
intermitente o por ruta. No se intentó evadir nada en ninguna de las dos.
