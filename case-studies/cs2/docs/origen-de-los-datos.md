# De dónde salen los datos del POC

Documento de decisión. El caso no tiene datos y probablemente no exista un
conjunto de datos público que sirva, así que hay que decidir de dónde salen los
del POC. Se evalúan cinco caminos con el mismo método que
[versionado-de-datos.md](versionado-de-datos.md): matriz de decisión ponderada,
con los pesos declarados antes de puntuar.

## Por qué no hay datos

Dos razones distintas, y conviene no confundirlas.

**No hay datos del programa.** Los consumos, saldos y acreditaciones de Puntos Bi
son datos propietarios de Corporación BI. El encargo no incluye acceso al sistema,
que es precisamente la restricción que define el caso.

**Y no hay un sustituto público.** Esto es más fuerte que no encontrarlo: es que
los campos que el caso necesita no existen juntos en ningún conjunto de datos
abierto. Para que el motor de acumulación pueda ejecutarse hacen falta:

| Campo | Para qué lo necesita el motor |
| --- | --- |
| Código de rubro del comercio | Decidir entre la tasa base y la reducida. Es la decisión de H-6 |
| Monto y moneda de liquidación | Convertir a dólares antes de aplicar la tasa. H-4 |
| Categoría de la tarjeta | Aplicar el tope anual correcto |
| Grupo familiar | Es el grano del ledger, y el grano del tope es P-1 |
| Saldo promedio mensual por tipo de cuenta | La segunda vía de acumulación, con tres umbrales distintos |
| Estado de membresía Club Bi, de Bi Móvil y de afiliación Mastercard | Los predicados de elegibilidad, que no viajan en la transacción |
| Marca de reversa y de reintento | Para poder probar que el motor no acredita dos veces |

Los conjuntos públicos de transacciones de tarjeta traen fecha, monto y a veces
rubro. Ninguno trae grupo familiar, saldo promedio por tipo de cuenta ni estados
de elegibilidad, porque son estructuras específicas de este programa. Y los
conjuntos de detección de fraude más citados vienen con las variables
transformadas por reducción de dimensiones, de modo que ni el monto ni el rubro
son legibles.

Revisé también el material del curso. `Credit_Card_Customer_Data.csv` tiene 660
filas a nivel de cliente —límite de crédito promedio, número de tarjetas, visitas
y llamadas— y ninguna transacción. Sirve para una sola cosa, y vale anotarla:
calibrar **cuántas tarjetas tiene un cliente**, que es un insumo de P-1 cuando
haya que mostrar cómo cambia el resultado según el grano del tope. Para el resto
no aporta nada.

## Un criterio que es compuerta, no peso

Antes de la matriz, un requisito que ninguna ponderación puede negociar.

El POC tiene que demostrar que el motor se comporta bien frente a los defectos
del sistema real: que un reintento del autorizador no acredite dos veces, que una
reversa que llega como fila aparte descuente, que un consumo sin código de rubro
no se acredite con la tasa equivocada en silencio. **Demostrar eso exige saber de
antemano qué fila es un duplicado y qué fila es una reversa.**

Un generador aprendido de datos no entrega esa etiqueta. Puede producir filas
parecidas a duplicados, pero no sabe cuáles lo son, porque aprendió una
distribución y no un mecanismo. Ese requisito descarta el camino del generador
entrenado con independencia de los pesos que se le pongan a lo demás. Se puntúa
igual en la matriz, para que quede el registro de por qué pierde, pero la
compuerta ya lo había eliminado.

## La matriz

| ID | Criterio | Peso | Por qué ese peso |
| --- | --- | --- | --- |
| B1 | Trae los campos que el motor necesita | 5 | Sin ellos el POC no se puede ejecutar |
| B2 | Verdad de terreno de los defectos | 5 | Es la compuerta de arriba |
| B3 | Imposible de confundir con una medición del programa real | 4 | Es la regla que sostiene todo el caso |
| B4 | Reproducible por un tercero | 4 | El entregable tiene que poder volver a correrse |
| B5 | Costo de obtención y licencia | 2 | Importa, pero ninguna opción tiene un costo prohibitivo |
| B6 | Plausibilidad de las distribuciones | 2 | Mejora la presentación; no cambia ninguna conclusión |

| Opción | B1 | B2 | B3 | B4 | B5 | B6 | **Total** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **P5. Simulador por reglas con semilla** | 5 | 5 | 5 | 5 | 5 | 3 | **106** |
| P6. Simulador por reglas, calibrado contra un conjunto público | 5 | 5 | 5 | 4 | 4 | 5 | 104 |
| P3. Conjunto público más aumentación de los campos que faltan | 4 | 2 | 2 | 3 | 3 | 4 | 64 |
| P2. Conjunto público usado directamente | 1 | 1 | 2 | 4 | 4 | 5 | 52 |
| P4. Generador entrenado con ML, tipo CTGAN o TVAE | 3 | 1 | 3 | 2 | 2 | 3 | 50 |

Tres lecturas de esa tabla:

**P5 y P6 están empatados en la práctica.** La diferencia de dos puntos es que la
calibración compra plausibilidad (B6) a cambio de una dependencia externa (B4 y
B5): si el conjunto de calibración deja de estar disponible, la corrida sigue
funcionando pero la justificación de las distribuciones se queda sin fuente.

**P4 pierde por una razón que no es la esperada.** No pierde por ser complejo:
pierde porque un generador aprende de datos reales y aquí no hay datos reales de
los que aprender. Entrenarlo sobre un conjunto público produciría datos cuya
distribución conjunta refleja **otra población** —otro país, otro programa, otra
mezcla de rubros— sin ninguna forma de validar si se parece a la de Guatemala. Se
pagaría complejidad por una plausibilidad que no se puede verificar.

**P2 y P3 traen un riesgo que la matriz apenas insinúa en B3.** Un conjunto de
datos reales, aunque sea de otro banco, invita a leer los resultados como una
medición. El día que una tabla del reporte diga "el 34% de los clientes topa antes
de octubre" sobre datos ajenos, el caso perdió lo único que lo hacía defendible.
Con un simulador con semilla esa confusión es imposible de sostener, porque la
procedencia de cada número está en un archivo de configuración.

## Recomendación

**P5 ahora: simulador por reglas con semilla, que es lo que
[`poc-parameters.yaml`](../config/poc-parameters.yaml) ya especifica.** Semilla
20260922, 700 clientes, 240 grupos familiares, 30 meses desde enero de 2024, y
los siete defectos inyectados a tasas declaradas.

**P6 como mejora opcional y citada.** Si se quiere que las distribuciones de monto
y la mezcla de rubros sean plausibles, se calibran contra una fuente pública y se
cita en el notebook cuál y para qué. La calibración afecta la forma de las
distribuciones, nunca las reglas: las reglas salen del catálogo de evidencia.

Y una condición de escritura que vale más que la decisión: **cada tabla del
notebook cuyo resultado dependa de un valor de `poc-parameters.yaml` lo declara en
la propia tabla.** No en una nota al pie del documento, que es exactamente el
defecto que le estamos señalando al cliente en H-2 y H-6. En la tabla.

## Lo que esto no es

El simulador no modela el comportamiento de los clientes de Banco Industrial. No
hay nada que lo sostenga. Modela **transacciones con la forma que el motor
necesita procesar**, para poder demostrar que el motor hace lo que las reglas
dicen. Cualquier cifra que salga de ahí es una demostración de mecánica.

La distinción importa para el entregable: el cliente recibe un POC que prueba que
las reglas reconstruidas son implementables y que el diseño propuesto aguanta los
defectos conocidos. No recibe una estimación de su propio programa, y el reporte
lo dice en la primera página.
