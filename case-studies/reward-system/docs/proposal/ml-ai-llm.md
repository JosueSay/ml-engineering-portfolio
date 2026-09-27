# Propuesta: dónde entra ML, AI o un LLM en el pipeline

Parte de la documentación; el índice está en [../README.md](../README.md). La
ubicación de cada injerto sobre el pipeline está dibujada en
[04-donde-entra-el-modelo.md](../architecture/diagrams/04-donde-entra-el-modelo.md).

## El criterio antes de las propuestas

Un sistema de puntos es un sistema contable. Cada punto vigente es una
obligación de la empresa frente a un cliente, y eso impone una disciplina que
no aplica cuando el modelo recomienda una película: **un error del modelo puede
cambiar cuánto dinero debe la empresa.**

De ahí salen las tres reglas que gobiernan esta propuesta.

**Primera: separar lo que decide de lo que observa.** Un modelo dentro del
camino crítico —que altera el saldo de un cliente— exige garantías distintas de
uno que produce una lista para que alguien la lea. De las tres propuestas, solo
una está en el camino crítico, y se dice explícitamente.

**Segunda: cada modelo compite contra la alternativa sin modelo.** Si ordenar a
los clientes por saldo funciona tan bien como el clasificador, la respuesta
correcta es ordenar por saldo. Un modelo que no gana a su referencia es código
que hay que mantener, servir y vigilar a cambio de nada.

**Tercera: el umbral se fija antes de entrenar.** Moverlo después de ver el
resultado convierte la evaluación en una formalidad.

---

## M1 · Resolver el rubro del comercio con un LLM

**Capa: Silver. Está en el camino crítico.** Es la propuesta que de verdad va
*dentro* del pipeline de datos, que es lo que pide el encargo.

### El problema

El factor de acumulación depende del rubro del comercio, y la diferencia no es
marginal: **1 punto por US$1 frente a 1 punto por US$10.** Un factor de diez.

El rubro llega en el código que manda la red de pagos. Cuando ese código falta
—y falta— la única pista es la descripción que el punto de venta reporta, que
es un campo de ancho fijo lleno de ruido:

```
SUPER24  ZONA 10   GT
P CAMPERO  #14
FARM GALENO  MIXCO GT
STAR MART TXC  ZONA 4
```

Una regla de texto contra el catálogo de comercios resuelve buena parte de
esto. No resuelve las abreviaturas que el catálogo no conoce, y ahí el consumo
cae en «rubro desconocido».

En cualquier otro programa, equivocarse de rubro cuesta un porcentaje. Aquí
cuesta un orden de magnitud. Eso convierte la exactitud de la clasificación de
detalle técnico en control de negocio.

### El enfoque

Un LLM clasificando la descripción contra un **catálogo cerrado** de rubros, no
en texto libre. La salida se restringe al conjunto de categorías válidas más un
valor de confianza, y por debajo del umbral la fila va a revisión manual en vez
de acreditarse.

Lo que hace viable esto en costo es una observación sobre la forma del dato:
**no se llama al modelo por transacción, se llama por descripción distinta sin
resolver.** Un banco procesa millones de transacciones sobre unos pocos miles
de cadenas de comercio distintas, y esas cadenas se repiten. Con una caché
sobre la descripción normalizada, el volumen real de llamadas es el de comercios
nuevos por mes, que es un número pequeño y decreciente.

Y el resultado no se descarta: se escribe al catálogo, de modo que el sistema
aprende y la regla de texto va cubriendo cada vez más.

### Qué datos necesita

Solo la descripción del punto de venta y el catálogo de rubros. No necesita
datos de cliente, lo que lo mantiene fuera de cualquier discusión de privacidad.

### Métrica y compuerta

La métrica de negocio no es la exactitud: son **los puntos mal acreditados**.
Una regla puede fallar mucho en transacciones pequeñas y no importar, o fallar
poco en viajes y costar caro.

| | |
|---|---|
| Referencia a batir | La regla de texto actual, medida sobre las filas sin código de rubro |
| Métrica primaria | Puntos acreditados con el factor equivocado, en porcentaje del total |
| Métrica secundaria | Proporción de filas que quedan sin resolver |
| Compuerta | No entra si no reduce los puntos mal acreditados frente a la regla actual |
| Umbral operativo | Las filas por debajo del umbral de confianza van a revisión, no al motor |

### Qué puede salir mal

- **Deriva del catálogo.** Comercios nuevos aparecen todo el tiempo. Sin
  reentrenar el conjunto de ejemplos, la exactitud se degrada en silencio.
  Mitigación: vigilar la tasa de «sin resolver» como serie, no como número.
- **Confianza mal calibrada.** Un modelo seguro de sí mismo y equivocado es
  peor que uno que duda. La calibración hay que medirla, no asumirla.
- **Es el único de los tres que toca el saldo.** Cualquier cambio de versión
  del modelo debería correr en paralelo antes de sustituir al anterior.

---

## M2 · Detección de anomalías en la acumulación

**Entre Silver y Gold, antes de asentar. Observador.**

### El problema

Un consumo que genera puntos fuera de escala puede ser un error de rubro, un
error de tipo de cambio, un fallo de una campaña mal configurada o un abuso.
Los cuatro se ven igual desde el ledger, y los cuatro son más baratos de
atender antes de que el asiento quede firme.

Corregir un lote ya asentado obliga a emitir un ajuste, explicárselo al cliente
y resolver qué hacer si ya lo canjeó.

### El enfoque

Un detector **no supervisado** sobre características de la acreditación: monto,
puntos otorgados, la razón entre ambos y el factor aplicado. No supervisado a
propósito: no hay etiquetas de fraude de puntos, y esperar a tenerlas significa
haberlo pagado antes.

Lo que marca **no se descarta: se retiene para revisión**. Un falso positivo
que bloquea puntos legítimos hace más daño que el fraude que evita.

### Qué datos necesita

Las columnas de acumulación de Silver. No necesita histórico largo para
arrancar.

### Métrica y compuerta

| | |
|---|---|
| Referencia a batir | Un umbral fijo sobre puntos por quetzal |
| Métrica | Precisión sobre lo marcado, evaluada por revisión humana durante el piloto |
| Compuerta | El volumen retenido tiene que caber en la capacidad real de revisión |

Esa última línea es la que suele romper estos proyectos. Un detector que marca
el 1% de las transacciones de un banco genera una cola que nadie puede revisar.
El parámetro de contaminación se fija por capacidad operativa, no por lo que
maximice una métrica.

---

## M3 · Propensión al canje a 90 días

**Sobre Gold. Observador, y su salida no vuelve al pipeline.**

### El problema

Los puntos vigentes son un pasivo. Cuánto de ese pasivo se va a realizar y
cuánto va a expirar el 5 de febrero es una pregunta de finanzas, y hoy se
responde con una tasa global aplicada al saldo total.

Además hay una acción concreta que depende de la respuesta: **a quién avisar
antes del corte.** Avisar a todos es ruido; avisar a quien iba a canjear de
todas formas no cambia nada. Lo que sirve es identificar a quien tiene saldo,
puede canjear y no lo va a hacer.

### El enfoque

Clasificación binaria por grupo familiar: ¿va a haber un canje en los próximos
90 días? El grano es el grupo porque el saldo es del grupo.

Variables candidatas, todas anteriores al corte de observación:

- saldo vigente y puntos que vencen en los próximos seis meses,
- consumo de los últimos 90 días y consumo histórico,
- número de canjes previos y días desde el último,
- meses que lleva la unificación —un grupo que no cumple los doce no puede
  canjear, y confundir «no quiso» con «no pudo» arruina el modelo,
- composición del saldo por origen.

**Línea base: regresión logística.** No por prudencia sino porque sus
coeficientes son legibles, y en un modelo que va a justificar una provisión
contable poder explicar por qué predice lo que predice vale más que un par de
puntos de métrica.

**Validación temporal, no aleatoria.** Se entrena con un corte y se evalúa con
otro posterior. Una partición aleatoria deja que un grupo que canjeó en marzo
esté en el entrenamiento cuando se predice marzo, y eso produce una métrica que
no se repite nunca en producción.

### Métrica y compuerta

| | |
|---|---|
| Referencia a batir | Ordenar a los grupos por saldo |
| Métrica primaria | Área bajo la curva ROC, fijada en 0.62 antes de entrenar |
| Métrica de negocio | Error en la estimación del pasivo que se realiza, contra la tasa global |
| Compuerta | No entra si no supera a la vez el umbral y a la referencia por saldo |

La segunda métrica es la que importa. Un modelo de propensión no sirve para
acertar cliente por cliente: sirve para estimar cuánto del pasivo se realiza. Si
no mejora esa estimación frente a aplicar una tasa global, no aporta nada a
finanzas por bueno que sea su AUC.

### Qué puede salir mal

- **El modelo aprende la fricción, no la intención.** Si el canje es presencial
  y difícil, el modelo va a predecir «cercanía a un centro de canje» disfrazada
  de propensión. Es información útil, pero no es lo que dice la etiqueta.
- **El aviso cambia el comportamiento que el modelo predice.** En cuanto se
  actúa sobre las predicciones, el histórico deja de ser comparable. Hay que
  reservar un grupo de control desde el primer envío.

---

## Lo que se evaluó y no se propone ahora

Dos ideas que aparecen solas al mirar este sistema y que conviene descartar
explícitamente, para que no vuelvan sin haberlas pensado.

**Un asistente conversacional que explique el saldo.** Es tentador: «¿por qué
tengo estos puntos y cuándo vencen?» es la pregunta que más recibe el programa,
y un LLM sobre el ledger podría responderla. El problema es que **el ledger
todavía no puede responderla bien**. Mientras el origen de los lotes, la
trazabilidad de campaña y el versionado de elegibilidad no estén resueltos
([modelo de datos](../architecture/diagrams/03-modelo-de-datos.md), «Lo que
falta»), un asistente sobre esos datos daría respuestas fluidas y a veces
falsas sobre el dinero de un cliente. Es el peor resultado posible. La
propuesta es volver a esto **después** de cerrar H-1 y H-2, no antes.

**Un recomendador de premios del catálogo.** Con más de 50 establecimientos
afiliados, recomendar parece natural. Pero el cuello de botella del canje no es
que el cliente no sepa qué quiere: es que tiene que ir presencialmente con una
tarjeta física ([H-8](../report/03-hallazgos.md)). Un recomendador optimiza el
paso que no está fallando.

---

## Orden sugerido

| Orden | Injerto | Por qué primero |
|---|---|---|
| 1 | M1 · Rubro | Es el único que corrige un cálculo que hoy puede estar mal. Los otros dos observan un sistema que conviene que ya esté bien |
| 2 | M3 · Propensión | No depende de nada nuevo y tiene un destinatario claro en finanzas |
| 3 | M2 · Anomalías | Necesita capacidad de revisión disponible; sin ella, produce una cola que nadie atiende |

Y una precondición para los tres: ninguno vale nada mientras no se responda la
pregunta P-3, el tipo de cambio de acumulación. Si el saldo base está calculado
sobre una conversión que nadie puede verificar, mejorar la clasificación de
rubro es afinar un instrumento desafinado.
