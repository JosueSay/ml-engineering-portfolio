# 03 · El modelo de datos

Qué entidades tienen que existir para que las reglas públicas se puedan
cumplir. Parte de la [arquitectura](../README.md).

Como el resto de estos diagramas, es una **deducción**: el modelo que el
comportamiento publicado obliga a que exista, no un esquema verificado en
producción.

```mermaid
erDiagram
    GRUPO_FAMILIAR ||--o{ CLIENTE : agrupa
    GRUPO_FAMILIAR ||--|| CLIENTE : "tiene un titular"
    CLIENTE ||--o{ TARJETA : posee
    CLIENTE ||--o{ CUENTA_DEPOSITO : posee

    TARJETA ||--o{ TRANSACCION : origina
    CUENTA_DEPOSITO ||--o{ SALDO_MENSUAL : cierra

    CAMPANA ||--o{ INSCRIPCION : admite
    CLIENTE ||--o{ INSCRIPCION : se_inscribe
    CAMPANA ||--o{ SORTEO_PREMIO : otorga
    CLIENTE ||--o{ SORTEO_PREMIO : gana

    TRANSACCION ||--o| LOTE_PUNTOS : acredita
    SALDO_MENSUAL ||--o| LOTE_PUNTOS : acredita
    SORTEO_PREMIO ||--o| LOTE_PUNTOS : acredita

    GRUPO_FAMILIAR ||--o{ LOTE_PUNTOS : posee
    GRUPO_FAMILIAR ||--o{ ACUMULADOR : consume
    LOTE_PUNTOS ||--o{ MOVIMIENTO : registra
    CANJE ||--o{ MOVIMIENTO : produce
    GRUPO_FAMILIAR ||--o{ CANJE : solicita

    GRUPO_FAMILIAR {
        string grupo_id PK
        string titular_cliente_id FK
        date   unificacion_desde
        bool   puede_canjear "derivado: 12 meses"
    }

    CLIENTE {
        string cliente_id PK
        string grupo_id FK
        bool   membresia_club_bi_vigente
        bool   bi_movil_activo
    }

    TARJETA {
        string tarjeta_id PK
        string cliente_id FK
        string marca "visa | mastercard"
        string categoria "clasica..infinite"
        bool   acumula "atributo por tarjeta"
        bool   afiliada_mc "solicitada por 1717"
        int    tope_anual "180k | 360k | 420k | null"
    }

    CUENTA_DEPOSITO {
        string cuenta_id PK
        string cliente_id FK
        string tipo "monetaria | ahorro | 5 estrellas"
    }

    TRANSACCION {
        string auth_code PK
        string tarjeta_id FK
        datetime ts
        decimal monto
        string moneda
        decimal tipo_cambio_aplicado "NO PUBLICO"
        string mcc "puede faltar"
        string comercio_desc "texto del punto de venta"
        string categoria_resuelta
        string categoria_origen "mcc | descripcion | sin_resolver"
        bool   excluida
        string motivo_exclusion
    }

    SALDO_MENSUAL {
        string cuenta_id FK
        string periodo PK
        decimal saldo_promedio
    }

    CAMPANA {
        string campana_id PK
        date   vigencia_desde
        date   vigencia_hasta
        string mecanica "multiplicador | bonificacion | sorteo"
        decimal factor
        decimal ticket_minimo
        int    tope_por_cliente
        bool   requiere_inscripcion
    }

    INSCRIPCION {
        string campana_id FK
        string cliente_id FK
        datetime inscrito_en
    }

    SORTEO_PREMIO {
        string premio_id PK
        string campana_id FK
        string cliente_id FK
        int    puntos
        datetime notificado_en
        datetime acreditado_en "+48 h"
    }

    ACUMULADOR {
        string grupo_id FK
        string ventana "diario | mensual | campana | anual"
        string periodo PK
        int    consumido
        int    tope
    }

    LOTE_PUNTOS {
        string lote_id PK
        string grupo_id FK
        string periodo "mes de acumulacion"
        string origen "define el valor de canje"
        int    puntos
        date   vence_el "5 de febrero de periodo+2"
    }

    MOVIMIENTO {
        string movimiento_id PK
        string lote_id FK
        string tipo "acumulacion | canje | expiracion | ajuste"
        datetime fecha
        int    puntos
    }

    CANJE {
        string canje_id PK
        string grupo_id FK
        string centro_de_canje
        datetime fecha
        string premio
        int    puntos_solicitados
    }
```

## Las cinco decisiones del modelo

### 1. `LOTE_PUNTOS` cuelga del grupo, no del cliente

Es la traducción directa de la unificación familiar. El saldo pertenece al
grupo y solo el titular lo ejerce, así que la clave foránea natural es
`grupo_id`. Colgarlo del cliente obligaría a re-agregar en cada consulta y
abriría la puerta a contar puntos que nadie puede canjear.

`CLIENTE` sigue existiendo porque la elegibilidad es individual: la membresía
Club Bi, el servicio Bi Móvil y la inscripción a campañas son del cliente, no
del grupo.

### 2. `origen` vive en el lote y no se deriva de nada

Es la columna que sostiene el hallazgo central. Si la conversión a millas varía
según el producto que generó el punto, el origen **es parte del valor**, no una
etiqueta descriptiva. Un lote sin origen es un lote que no se puede canjear a
millas.

Y no se puede reconstruir después: un lote de 2024 que perdió su origen no
tiene cómo recuperarlo si la transacción que lo generó ya se archivó.

### 3. `vence_el` se escribe al crear el lote

Podría calcularse al consultarlo —es una función del periodo— pero entonces la
regla del 5 de febrero viviría repetida en los seis canales de consulta, y basta
con que uno la implemente distinto para que el cliente vea dos fechas según
dónde mire. Escribirla una vez, en el origen, cuesta un campo.

### 4. `ACUMULADOR` es una entidad, no un `SUM()`

Las bases de promociones dejan ver cuatro ventanas conviviendo: tope diario,
tope mensual, tope por campaña y tope anual por categoría de tarjeta. Resolverlas
con agregaciones sobre el histórico es correcto y lento, y además no permite
responder «¿cuánto me queda de mi tope?», que es justo lo que un cliente
querría saber antes de comprar.

Su grano está declarado como `grupo_id`, pero **es la pregunta abierta P-1**: el
tope anual podría ser por tarjeta, por cliente o por grupo. Las tres opciones
dan saldos distintos para el mismo consumo, y esta tabla cambia según la
respuesta.

### 5. `MOVIMIENTO` es la única fuente del saldo

No hay campo `saldo` en ninguna entidad. El saldo de un grupo es la suma de sus
movimientos, y punto. Guardarlo además en una columna crea dos verdades que se
desincronizan, y el día que difieren nadie sabe cuál es la buena.

Esto es lo que hace que `expiracion` tenga que ser un tipo de movimiento y no
un borrado: si expirar no deja asiento, el saldo derivado deja de cuadrar con
la historia.

## Lo que falta en este modelo

- **Versionado de la elegibilidad.** `CLIENTE.membresia_club_bi_vigente` es un
  booleano del presente. Para recalcular una acreditación del año pasado haría
  falta saber cómo estaba ese booleano entonces. Sin historial, el recálculo es
  imposible y la auditoría también.
- **Trazabilidad de la campaña en el lote.** Un lote acredita desde una
  transacción, pero si hubo un multiplicador de campaña, el lote no dice cuál.
  Falta una referencia a `CAMPANA` para poder explicar por qué un consumo de
  Q100 dio el doble de lo esperado.
- **El tipo de cambio.** Está en `TRANSACCION` como campo, pero su origen no es
  público. Mientras no se sepa de dónde sale, es un campo cuyo contenido nadie
  puede verificar.
