# Documentación del caso

Diagnóstico del sistema de recompensas Puntos Bi. La visión general está en el
[README del caso](../README.md); aquí está el detalle.

## Índice

| Documento | Para qué |
|---|---|
| [report/01-situacion.md](report/01-situacion.md) | Qué se pidió, qué se sabía al empezar y cómo se levantó el diagnóstico |
| [report/02-reglas-del-programa.md](report/02-reglas-del-programa.md) | Cómo se ganan, se conservan y se pierden los puntos |
| [report/03-hallazgos.md](report/03-hallazgos.md) | Los ocho hallazgos, con severidad y evidencia |
| [report/04-conclusiones.md](report/04-conclusiones.md) | Qué hacer, en qué orden y por qué |
| [report/05-referencias.md](report/05-referencias.md) | Fuentes consultadas, con fecha y qué aportó cada una |
| [architecture/README.md](architecture/README.md) | Los cuatro diagramas y cómo leerlos |
| [proposal/ml-ai-llm.md](proposal/ml-ai-llm.md) | Dónde entra un modelo y cómo se sabe si vale la pena |
| [investigacion-y-supuestos.md](investigacion-y-supuestos.md) | Bitácora de campo: qué se buscó, qué se encontró, qué se corrigió y en qué se contradicen las fuentes |

El catálogo de reglas con su procedencia está en
[`config/assumptions.yaml`](../config/assumptions.yaml). No es documentación de
apoyo es la fuente de la que salen los demás documentos, y la que el POC lee
para no tener constantes incrustadas en el código.

## Por dónde empezar

- **Primera vez en el caso**: [01-situacion.md](report/01-situacion.md), y
  luego el diagrama de arquitectura del [README](../README.md).
- **Buscando una regla concreta**:
  [02-reglas-del-programa.md](report/02-reglas-del-programa.md), o directamente
  `config/assumptions.yaml` si se quiere ver la fuente.
- **Preparando la presentación al cliente**:
  [03-hallazgos.md](report/03-hallazgos.md) y
  [04-conclusiones.md](report/04-conclusiones.md).
- **Revisando el trabajo**: [05-referencias.md](report/05-referencias.md) trae
  cada fuente con lo que aportó, para poder verificar cualquier afirmación.

## Las tres reglas que explican casi todo

Cualquier decisión de este caso sale de una de estas tres.

**Nada se afirma sin nivel de confianza.** Público, inferido o supuesto. Es la
única forma de que el cliente pueda separar lo que su banco ya publica de lo
que este equipo dedujo, y de que un lector futuro sepa qué se puede reutilizar
sin volver a verificarlo.

**La ausencia de información es información.** Cuando una fuente no dice algo
que debería decir, se registra como ausencia verificada, con la fuente donde se
buscó. Así se puede afirmar que cuatro categorías de tarjeta publican su tope
anual y el resto no, en vez de insinuarlo.

**Lo que no se sabe se convierte en pregunta, no en supuesto conveniente.** Las
seis preguntas abiertas al final de `assumptions.yaml` son parte de la entrega.
Un diagnóstico que rellena sus huecos con estimaciones plausibles le traslada
el riesgo al cliente sin avisarle.
