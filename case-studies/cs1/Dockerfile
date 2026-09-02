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
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        tesseract-ocr \
        libgl1 \
        libglib2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY scripts ./scripts
COPY tests ./tests


FROM base AS production

RUN pip install --no-cache-dir .

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
ENV FUEL_PRICE_GT_ROOT=/app \
    API_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD curl -sf http://localhost:8000/health || exit 1

CMD ["uvicorn", "fuel_price_gt.serving.api:app", "--host", "0.0.0.0", "--port", "8000"]


FROM production AS test

RUN pip install --no-cache-dir '.[dev]'
CMD ["pytest", "-q"]
