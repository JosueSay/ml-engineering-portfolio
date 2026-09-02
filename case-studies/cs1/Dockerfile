# Imagen del caso de estudio CS1.
#
# Dos decisiones que explican la forma del archivo:
#
# 1. Ni los datos ni los modelos entran en la imagen. Entran por volumen. Meter
#    las fotografias aqui obligaria a reconstruir por cada foto nueva y haria
#    crecer la imagen sin control con el historico completo.
# 2. Se instala el motor alterno de lectura de texto. El codigo lo usa como
#    segunda opinion cuando esta disponible, y antes lo daba por hecho dentro
#    del contenedor sin que nada lo instalara.

FROM python:3.12-slim AS base

# libGL y libglib son dependencias de sistema de la biblioteca de vision.
# tesseract-ocr es el motor alterno de lectura.
# El upgrade no es rutina: la imagen base se reconstruye cada cierto tiempo y
# entre reconstrucciones acumula paquetes con actualizacion de seguridad ya
# publicada por la distribucion. Sin esta linea se publican con ella.
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
        tesseract-ocr \
        libgl1 \
        libglib2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# pip viene en la imagen base y envejece con ella. La version que trae hoy
# acumula seis vulnerabilidades con arreglo publicado, y son las unicas que el
# analisis encuentra en toda la imagen. Actualizarlo es una linea; dejarlo es
# publicar una imagen con lo unico que se podia cerrar sin cerrar.
RUN python -m pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY scripts ./scripts
COPY tests ./tests


# La estructura de datos existe vacia: los volumenes se montan encima y el
# codigo no tiene que comprobar si cada carpeta esta antes de escribir.
RUN mkdir -p \
        data/raw \
        data/interim \
        data/processed/bronze \
        data/processed/silver \
        data/processed/gold \
        data/db \
        models/vendor \
        models/trained \
        reports \
        logs \
        keys

# La raiz se declara de forma explicita: con el paquete instalado de forma no
# editable, deducirla del arbol de archivos ya no aplica.
#
# Dentro del contenedor el puerto es fijo. El parametrizable es el del anfitrion
# y lo decide quien levanta el servicio, no la imagen: API_PORT vive en .env y
# lo lee compose para el lado de fuera del mapeo.
ENV FUEL_PRICE_GT_ROOT=/app


FROM base AS production

# Con los extras, la instalacion minima no trae ni el servidor web ni el motor
# de entrenamiento, y esta imagen necesita los dos: sirve una recomendacion, y
# para leer un modelo hace falta la misma biblioteca con la que se escribio.
#
# Y despues se quita pip. Un contenedor que ya tiene su codigo instalado no
# necesita un instalador dentro, y el que traia la imagen base era lo unico que
# el analisis encontraba: sus dependencias empotradas no se pueden actualizar
# por separado, harian falta versiones de pip que cambien lo que empotra.
# Quitarlo cierra ese frente entero y reduce lo que se puede hacer dentro del
# contenedor si alguien llega a el.
RUN pip install --no-cache-dir '.[serving,modeling]' \
    && python -m pip uninstall --yes pip

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD curl -sf http://localhost:8000/health || exit 1

CMD ["uvicorn", "fuel_price_gt.serving.api:app", "--host", "0.0.0.0", "--port", "8000"]


# Cuelga de la base y no de produccion: alli ya no hay instalador con el que
# anadir las herramientas de desarrollo.
FROM base AS test

RUN pip install --no-cache-dir '.[dev]'
CMD ["pytest", "-q"]
