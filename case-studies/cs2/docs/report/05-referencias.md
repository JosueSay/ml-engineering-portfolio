# Referencias

Las fuentes del diagnóstico, con qué aportó cada una y qué buscamos en ella sin
encontrarlo. Todas son públicas y todas son de Corporación BI, salvo donde se
indica. La fecha de consulta del catálogo completo es el **22 de septiembre de
2026**.

Cada afirmación del reporte se puede rastrear desde
[`config/assumptions.yaml`](../../config/assumptions.yaml) hasta una de estas
nueve fuentes.

## Por qué esta tabla incluye lo que no se encontró

En un diagnóstico normal las referencias listan de dónde salió cada dato. Aquí
tienen una segunda función, porque el caso trata sobre información que el banco no
publica: **una ausencia solo es un hallazgo si se registra dónde se buscó.**

Decir "el banco no publica la tasa de acumulación por saldo promedio" no vale
nada por sí solo. Vale cuando se puede decir en qué tres páginas de producto, en
qué portal y en qué preguntas frecuentes se buscó. Por eso cada fuente declara
también qué se le preguntó sin respuesta.

## Las fuentes

### F-1. Páginas de producto de tarjetas de crédito y débito

**Dónde:** `tarjetasbi.com`, ocho páginas de producto, una por categoría de
tarjeta.

**Qué aportó.** Es la fuente más productiva del caso y la que nadie leería
esperando encontrar la regla del programa.

- La tasa base, enunciada producto por producto: "acumulas Puntos Bi por cada
  dólar de compra".
- La tasa reducida, en una nota al pie con asterisco idéntica en cuatro páginas:
  las cinco categorías de supermercados, gasolineras, tiendas de conveniencia,
  entidades de beneficencia y centros educativos.
- Los topes anuales de cuatro categorías: Mastercard Gold Internacional y Visa
  Premier con 180,000 puntos, Visa Signature con 360,000, Visa Infinite con
  420,000.
- El tarifario completo, en el mismo cuadro en las ocho páginas, lo que permite
  comparar sin ajustes.

**Qué se buscó y no estaba.** El tope anual de Visa Clásica, Visa Platinum,
Mastercard Standard, Platinum y Black, y de las tarjetas de débito. Esas páginas
solo dicen que acumulan Bi Puntos canjeables en establecimientos afiliados. Es la
ausencia verificada que sostiene una parte de H-2.

### F-2. Portal de Bi Puntos

**Dónde:** `bipuntos.bi.com.gt`, portada, preguntas frecuentes, alta de usuario y
menú de canje.

**Qué aportó.**

- El primer y único valor monetario del punto: 1,615 puntos por un certificado de
  regalo de Q100, en el bloque de premios destacados.
- La latencia de acreditación: "el proceso de acreditación de Bi Puntos puede
  variar y en la mayoría de los casos tarda entre 48 y 72 horas (días hábiles)".
- Que participar en Bi Puntos es gratuito y es un programa distinto de la
  membresía Club Bi. Esto corrigió un error del propio equipo, registrado en la
  bitácora.
- La existencia del canje en línea, por la entrada de menú y el aviso de que hay
  que iniciar sesión para canjear.
- Que el portal tiene identidad propia, distinta de la de Bi en Línea, con alta y
  recuperación de contraseña separadas.
- La política de contraseñas: exige cuatro clases de carácter y admite un mínimo
  de cuatro caracteres. Es H-5.

**Qué se buscó y no estaba.** Qué parte del catálogo admite el canje en línea, y
la regla de acumulación completa. La página del programa no enuncia ni la tasa base
ni la reducida.

**Advertencia de vigencia.** El catálogo de premios cambia. La cifra de 1,615
puntos es una lectura fechada y hay que releerla antes de reutilizarla: el PDF de
arquitectura del equipo registra 1,595 para el mismo certificado, probablemente de
una lectura anterior.

### F-3. Página del programa Bi Puntos

**Qué aportó.**

- Que se pueden obtener certificados de regalo desde Q100, lo que confirma F-2.
- Que con membresía Club Bi activa se acumulan dobles Bi Puntos "con tu cuenta
  monetaria".
- Una de las tres listas de comercios aliados: Max, Cemaco, La Torre.

**Por qué importa que se contradiga con F-4.** Esta fuente dice que el doble aplica
a la cuenta monetaria y las preguntas frecuentes de Club Bi dicen que aplica a la
Súper Cuenta de Ahorros. Son dos fuentes del mismo emisor discrepando sobre un
multiplicador de dos. Es la pregunta abierta P-12.

### F-4. Preguntas frecuentes de Club Bi

**Qué aportó.** Es la única fuente que intenta enumerar las vías de acumulación de
una sola vez, y por eso es la base de la reconstrucción:

- La enumeración de las ocho vías: tarjetas Visa de crédito y débito, débito
  Mastercard, saldo promedio en tres cuentas, Divídelo Todo, comercios aliados, y
  crédito Mastercard "se deberá de solicitar por medio de agencia o Contact Center
  para acumular".
- Que los depósitos no acumulan: "recuerda que los depósitos a tus cuentas no
  acumulan Bi Puntos, acumulas Bi Puntos por los saldos promedio que mantienes".
- El asterisco que reconoce que hay tres reglas y no una: "Cada Cuenta tiene su
  propia Regla de Acumulación".
- La unificación familiar: parentescos admitidos, cónyuge con acta matrimonial,
  permanencia mínima de un año, y que solo el titular puede canjear.
- Los requisitos de canje para titular, tercero y empresa.
- Otra de las tres listas de comercios aliados: La Torre y Cemaco.

**Qué se buscó y no estaba.** La tasa de ninguna de las siete vías que no son
tarjeta Visa. De las ocho vías, una sola publica su tasa.

### F-5. Página de Club Bi

**Qué aportó.** El costo de la membresía: "La membresía Club Bi tiene un costo de
Q15.00 mensuales", es decir Q180 al año. Y que corresponde al programa de
beneficios y descuentos, no al de puntos.

### F-6. Páginas de producto de cuentas de depósito

**Qué aportó.** Los tres umbrales de saldo promedio mensual desde los que se
empieza a acumular, cada uno en la página de su producto: Súper Cuenta de Ahorro
desde más de Q500, Súper Cuenta Monetaria desde más de Q1,000, Cuenta de Ahorro 5
Estrellas a partir de Q1,000.

**Qué se buscó y no estaba.** La tasa. Ninguna de las tres páginas dice cuántos
puntos genera cuánto saldo. Se sabe desde dónde se empieza a acumular y no cuánto
se acumula, que es justo la mitad que le sirve al cliente. Es P-2, la pregunta
abierta con más consecuencias del caso.

### F-7. Portal de conversión a millas

**Qué aportó.**

- Que el socio es LifeMiles.
- Que la conversión "puede variar según el producto con el que acumules Bi
  Puntos". Es el hallazgo central del caso, H-1.
- Que el canje de millas se hace por teléfono: "Para canjear tus puntos llama al
  1717".

**Qué se buscó y no estaba.** Las tasas. Que varíen es público; cuánto varían, no.
Es P-5.

### F-8. Bases de tres promociones

**Qué aportó.** La capa de reglas temporales, que es la parte del sistema que más
maquinaria exige y la menos documentada:

- Un multiplicador que no multiplica sino que **sustituye la tasa y le cambia la
  moneda**: un punto por quetzal, cerca de ocho veces la tasa base.
- Una bonificación con su padrón de inscritos.
- Un sorteo con vigencia, consumo mínimo de Q100, premios diarios, semanales y
  mensuales de 500 a 50,000 puntos, acreditación 48 horas después de la
  notificación por SMS, y exigencia de Bi Móvil activo. Es la evidencia de H-7.
- Las dos únicas exclusiones publicadas: "No aplica para retiros o extra
  financiamientos".

**Qué se buscó y no estaba.** El listado general de exclusiones del programa. Las
dos que existen están dentro de las bases de una promoción concreta, lo que sugiere
que la regla general no está escrita en ningún lado. Es P-6.

### F-9. Infografía del boletín del blog

**Qué aportó.** Una enumeración de vías que cruza con F-4 y agrega la Tarjeta
Prepago Club Bi y el consumo en más de 1,000 puntos de venta Visa. Y la tercera
lista de comercios aliados: Cemaco, La Torre, Electrónica Panamericana, La Curacao.

**Advertencia.** Es la fuente más débil del conjunto: un blog de 2022. Hay un dato
que vive únicamente ahí, el PBX 1717 como canal de consulta, y por eso se registró
como pregunta abierta P-10 en vez de como hecho. Ninguna afirmación del reporte se
apoya solo en F-9.

## Las tres listas de comercios aliados

Vale reunirlas, porque la discrepancia es en sí misma un hallazgo y se aprecia mejor
junta:

| Fuente | Comercios |
| --- | --- |
| F-9, infografía del blog | Cemaco, La Torre, Electrónica Panamericana, La Curacao |
| F-3, página de Bi Puntos | Max, Cemaco, La Torre |
| F-4, preguntas frecuentes de Club Bi | La Torre, Cemaco |

Tres fuentes del mismo emisor y ninguna coincide con otra. Y ninguna publica cuánto
acreditan de más. Si el motor aplica un factor por comercio, la lista es parte de la
regla de acumulación y hoy no se puede reconstruir desde fuera. Es P-13.

## Pendiente de esta sección

**Los enlaces exactos.** Este documento registra las fuentes como las registró el
catálogo: por qué son, dónde viven y qué aportaron. Los enlaces profundos a cada
página concreta los tiene que anotar quien hizo la consulta.

No los inventamos, y conviene decir por qué: un enlace fabricado que resulta no
existir invalida la fuente entera ante el cliente, y con ella el hallazgo que se
apoyaba en ella. Es exactamente el tipo de atajo que el caso se prohíbe, y el
reporte no puede predicar trazabilidad y a la vez rellenar sus propias citas.

**Una relectura antes de la entrega.** El catálogo de premios y las promociones
cambian. Antes de entregar hay que reconfirmar al menos F-2, que es la fuente de la
única cifra monetaria del caso, y anotar la nueva fecha de consulta.
