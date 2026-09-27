# Arquitectura de datos

Parte de la documentación; el índice general está en [../README.md](../README.md).

## Qué es esto y qué no es

Lo que sigue es **la arquitectura que las reglas públicas obligan a que
exista**, no la que se verificó en producción. No se observó ningún sistema de
Corporación BI: se observó su comportamiento publicado, y de ahí se dedujo qué
componentes tienen que estar detrás para que ese comportamiento sea posible.

Por eso estos diagramas sirven para razonar sobre el
sistema, para localizar dónde duele y para dirigir las preguntas al cliente.
No sirven como inventario de servicios.

Cuando un elemento del diagrama se sostiene en una regla pública, el documento
lo dice. Cuando es una deducción, también.

## Los diagramas

Son cuatro, y son cuatro a propósito. Uno solo con todo se vuelve ilegible, y
las cuatro cosas que describen son independientes entre sí: qué componentes
hay, por dónde pasa un dato, qué le ocurre a un punto a lo largo de su vida, y
cómo se relacionan las entidades.

| Diagrama | Responde |
|---|---|
| [Vista de sistema](../../README.md#arquitectura-de-datos) | Qué componentes existen y cómo se conectan |
| [01 · Flujo del dato](diagrams/01-flujo-del-dato.md) | Por dónde pasa un consumo hasta volverse saldo |
| [02 · Ciclo de vida del punto](diagrams/02-ciclo-de-vida-del-punto.md) | Qué estados atraviesa un punto y cómo sale del sistema |
| [03 · Modelo de datos](diagrams/03-modelo-de-datos.md) | Qué entidades hay y qué las relaciona |
| [04 · Dónde entra el modelo](diagrams/04-donde-entra-el-modelo.md) | En qué puntos del pipeline se injerta ML o un LLM |

La vista de sistema vive en el [README del caso](../../README.md) y no se
repite aquí: un diagrama en dos archivos se desincroniza en cuanto alguien
edita uno de los dos.

La carpeta [`exports/`](exports/) queda para las versiones en imagen, si hacen
falta para la presentación. Los diagramas versionados son los de Mermaid: son
texto, se revisan en un *diff* y no se desincronizan de su explicación.

## Las tres decisiones que estructuran todo

Los cuatro diagramas son consecuencia de tres decisiones que el sistema real ya
tomó, y que este caso se limita a hacer explícitas.

### 1. El saldo es un conjunto de lotes, no un contador

Dos reglas públicas lo imponen a la vez, y ninguna de las dos admite un
contador simple:

- **El vencimiento es un corte anual por año de acumulación.** Para saber qué
  vence el 5 de febrero hay que saber de qué año es cada punto.
- **La conversión a millas varía según el producto de origen.** Para saber qué
  vale un punto hay que saber de dónde vino.

Un número único no puede responder ninguna de las dos preguntas. El grano
mínimo que sí puede es el lote: grupo × periodo × origen.

### 2. El grano es el grupo familiar, no el cliente

Lo impone la unificación familiar: el saldo pertenece a un grupo y solo el
titular lo ejerce. Cualquier tabla cuyo grano sea el cliente está contando
puntos que ese cliente no puede canjear.

Es la decisión que más cambia el modelo respecto de lo que uno dibujaría por
defecto, y la más fácil de olvidar a medio camino.

### 3. La elegibilidad no viaja en la transacción

Acreditar un punto exige consultar, en ese instante, cuatro estados que viven
fuera del dato del consumo:

- si la membresía Club Bi está vigente,
- si el servicio Bi Móvil está activo,
- si la tarjeta concreta acumula —hay tarjetas que sí y tarjetas que no dentro
  de la misma categoría—,
- si el cliente está inscrito en la campaña que aplica.

Una acreditación no es una función del consumo. Es una función del consumo y de
cuatro estados externos **en el momento de acreditar**, lo que significa que
recalcular el pasado exige saber cómo estaban esos cuatro estados entonces.
Si el sistema no versiona esos estados, el recálculo es imposible y la
auditoría también.

## Lo que el dibujo deja ver y el texto esconde

- **Hay cuatro tuberías de acumulación, no una**, y solo tres son reproducibles.
  La cuarta —el sorteo— acredita con 48 horas de retardo desde un canal
  externo. Ver [H-7](../report/03-hallazgos.md#h-7--la-acreditación-por-sorteo-no-se-puede-reconstruir).
  Son cuatro *tuberías*, no cuatro *productos*: comercialmente el programa
  comunica ocho vías de acumulación, y seis de ellas entran por el autorizador
  de tarjetas. Ver [§2.1 del reporte](../report/02-reglas-del-programa.md).
- **Dos de las cuatro tuberías no tienen tasa pública.** El saldo promedio
  publica el umbral desde el que acumula cada cuenta (Q500 / Q1,000 / Q1,000)
  pero **no la tasa**; el sorteo no se deriva de una tasa en absoluto.
- **Expirar no es borrar.** Es un asiento más, con su fecha y su lote. Un saldo
  que baja sin dejar asiento es un saldo que nadie puede explicar después, y
  «¿por qué bajó mi saldo?» es la pregunta que un programa de puntos recibe
  todos los días.
