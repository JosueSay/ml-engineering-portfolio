# Bitácora de investigación y supuestos

Registro de campo. Qué se buscó, qué se encontró, qué hubo que corregir y en qué
se contradicen las fuentes entre sí.

Este documento no es un entregable pulido: es el rastro del trabajo. Existe por
dos razones. La primera es que un diagnóstico sobre información ausente tiene que
poder demostrar **dónde buscó**, o sus ausencias no valen nada. La segunda es que
el equipo se equivocó dos veces y las dos veces se corrigió leyendo mejor; dejar
eso escrito es más útil para quien herede el caso que presentar el resultado como
si hubiera salido bien de una sola vez.

La sección 7 es la que el resto del caso cita: las preguntas abiertas P-7 a P-11,
que nacieron en la segunda ronda y no se duplican en
[`config/assumptions.yaml`](../config/assumptions.yaml) para que cada pregunta
tenga un solo lugar donde se mantiene.

## 1. Cómo se organizó la búsqueda

Tres rondas, y cada una tuvo un propósito distinto.

| Ronda | Qué se buscaba | Con qué se volvió |
| --- | --- | --- |
| Primera | La regla de acumulación y el costo de participar | La tasa base, la tasa reducida, los topes de cuatro categorías, la vigencia |
| Segunda | Verificar lo de la primera ronda cruzando fuentes | Tres correcciones a afirmaciones propias que eran falsas |
| Tercera | Cerrar los huecos que dejaron las dos anteriores | Tres vías de acumulación que no se habían visto |

El patrón vale anotarlo: **la segunda ronda no agregó información, quitó error.**
Y fue la más productiva del caso, porque las tres cosas que corrigió eran
afirmaciones que ya estaban escritas en el catálogo y que se habrían presentado al
cliente como hallazgos.

## 2. Primera ronda: la regla existe pero no vive en un solo lugar

Lo primero que se buscó fue la página donde el banco enuncia la regla del
programa. No existe. La página del programa describe los premios y no dice cuántos
puntos se ganan por cuánto consumo.

La tasa apareció donde nadie la buscaría: en las páginas de producto de cada
tarjeta, enunciada producto por producto, y la excepción en una nota al pie con
asterisco repetida en cuatro de ellas. Reconstruir la regla completa exigió cruzar
cuatro páginas de tarjeta.

Ese hecho se convirtió en el hallazgo H-2, y es el que reencuadró el caso entero:
el problema del cliente no es que su sistema esté mal documentado, es que **la
regla nunca fue un documento.**

## 3. Segunda ronda: las tres correcciones

### 3.1 El programa no cuesta Q180 al año

**Lo que el catálogo afirmaba:** que participar en Bi Puntos es una suscripción de
pago de Q180 al año.

**Lo que dice la fuente:** lo contrario, y es explícito. Las preguntas frecuentes
del portal dicen que aún se puede canjear sin membresía, "ya que el Programa de Bi
Puntos es ajeno al Programa de beneficios que otorga Club Bi al pagar tu
membresía".

**De dónde vino el error.** Son dos programas distintos que comparten nombre
comercial, tarjeta física y usuario del portal. Leer "Club Bi" en los dos lados y
asumir que es lo mismo es el error natural, y probablemente lo comete también
cualquier cliente del banco.

**Qué sobrevivió del error.** Tres matices que sí se sostienen: la Tarjeta Club Bi
física sigue siendo obligatoria para canjear, varias promociones exigen membresía
vigente, y —esto apareció en la tercera ronda— la membresía compra un
multiplicador permanente sobre una de las vías de acumulación. Así que la
membresía no compra el acceso al programa base, pero tampoco es solo un descuento.

### 3.2 Afiliarse a la acumulación Mastercard no encarece el crédito

**Lo que el catálogo afirmaba:** que solicitar la acumulación de puntos en una
tarjeta de crédito Mastercard encarece el crédito.

**Lo que dice la fuente:** un blog corporativo de enero de 2022 enuncia la "tasa
de interés mensual del producto al momento de realizar la gestión", con cifras
entre 2.0% y 2.5% mensual según la categoría. No dice contra qué se compara.

**Por qué el error era grave.** Frente al tarifario actual, 2.5% mensual sobre una
Mastercard Standard es **menos** que lo que hoy publica ese producto. Pero las dos
cifras son de años distintos y no son comparables limpiamente, así que la
conclusión correcta no es la inversa del error: es que **no se puede concluir**.

**Qué sí quedó sostenido.** Que la conversión cambia las condiciones del producto
de forma irreversible, y que la decisión se toma por teléfono o en agencia. Eso
basta para que sea un problema, y no hace falta exagerarlo. Ver P-7.

### 3.3 Hay tres canales de canje, no uno

**Lo que el catálogo afirmaba:** un único canal, presencial.

**Lo que se encontró.** Tres: el presencial, uno en línea en el portal y uno
telefónico por el 1717 para la conversión a millas. Los dos últimos no están
documentados: el canje en línea se deduce de que el portal tiene la entrada de
menú y el aviso de que hay que iniciar sesión para canjear, y el telefónico de una
frase del portal de millas.

**Por qué importa más de lo que parece.** El error propio reprodujo exactamente el
problema del cliente. Toda la documentación pública describe el mostrador, así que
leer la documentación y concluir que hay un solo canal es lo que haría cualquiera.
Es H-8, y la forma en que se descubrió es parte de su evidencia.

## 4. Tercera ronda: tres vías que no se habían visto

Las tres cambian el tamaño del sistema, no un detalle.

**Comercios aliados.** Consumir con Tarjetas Bi en ciertos comercios da puntos
**adicionales** a los de la tarjeta. Es una vía distinta y no una variante del
consumo, porque el premio lo origina el comercio y no el producto bancario: eso
implica un acuerdo comercial y una regla por comercio dentro del motor.

**Tarjeta Prepago Club Bi.** Acumula en más de 1,000 establecimientos con punto de
venta Visa. Rompe el supuesto de que acumular exige una relación de crédito o una
cuenta de depósito: un instrumento prepago, recargable en agencia, también genera
saldo de puntos.

**Multiplicador por membresía.** Pagar la membresía duplica los puntos que genera
el saldo promedio. Esto es lo que corrigió el alcance de 3.1: la membresía compra
un multiplicador permanente sobre una vía de acumulación, no solo acceso a
promociones temporales.

Ninguna de las tres publica su tasa.

## 5. Las contradicciones entre fuentes del mismo emisor

Todas leídas el mismo día. No son erratas de redacción: son reglas del sistema
sobre las que el banco dice dos cosas.

| Tema | Una fuente dice | Otra dice |
| --- | --- | --- |
| Sobre qué cuenta aplica el doble por membresía | Preguntas frecuentes de Club Bi: Súper Cuenta de Ahorros | Página de Bi Puntos: cuenta monetaria |
| Cuáles son los comercios aliados | Infografía: Cemaco, La Torre, Electrónica Panamericana, La Curacao | Página de Bi Puntos: Max, Cemaco, La Torre. Preguntas frecuentes: La Torre, Cemaco |
| Cuántos puntos vale el certificado de Q100 | Portal, 22 de septiembre de 2026: 1,615 | PDF de arquitectura del equipo: 1,595 |
| Por dónde se solicita la afiliación Mastercard | Blog de 2022: llamando al 1717 | Preguntas frecuentes: agencia o Contact Center |

La primera es la más costosa para el cliente: un cliente que paga la membresía
para duplicar sus puntos no puede saber en cuál de sus cuentas conviene dejar el
saldo. La tercera es un recordatorio de vigencia, no una contradicción real: el
catálogo de premios cambia y hay que releerlo antes de reutilizar la cifra.

## 6. Las ausencias verificadas

Lo que se buscó y no está. Cada una dice dónde se buscó, porque sin eso una
ausencia es solo una búsqueda incompleta.

| Qué falta | Dónde se buscó |
| --- | --- |
| La tasa de acumulación por saldo promedio | Las tres páginas de producto de cuentas, el portal y las preguntas frecuentes de dos programas |
| El tope anual de seis categorías de tarjeta | Las ocho páginas de producto de `tarjetasbi.com` |
| Las tasas de conversión a millas por producto | El portal de millas, que confirma que varían y no dice cuánto |
| El listado general de exclusiones del programa | Las bases de tres promociones y la página del programa |
| Qué parte del catálogo admite el canje en línea | El portal, que tiene la funcionalidad y no describe su alcance |
| El mapa de códigos de rubro a las cinco categorías de tasa reducida | Todas las fuentes. El banco nombra las categorías, no los códigos |
| La política de tipo de cambio | Todas las fuentes. La regla está en dólares y el consumo se liquida en quetzales |

Las siete comparten una forma: **el banco publica la mitad que no le sirve al
cliente para decidir.** Publica desde qué saldo se empieza a acumular y no cuánto;
publica que la conversión a millas varía y no cuánto; publica que hay comercios
aliados y no cuáles ni a qué tasa.

## 7. Preguntas abiertas nacidas en la segunda ronda

Estas cinco completan el cuestionario al cliente, que son trece con las seis del
catálogo y las dos que se agregaron en la tercera ronda. Cada una nace de un
hallazgo concreto de esta bitácora.

### P-7. La afiliación Mastercard es irreversible y se decide por teléfono. ¿Qué información recibe el cliente antes de decidir?

**De dónde nace:** de la corrección 3.2. Lo que quedó sostenido es que la
conversión no se deshace sin emitir una tarjeta nueva, y que la gestión se hace por
teléfono o en agencia.

**Por qué importa:** una decisión irreversible sobre las condiciones de un producto
de crédito, tomada en una llamada, exige que el cliente sepa exactamente qué
cambia. Hoy no se puede saber desde fuera si eso ocurre, y el blog que menciona la
tasa es de 2022.

### P-8. ¿Qué parte del catálogo admite el canje en línea?

**De dónde nace:** de la corrección 3.3. El portal tiene la funcionalidad y el
aviso de que hay que iniciar sesión para canjear, y ninguna fuente describe su
alcance.

**Por qué importa:** si el canje en línea cubre todo el catálogo, comunicarlo es
probablemente la mejora de costo operativo más barata del programa, porque el canal
presencial exige que el cliente se presente con tarjeta física y documento de
identificación. Es la parte accionable de H-8.

### P-9. ¿Los consumos hechos con una Mastercard antes de solicitar la afiliación se acreditan retroactivamente?

**De dónde nace:** de que la acumulación Mastercard no es automática y hay que
pedirla.

**Por qué importa:** es una pregunta de diseño del motor, no comercial. Si hay
retroactividad, el motor tiene que poder recorrer transacciones ya procesadas y
emitir asientos nuevos con fecha pasada, lo que cambia el modelo del ledger. Si no
la hay, hay clientes que acumularon cero durante años sin saber que existía un
trámite.

### P-10. ¿El PBX 1717 sigue siendo canal de consulta y de solicitud?

**De dónde nace:** de una ausencia verificada. Las cuatro páginas de producto
Mastercard listan exactamente los mismos beneficios que las Visa **menos** la línea
de acumulación de puntos. No dicen que no acumulan: el beneficio simplemente no
aparece, y tampoco aparece que se pueda solicitar. Ese dato vive únicamente en un
blog de 2022.

**Por qué importa:** un cliente que compara productos en el sitio del banco no
tiene forma de enterarse de que su Mastercard puede acumular. Y la única fuente que
lo dice es la más débil del conjunto.

### P-11. Si Bi Puntos y Club Bi son programas distintos, ¿qué sistema es dueño de la Tarjeta Club Bi física?

**De dónde nace:** de la corrección 3.1. Son dos programas que comparten nombre
comercial, tarjeta física y usuario del portal, y la tarjeta física es obligatoria
para canjear porque "en ella se depositan todos tus Bi Puntos".

**Por qué importa:** es la pregunta más arquitectónica de las cinco. Si el saldo de
puntos está atado a un plástico que pertenece a otro programa, entonces hay una
dependencia entre dos sistemas que el organigrama probablemente separa. Y explica
por qué el canje exige presencia física: no es una decisión de seguridad, puede ser
una consecuencia de que el saldo viva en la tarjeta y no en el cliente.

## 8. Lo que no se hizo, y por qué

**No se llamó al 1717 ni se visitó una agencia.** Habría respondido varias
preguntas abiertas de primera mano. No se hizo porque el resultado no sería
verificable por un tercero: lo que diga un asesor en una llamada no es una fuente
citable, y el caso se sostiene sobre que cualquier afirmación se puede volver a
comprobar. Si el cliente autoriza contacto directo, es la vía más rápida para
cerrar P-7 a P-11.

**No se abrió una cuenta ni se solicitó una tarjeta.** Habría dado acceso a un
estado de cuenta real, que es la única fuente donde probablemente aparezca la tasa
del saldo promedio. Excede el alcance de un diagnóstico documental y un solo caso
no permite generalizar.

**No se estimó ningún número que no fuera público.** Es la regla del caso. Donde
hacía falta un valor para que el código corriera, se puso en
[`config/poc-parameters.yaml`](../config/poc-parameters.yaml) declarando qué
pregunta abierta sustituye, y ningún entregable lo presenta como dato del sistema.
