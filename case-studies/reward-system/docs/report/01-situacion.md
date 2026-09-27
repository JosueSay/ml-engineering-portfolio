# 1. Resumen de la situación

Parte del reporte; el índice está en [README.md](../README.md).

## El encargo

Un equipo de consultores contratado para optimizar el sistema de recompensas de
una empresa. La condición que define el trabajo aparece en una sola línea del
enunciado:

> «los responsables de diseñarlo e implementarlo ya no trabajan en la empresa»

Eso convierte el encargo en algo distinto de una auditoría normal. No hay
documentación interna que leer ni arquitecto a quien preguntarle. Lo que hay es
un sistema en producción, con clientes reales acumulando saldos reales, cuyo
comportamiento solo se puede reconstruir desde afuera: desde lo que el programa
le dice al público, desde lo que las bases de sus promociones dejan ver, y desde
lo que sus canales permiten observar.

Empresa elegida: **Puntos Bi**, el programa de lealtad de Corporación BI /
Banco Industrial en Guatemala, operado bajo la marca Club Bi.

Plazo: una semana para el diagnóstico y las propuestas de optimización.

## Por qué Puntos Bi

De las cinco opciones del enunciado, Puntos Bi es la que tiene más superficie
observable y más complejidad real. No es un programa de sellos: es un sistema
financiero con un pasivo contable detrás.

Tres razones concretas:

- **Acumula desde productos que no se parecen.** Tarjetas de crédito y débito,
  un producto de financiamiento en cuotas, y el saldo promedio de tres tipos de
  cuenta de depósito. El último no es una transacción: es un cierre de mes. Un
  programa que suma las dos cosas en un mismo saldo está sumando un flujo y un
  lote.
- **Tiene reglas de titularidad poco comunes.** La unificación familiar hace
  que el saldo pertenezca a un grupo y lo ejerza una sola persona, con una
  permanencia mínima de un año. Eso cambia el grano de todo el modelo de datos.
- **Expira por corte anual en fecha fija**, no por vencimiento rodante. Una
  decisión que parece un detalle operativo y que, medida, resulta tener
  consecuencias que el propio programa no comunica.

## Qué se sabía al empezar, y qué no

Al empezar, la página del programa respondía tres preguntas: que el programa
existe, que los puntos duran dos años y que se canjean en centros de canje. No
respondía la única que importa para documentar el sistema, que es **cuántos
puntos da un consumo**.

Esa pregunta terminó respondiéndose, pero no donde debería estar. La respuesta
está repartida en notas al pie con asterisco de las páginas de producto, una
por cada categoría de tarjeta, y hubo que cruzar cuatro de ellas para
reconstruir la regla. No existe ninguna fuente pública que la enuncie completa.

Ese hecho —que la regla central del programa es pública pero no está en ningún
lugar único— dejó de ser un obstáculo de la investigación y pasó a ser el
primer hallazgo del reporte. Es el síntoma que deja un sistema cuyo
equipo se fue: las reglas siguen operando, pero el documento que las explicaba
nunca existió o ya no se mantiene.

## Cómo se levantó el diagnóstico

Cuatro fuentes, en orden de cuánto pesan:

1. **Páginas de producto de Tarjetas Bi.** De ahí salen la tasa base, la tasa
   reducida y los topes anuales. Es la fuente más dura: son condiciones
   contractuales publicadas por producto.
2. **Bases de promociones publicadas en el blog corporativo.** La fuente más
   reveladora, y la menos obvia. Las bases de una promoción tienen que enunciar
   sus topes, sus mínimos y sus requisitos de elegibilidad, así que dejan ver
   qué maquinaria existe detrás. Es ahí donde aparecen los topes diarios y
   mensuales, el ticket mínimo, el padrón de inscritos y la acreditación
   diferida de los sorteos.
3. **Portal de puntos y canales de consulta.** De ahí salen la estructura de
   canales, el registro de identidad independiente y la advertencia de que la
   conversión a millas varía según el producto de origen.
4. **Reglamento del programa.** Publicado en un visor que no expone el texto,
   de modo que solo se pudo usar lo que otras fuentes citan de él: los productos
   que acumulan, la unificación familiar y las condiciones de canje.

**Lo que no se hizo:** no se accedió a ningún sistema, no se usó ninguna cuenta
de cliente y no se intentó rodear ninguna protección de los sitios consultados.
Todo el diagnóstico sale de material público. Donde eso no alcanzó, el
resultado es una pregunta abierta y no una estimación.

## Estado del sistema, en una página

El programa funciona. Acumula, expira, canjea y lleva años operando con
promociones encima. Los problemas que encontró este diagnóstico no son fallos
de funcionamiento: son problemas de **explicabilidad y de gobierno de reglas**.

- La regla que decide cuántos puntos gana un cliente existe, opera y es
  pública, pero está dispersa y comunicada en asteriscos.
- Hay al menos un mecanismo de acumulación —el de saldos promedio— del que no
  hay ni una sola cifra pública.
- Hay una vía de acreditación, la de sorteos, que no se deriva de las
  transacciones y que por tanto no se puede reconstruir si su registro se
  pierde.
- El saldo se presenta como un número único, pero el propio programa advierte
  que el valor de canje depende del producto que generó cada punto. Un número
  único no alcanza para decidir un canje.

De ahí salen los siete hallazgos de
[03-hallazgos.md](03-hallazgos.md) y las propuestas de
[04-conclusiones.md](04-conclusiones.md).
