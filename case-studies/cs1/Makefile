# Entry points ejecutables del caso de estudio. Correr desde case-studies/cs1/.
#
# La ruta al interprete se detecta, no se quema: Windows pone el venv en
# Scripts/ y el resto en bin/.

VENV := .venv

ifeq ($(OS),Windows_NT)
	DEFAULT_PY := $(if $(wildcard $(VENV)/Scripts/python.exe),$(VENV)/Scripts/python.exe,python)
else
	DEFAULT_PY := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python)
endif

PY ?= $(DEFAULT_PY)

.PHONY: help venv install install-mlops install-dev models convert lint test extract transform train evaluate recommend pipeline docker-build docker-smoke clean clean-logs clean-models

help:
	@echo "venv          crea el entorno virtual en $(VENV)"
	@echo "install       instala requirements.txt en el venv"
	@echo "install-mlops instala el paquete gasolina-gt"
	@echo "install-dev   instala gasolina-gt y herramientas de desarrollo"
	@echo "models        descarga y cachea Florence-2 en la revision fijada"
	@echo "convert       HEIC -> JPG. Requiere INPUT= y OUTPUT="
	@echo "lint          ejecuta Ruff sobre src, tests y scripts"
	@echo "test          ejecuta la suite de pytest"
	@echo "pipeline      ejecuta extraccion, datos, entrenamiento, evaluacion e inferencia"
	@echo "docker-smoke  construye la imagen y verifica el endpoint /health"
	@echo "clean-logs    borra los .jsonl de corrida"
	@echo "clean-models  borra el cache de pesos (~1.5 GB, se vuelve a bajar)"

venv:
	python -m venv $(VENV)

install:
	$(PY) -m pip install -r requirements.txt

install-mlops:
	$(PY) -m pip install -e .

install-dev:
	$(PY) -m pip install -e '.[dev]'

models:
	$(PY) download_models.py

# make convert INPUT=data/raw OUTPUT=imageConvert/output
convert:
ifndef INPUT
	$(error falta INPUT. Uso: make convert INPUT=<dir> OUTPUT=<dir>)
endif
ifndef OUTPUT
	$(error falta OUTPUT. Uso: make convert INPUT=<dir> OUTPUT=<dir>)
endif
	$(PY) -m imageConvert.convert --input $(INPUT) --output $(OUTPUT)

COMBUSTIBLE ?= regular
HORIZONTE ?= 1
HORA ?= 18
IMAGE ?= gasolina-gt:ci

lint:
	$(PY) -m ruff check src tests scripts

test:
	$(PY) -m pytest -q

extract:
	$(PY) scripts/stage_extract.py

transform:
	$(PY) -m gasolina_gt.cli build-data

train:
	$(PY) -m gasolina_gt.cli train --combustible $(COMBUSTIBLE)

evaluate:
	$(PY) scripts/quality_gate.py

recommend:
	$(PY) -m gasolina_gt.cli recommend --combustible $(COMBUSTIBLE) --horizonte $(HORIZONTE) --hora $(HORA)

pipeline: extract transform train evaluate recommend

docker-build:
	docker build --target production -t $(IMAGE) .

docker-smoke: docker-build
	docker run -d --rm --name gasolina-gt-smoke -p 8000:8000 $(IMAGE)
	for i in $$(seq 1 30); do curl -sf http://localhost:8000/health && break || sleep 2; done
	docker stop gasolina-gt-smoke

clean:
	$(PY) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('datos_procesados', 'reports')]"

clean-logs:
	$(PY) -c "import pathlib; [p.unlink() for p in pathlib.Path('logs').glob('*.jsonl')]"

clean-models:
	$(PY) -c "import shutil, pathlib; shutil.rmtree(pathlib.Path('models'), ignore_errors=True); pathlib.Path('models').mkdir(); pathlib.Path('models/.gitkeep').touch()"
