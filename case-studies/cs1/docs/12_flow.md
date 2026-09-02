# El flujo completo

De la fotografía a la recomendación, y de ahí a lo publicado. Parte de la
documentación; el índice está en [README.md](README.md).

Son tres diagramas y no uno. Uno solo con todo se vuelve ilegible, y las tres
cosas que describen son independientes: por dónde pasa un dato, cómo se rastrea
hacia atrás, y cómo sale una entrega.

## 1. El dato, de la foto al consejo

```mermaid
flowchart TD
    A[Fotografias<br/>almacenamiento externo] -->|ingesta con cache| B[Imagenes locales]
    B --> C[Recorte del panel]
    C --> D{Contiene display?}
    D -->|no| X[Descartada<br/>queda registrada]
    D -->|si| E[Correccion de cursiva]
    E --> F[Clasificacion<br/>siete segmentos]
    F --> G{Motor alterno<br/>disponible?}
    G -->|si| H[Segunda opinion<br/>gana mayor confianza]
    G -->|no| I
    H --> I[BRONZE<br/>lectura + confianza]

    I --> J{Precio legible?}
    J -->|si| K["metodo = ocr"]
    J -->|no, hay total| L["metodo = arithmetic"]
    J -->|no| M{Hay lecturas<br/>vecinas?}
    M -->|si| N["metodo = interpolated"]
    M -->|no| O["metodo = median / mean"]

    P[Serie sintetica<br/>corte explicito] --> Q["metodo = synthetic"]

    K --> R[SILVER<br/>precios con procedencia]
    L --> R
    N --> R
    O --> R
    Q --> R

    R --> S[GOLD<br/>features + metodo + marca]
    S --> T[Entrenamiento<br/>particion temporal]
    T --> U{Compuerta<br/>de calidad}
    U -->|falla| V[Corrida en rojo]
    U -->|pasa| W[Modelo registrado]
    W --> Y[Recomendacion<br/>a 1, 2 y 4 semanas]

    style I fill:#7a5c2e,color:#fff
    style R fill:#6b6b6b,color:#fff
    style S fill:#8a7320,color:#fff
    style U fill:#7a2e2e,color:#fff
```

Dos cosas que el dibujo hace explícitas y el texto esconde:

- **La columna `metodo` nace en Silver y llega hasta el modelo.** No es
  metadato: es una entrada. Un precio imputado y uno leído no valen lo mismo, y
  el modelo no puede distinguirlos si nadie se lo dice.
- **La compuerta corta.** No informa. Un pipeline en verde con un modelo que no
  gana a la referencia simple es peor que uno en rojo.

## 2. El rastro hacia atrás

Lo anterior visto al revés: desde un número del conjunto de modelado hasta la
fotografía de la que salió.

```mermaid
flowchart LR
    G[gold_row] --> S[silver_price]
    S --> P[price_reading]
    P --> E[extraction_run]
    P --> C[image_crop]
    C --> I[image]
    E -.->|version del codigo<br/>huella de config| E
    G --> M[trained_model]

    R{{"Fila sintetica<br/>o imputada"}} -.->|el rastro<br/>termina aqui| S

    style I fill:#2e5c7a,color:#fff
    style R fill:#7a5c2e,color:#fff
```

El encadenamiento son claves foráneas, no un campo que alguien mantiene: por eso
no se puede desincronizar. La base fuerza esa integridad en cada conexión, algo
que el motor embebido no hace salvo que se le pida explícitamente.

Cuando el rastro se corta —una fila sintética no tiene fotografía detrás— la
consulta **lo declara** en vez de devolver un hueco. Y `lineage_coverage` mide
qué porcentaje del conjunto llega hasta una foto real: si da cero, el modelo se
entrena solo sobre datos generados, y conviene que eso sea visible y no una
sorpresa.

## 3. Cómo sale una entrega

```mermaid
flowchart TD
    subgraph diario["En cada empujon"]
        A1[Calidad de codigo] --> A2{Hay fotografias?}
        A2 -->|no| A3[Etapas de datos<br/>se saltan, con motivo]
        A2 -->|si| A4[Bronze] --> A5[Silver / Gold] --> A6[Entrenamiento] --> A7[Compuerta]
        A1 --> A8[Imagen + humo de API]
        A8 --> A9[Analisis de vulnerabilidades<br/>informa, no bloquea]
    end

    subgraph entrega["Al empujar una etiqueta cs1-v*"]
        B1{Etiqueta = version<br/>del paquete?} -->|no| B2[Corta en segundos]
        B1 -->|si| B3[Construir y verificar<br/>que no se cuele nada]
        B3 --> B4[Instalar en limpio<br/>Linux y Windows]
        B4 --> B5{Aprobacion<br/>manual}
        B5 --> B6[Paquete al indice]
        B6 --> B7{Analisis:<br/>algo grave<br/>con arreglo?}
        B7 -->|si| B8[Corta]
        B7 -->|no| B9[Imagen al registro]
    end

    style B5 fill:#7a2e2e,color:#fff
    style B1 fill:#7a5c2e,color:#fff
    style A9 fill:#2e5c7a,color:#fff
```

Tres decisiones que el dibujo explica mejor que un párrafo:

- **La ausencia de fotografías no es un fallo.** Se decide una vez, se deja
  escrito el motivo en el resumen, y las etapas que dependen de datos se saltan.
  Un pipeline verde que en realidad no ejecutó nada es peor que uno rojo.
- **La imagen sale después del paquete, no en paralelo.** Si la aprobación se
  rechaza, una imagen ya publicada anunciaría una versión que no existe en el
  índice.
- **El análisis corta al publicar y solo informa a diario.** La mayor parte de
  lo que encuentra son paquetes de la distribución sin arreglo publicado: cortar
  por algo que nadie puede arreglar entrena a ignorar el rojo.

## Dónde está cada cosa

| Del diagrama | En el código |
|---|---|
| Ingesta con caché | `ingestion/` |
| Recorte y lectura | `extraction/` |
| Bronze, Silver, Gold | `data/pipeline.py` |
| Recuperación y relleno | `data/recovery.py` |
| Las siete tablas | `db/models.py` |
| El rastro hacia atrás | `db/lineage.py` |
| Entrenamiento y compuerta | `modeling/`, `evaluation/` |
| Recomendación y servicio | `serving/` |

El detalle del modelo de datos está en [06_data_model.md](06_data_model.md), y
el de los flujos en [09_ci.md](09_ci.md).
