# Experimentos

Lo que se exploró y no quedó en el camino productivo. Vive aquí, separado, por
dos razones: conservar el recorrido del caso —qué se probó y por qué se
descartó es parte del resultado— y evitar que arrastre al pipeline
dependencias, descargas y riesgos que este no necesita.

Nada de esta carpeta se instala con el paquete, se ejecuta en la integración
continua ni entra en la imagen de contenedor.

## florence2-vision

Primer intento de extracción de precios con un modelo de visión y lenguaje
como caja negra: se le pasa la fotografía y una pregunta, y devuelve el texto
leído.

### Por qué no quedó

- **Peso.** Son unos 1.5 GB de pesos y el proyecto tiene que correr en un
  servidor modesto sin tarjeta gráfica.
- **Ejecución de código de terceros.** El modelo requiere confiar en el código
  del repositorio remoto para cargarse, lo que amplía la superficie de riesgo
  sin aportar nada que el enfoque clásico no resuelva.
- **Innecesario para el problema.** Los precios están en visores de siete
  segmentos, un dominio muy acotado. Un clasificador por plantillas sobre esa
  geometría es determinista, no necesita entrenamiento ni acelerador, y da un
  valor de confianza directamente interpretable. Es lo que quedó en
  `extraction/digit_ocr.py`.

### Lo que sí aportó, y se conserva

La lección sobre reproducibilidad, que aplica a cualquier modelo publicado y
está incorporada a la política de modelos del proyecto: **fijar la revisión
exacta, nunca la rama**.

El repositorio de este modelo no publica etiquetas ni versiones, solo una rama
principal, y en diciembre de 2024 una confirmación cambió los pesos a un modelo
distinto sobre esa misma rama. Es decir, "el modelo" no era una cosa fija:
descargarlo dos veces en fechas distintas daba dos modelos diferentes con el
mismo nombre. Por eso `config.yml` fija el identificador completo de la
confirmación, y el descargador falla ruidosamente si la revisión no está
declarada, en vez de caer en silencio a la rama.

También quedó documentado un detalle de compatibilidad: se pide la
implementación de atención más simple a propósito, porque el código remoto
declara su soporte para la variante acelerada leyendo un atributo que todavía
no existe en el momento en que la biblioteca lo consulta.

### Cómo se ejecuta, si hace falta

Desde `case-studies/cs1/`:

```bash
python experiments/florence2-vision/download_models.py
```

Es idempotente: si los pesos ya están en la caché, no vuelve a descargarlos.
Su configuración es propia y no se mezcla con la del pipeline, que vive en
`config/config.yaml`.
