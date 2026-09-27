# 01 · El flujo del dato

De un consumo a un saldo consultable. Parte de la
[arquitectura](../README.md).

Las capas son Bronze, Silver y Gold. No se eligen por moda: el problema del
encargo es de explicabilidad, y explicar un saldo exige que existan una copia
intacta de lo que entró, una versión limpia que declare qué le pasó a cada
fila, y una tabla de negocio construida solo a partir de la anterior.

```mermaid
flowchart TD
    subgraph B["BRONZE · lo que entro, sin tocar"]
        direction TB
        B1["Transacciones<br/>del autorizador"]
        B2["Saldos promedio<br/>del core de depositos"]
        B3["Padron de inscritos<br/>por campana"]
        B4["Premios de sorteo<br/>notificados por SMS"]
    end

    subgraph S["SILVER · limpio, con la procedencia declarada"]
        direction TB
        S1["Tipado<br/>texto a fecha e importe"]
        S2["Deduplicacion<br/>reintentos del autorizador"]
        S3["Reversas<br/>la anulacion retira su compra"]
        S4["Conversion GTQ a USD<br/>tipo de cambio NO PUBLICO"]
        S5{"Rubro del comercio"}
        S6["categoria_origen = mcc"]
        S7["categoria_origen = descripcion"]
        S8["categoria_origen = sin_resolver"]
    end

    subgraph M["MOTOR DE ACUMULACION"]
        direction TB
        M1{"Excluido?<br/>retiro, extrafinanciamiento"}
        M2{"Tarjeta acumula?<br/>atributo + afiliacion MC"}
        M3{"Rubro en las<br/>cinco categorias?"}
        M4["1 punto por US$1"]
        M5["1 punto por US$10"]
        M6["Multiplicador de campana<br/>si hay campana vigente<br/>y el cliente esta inscrito"]
        M7[("Acumuladores<br/>diario / mensual / campana / anual")]
    end

    subgraph G["GOLD · el ledger y lo que se deriva de el"]
        direction TB
        G1[("LOTE_PUNTOS<br/>grupo x periodo x origen<br/>nace con su vence_el")]
        G2[("MOVIMIENTO<br/>acumulacion | canje | expiracion")]
        G3["Saldo por grupo<br/>derivado de los asientos"]
    end

    X["Descartado<br/>queda registrado con su motivo"]

    B1 --> S1 --> S2 --> S3 --> S4 --> S5
    S5 -->|"hay codigo de rubro"| S6
    S5 -->|"se reconocio el nombre"| S7
    S5 -->|"no se pudo"| S8
    S6 --> M1
    S7 --> M1
    S8 --> M1

    M1 -->|"si"| X
    M1 -->|"no"| M2
    M2 -->|"no"| X
    M2 -->|"si"| M3
    M3 -->|"si"| M5
    M3 -->|"no"| M4
    M4 --> M6
    M5 --> M6
    B3 -.->|"elegibilidad"| M6
    M6 --> M7
    M7 -->|"lo que cabe bajo el tope"| G1
    M7 -->|"lo que excede"| X

    B2 -.->|"cierre mensual<br/>tasa NO PUBLICA"| G1
    B4 -.->|"+48 h<br/>sin tasa, sin consumo"| G1

    G1 --> G2 --> G3

    style G1 fill:#8a7320,color:#fff
    style G2 fill:#8a7320,color:#fff
    style M7 fill:#7a5c2e,color:#fff
    style S4 fill:#6b6b6b,color:#fff
    style S8 fill:#7a2e2e,color:#fff
    style X fill:#7a2e2e,color:#fff
```

## Lo que el diagrama hace explícito

**Las flechas punteadas entran al ledger sin pasar por el motor.** El saldo
promedio y los sorteos no se acumulan: se asientan. No hay rubro que resolver
ni tope que consultar. Eso las hace más simples y a la vez más frágiles: son
las dos vías que no se pueden rederivar si se pierde su origen.

**`categoria_origen` no es metadato.** Es la columna que dice si el rubro del
comercio se supo de verdad o se dedujo del texto. Tiene que sobrevivir hasta
Gold, porque de ella depende si se aplicó la tasa base o la reducida, y entre
una y otra hay un factor de diez. En un programa donde el error de rubro cuesta
un 10%, esta columna sería una curiosidad; aquí decide un orden de magnitud.

**Hay tres salidas al descarte, y las tres son distintas.** Una exclusión de
producto, una tarjeta que no acumula y un consumo que excedió el tope no son lo
mismo, aunque los tres terminen en cero puntos. Un cliente que reclama merece
saber cuál de los tres le pasó, y el sistema solo puede responderlo si lo
escribió en el momento.

**El tope se aplica al final, no al principio.** El cálculo se hace completo y
el acumulador recorta. Es la única forma de poder decirle al cliente «ganaste
X, se te acreditaron Y, el resto excedió tu tope anual» en lugar de
simplemente acreditarle Y sin explicación.

## Lo que el diagrama no resuelve

El nodo `Conversion GTQ a USD` está en gris porque es un hueco, no un
componente. La tasa se define en dólares y el consumo se liquida en quetzales,
pero ninguna fuente pública dice con qué tipo de cambio ni de qué fecha. Todo
lo que está a su derecha depende de ese valor. Ver
[H-4](../../report/03-hallazgos.md#h-4--la-tasa-se-define-en-dólares-el-consumo-se-liquida-en-quetzales)
y la pregunta P-3.
