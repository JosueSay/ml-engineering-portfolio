# Conclusiones

Qué hacer, en qué orden y por qué. Sale de los ocho hallazgos de
[03-hallazgos.md](03-hallazgos.md) y no agrega ninguna afirmación nueva sobre el
sistema.

## La conclusión de fondo

El programa funciona. Acumula, acredita, vence y canja, y lo hace con una
maquinaria más sofisticada de lo que su comunicación deja ver: cuatro orígenes de
datos con relojes distintos, una capa de reglas temporales, unificación de saldos
entre personas y vencimiento por lotes.

El problema no es que el sistema esté mal construido. **El problema es que la regla
que lo gobierna nunca fue un documento**, y por eso el conocimiento se fue con las
personas que lo diseñaron. Seis de los ocho hallazgos son consecuencias de eso, no
defectos independientes.

Esa es la razón por la que la recomendación principal de este diagnóstico no es un
cambio al programa: es un cambio a **dónde vive su regla**.

## Cómo se ordenaron las recomendaciones

No por severidad. Un hallazgo crítico que exige un proyecto de seis meses no puede
ir antes que uno alto que se cierra en una semana, porque entonces la lista no se
empieza.

El orden es por **dependencia**: primero lo que no requiere decidir nada, después lo
que requiere una decisión del banco, y al final lo que requiere un proyecto. Dentro
de cada nivel, por severidad.

| Nivel | Qué lo caracteriza | Cuántas |
| --- | --- | --- |
| 1 | No requiere decidir nada ni preguntar nada. Es redactar o ajustar | 4 |
| 2 | Requiere que el banco decida o publique algo que hoy no publica | 5 |
| 3 | Requiere un proyecto de datos | 3 |

## Nivel 1: lo que se puede hacer sin decidir nada

### 1.1 Subir la longitud mínima de contraseña del portal

**Cierra H-5.** Es lo primero de la lista y no porque sea lo más importante, sino
porque es lo único de los ocho que no necesita una reunión: no toca el motor de
puntos, no exige preguntarle nada a nadie y no cambia ninguna regla del programa.

Detrás de esa contraseña hay saldo canjeable por bienes y un canje en línea
habilitado. Y es una superficie de autenticación separada de la banca en línea, así
que lo que se haya endurecido allá no protege aquí.

### 1.2 Publicar la tasa reducida con la misma prominencia que la base

**Cierra la parte de comunicación de H-6.** Hoy la regla con más impacto sobre el
saldo de un cliente promedio vive en una nota al pie con asterisco de las páginas de
producto, y la página del programa no la menciona.

No se pide cambiar la tasa. Se pide que la página del programa diga que en
supermercados, gasolineras, tiendas de conveniencia, entidades de beneficencia y
centros educativos se acumula una décima parte. Un cliente que usa la tarjeta
sobre todo en esas categorías está en un programa que le devuelve mucho menos de lo
que cree, y hoy no tiene forma razonable de enterarse.

### 1.3 Documentar el alcance de los tres canales de canje

**Cierra H-8.** Hay tres canales y toda la documentación pública describe uno. El
canje en línea existe —el portal tiene la funcionalidad y el aviso— y ninguna fuente
dice qué parte del catálogo admite.

Si resulta que cubre todo el catálogo, comunicarlo es probablemente **la mejora de
costo operativo más barata del programa**, porque el canal presencial exige que el
cliente se presente con tarjeta física y documento de identificación.

### 1.4 Comunicar la vigencia como fecha por lote, no como duración

**Cierra la parte de comunicación de H-3.** La regla publicada dice "dos años" y el
mecanismo real es un corte anual en fecha fija, lo que da una vigencia efectiva de
13 a 25 meses según el mes en que se ganó el punto.

El dato ya existe en el sistema: para poder vencer un lote, el motor tiene que
conocer su fecha. Lo que falta es mostrarlo. Un saldo que dice "12,400 puntos, de
los cuales 3,100 vencen el 5 de febrero" es la misma información que el sistema ya
tiene, presentada de forma que el cliente pueda actuar.

## Nivel 2: lo que requiere que el banco decida

### 2.1 Publicar la política de tipo de cambio

**Cierra H-4 del lado del cliente.** Una línea de texto: con qué tipo de cambio y de
qué fecha se convierte el consumo en quetzales a los dólares en que está enunciada
la regla.

Sin eso, ningún cliente puede verificar su propio saldo y el banco no puede expresar
el retorno del programa como porcentaje del consumo, que es lo que haría falta para
compararlo con cualquier otro programa de la región.

### 2.2 Publicar las tasas de conversión a millas, o mostrar el saldo desglosado

**Cierra H-1.** Son dos acciones y la segunda depende de la primera.

Que la conversión varíe según el producto de origen es público; cuánto varía, no. Y
mientras eso siga así, los seis canales de consulta están mostrando un número único
sobre un saldo que no es homogéneo: dos clientes con el mismo saldo no tienen el
mismo poder de compra y ninguno de los dos puede saberlo.

### 2.3 Resolver la contradicción del multiplicador por membresía

Las preguntas frecuentes de Club Bi dicen que la membresía da dobles puntos en la
Súper Cuenta de Ahorros; la página de Bi Puntos dice que es con la cuenta monetaria.
Son dos fuentes del mismo emisor sobre un multiplicador de dos.

Es la corrección más urgente del nivel 2 en términos de daño directo: un cliente que
paga Q180 al año para duplicar sus puntos no puede saber en cuál de sus cuentas
conviene dejar el saldo.

### 2.4 Publicar la tasa de acumulación por saldo promedio

Es el único mecanismo del programa sin ninguna cifra pública, y el banco reconoce por
escrito que no hay una regla sino tres, una por tipo de cuenta, sin publicar
ninguna.

Hoy se sabe desde qué saldo se empieza a acumular y no cuánto se acumula, que es
justo la mitad que le sirve al cliente para decidir. Y sin ese número no se puede
responder algo básico sobre el diseño del programa: **si premia gastar o premia
ahorrar.**

### 2.5 Publicar el listado general de exclusiones y la lista de comercios aliados

Dos huecos de la misma naturaleza. Las únicas exclusiones publicadas —retiros de
efectivo y extrafinanciamientos— aparecen dentro de las bases de una promoción
concreta, no como regla general. Y de los comercios aliados hay tres listas públicas
distintas, ninguna coincidente, y ninguna tasa.

Si el motor aplica un factor por comercio, la lista **es parte de la regla de
acumulación**, y hoy no se puede reconstruir desde fuera.

## Nivel 3: lo que requiere un proyecto

Estas tres son la recomendación de fondo, y el orden entre ellas no es negociable
porque cada una es insumo de la siguiente.

### 3.1 Un archivo único de reglas, versionado, del que dependa el motor

**Ataca H-2 estructuralmente, y por eso es la recomendación principal del
diagnóstico.**

La respuesta intuitiva a H-2 es escribir un manual. No sirve: un manual se
desincroniza del motor en el primer cambio, y eso es precisamente lo que ya pasó. La
respuesta estructural es que **el motor lea la regla de un archivo legible y
versionado**, de modo que la documentación y la configuración sean el mismo objeto y
no puedan divergir.

Las páginas de producto y el material comercial se generan desde ese archivo, no en
paralelo. Con eso, las tres listas distintas de comercios aliados y la contradicción
del multiplicador dejan de ser posibles por construcción, no por disciplina.

Este caso trae la demostración: el POC no tiene constantes incrustadas, lee
[`../../config/assumptions.yaml`](../../config/assumptions.yaml), y se puede mostrar
corriendo.

### 3.2 Procedencia en el ledger

**Cierra H-4 del lado de la auditoría, y mitiga H-7.**

Hay algo peor que un tipo de cambio no público, y es un tipo de cambio no guardado.
Si la acreditación registra los puntos resultantes pero no la tasa con la que
convirtió, **el saldo no es reproducible ni teniendo las reglas en la mano**, y el
banco no puede auditar su propio motor hacia atrás.

La recomendación concreta es un puñado de columnas más: que cada lote acreditado
guarde el tipo de cambio aplicado y su fecha, la versión del mapa de rubros, la
versión de las reglas, el identificador de la campaña o del sorteo y el estado de
elegibilidad consultado en ese momento.

Para los puntos de sorteo la respuesta es mitigar y no resolver: no hay nada de qué
derivarlos, así que lo más que se puede lograr es que tengan procedencia propia y
sean verificables aunque no sean derivables.

El modelo de datos que esto implica está en
[`../architecture/README.md`](../architecture/README.md), y la evaluación de con qué
herramienta versionar los datos de referencia —con la conclusión de que **no es
DVC**— en [`../versionado-de-datos.md`](../versionado-de-datos.md).

### 3.3 Después de 3.1 y 3.2, el clasificador de rubro

Con las dos anteriores hechas, hay un lugar en el pipeline donde un modelo aporta:
las transacciones que llegan sin código de rubro, donde hoy la regla no tiene con qué
decidir y el error es de diez a uno.

La propuesta completa, con su umbral de confianza, su respaldo favorable al cliente y
su criterio de descarte fijado antes de entrenar, está en
[`../proposal/ml-ai-llm.md`](../proposal/ml-ai-llm.md).

Va al final a propósito: **un modelo montado sobre un ledger sin procedencia hereda
el problema que este diagnóstico encontró y lo vuelve más difícil de investigar.**

## El mapa completo

| Hallazgo | Severidad | Recomendación | Nivel |
| --- | --- | --- | --- |
| H-5 | Crítica | Subir la longitud mínima de contraseña | 1 |
| H-6 | Alta | Publicar la tasa reducida con prominencia | 1 |
| H-8 | Media | Documentar el alcance de los tres canales | 1 |
| H-3 | Alta | Comunicar la vigencia por lote | 1 |
| H-4 | Crítica | Publicar la política de tipo de cambio | 2 |
| H-1 | Alta | Publicar las tasas de millas y desglosar el saldo | 2 |
| H-2 | Crítica | Archivo único de reglas versionado | 3 |
| H-4, H-7 | Crítica y media | Procedencia en el ledger | 3 |

## La entrega más importante no es esta lista

Son las **trece preguntas abiertas**. Seis están en
[`../../config/assumptions.yaml`](../../config/assumptions.yaml) y siete en
[`../investigacion-y-supuestos.md`](../investigacion-y-supuestos.md).

Un diagnóstico hecho desde fuera tiene un límite duro, y conviene decirlo en la
entrega en vez de disimularlo: hay cosas que no se pueden saber sin acceso al
sistema. Las trece preguntas son ese límite, escrito.

Y son accionables de inmediato. Cuatro de ellas —el grano del tope, la tasa del
saldo promedio, el tipo de cambio y el orden de consumo de lotes— se pueden
responder en una reunión con quien opere el motor hoy, y cada respuesta cambia una
parte del diagnóstico. El POC está construido para que cambiar esos cuatro valores en
un archivo de configuración vuelva a producir todos los resultados sin tocar código.

## Qué no se puede concluir desde fuera

Cuatro cosas que este diagnóstico **no** afirma, y que alguien podría esperar que
afirmara:

**Si el programa es competitivo.** Haría falta el tipo de cambio de acumulación y las
tasas de millas. Con los datos públicos solo se puede decir el orden de magnitud del
retorno, y como ilustración.

**Si los clientes están perdiendo puntos en el corte.** Se puede demostrar que la
vigencia efectiva varía de 13 a 25 meses, pero cuántos puntos vencen sin canjear es
un dato del ledger.

**Si la tasa reducida está económicamente justificada.** Las cinco categorías son
las de tasa de intercambio regulada, así que hay una explicación económica
razonable. Verificar si el traslado al cliente es proporcionado exigiría los costos
de intercambio reales del banco.

**Si el sistema tiene defectos de implementación.** No hay acceso. Todo lo que este
reporte llama hallazgo es una propiedad de las reglas o de su comunicación, no un
error de código, y la distinción es deliberada.

## Cómo se sabría que esto funcionó

Cuatro medidas que el banco ya puede calcular con lo que tiene, y que conviene medir
antes de empezar para tener línea base:

| Medida | Qué hallazgo vigila |
| --- | --- |
| Reclamos sobre saldo de puntos, y cuántos se pueden resolver consultando el sistema | H-4 y H-7: si no se puede reconstruir, no se puede resolver |
| Proporción de canjes por canal | H-8: si el canje en línea sube, la documentación funcionó |
| Puntos vencidos como proporción de los acumulados | H-3: si baja al comunicar la vigencia por lote, el cliente está actuando |
| Tiempo que tarda un asesor en responder una pregunta sobre las reglas | H-2: es la medida directa de si la regla ya está escrita en algún lado |

La cuarta es la que más importa y la que nadie mide. Si dentro de un año un asesor
sigue necesitando cruzar cuatro páginas de producto para responder cuántos puntos da
una compra en el supermercado, el diagnóstico no sirvió de nada.
