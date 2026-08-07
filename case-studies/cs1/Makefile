# Entry points ejecutables del caso de estudio. Correr desde case-studies/cs1/.
#
# La ruta al interprete se detecta, no se quema: Windows pone el venv en
# Scripts/ y el resto en bin/.

VENV := .venv

ifeq ($(OS),Windows_NT)
	PY := $(VENV)/Scripts/python.exe
else
	PY := $(VENV)/bin/python
endif

.PHONY: help venv install models convert clean-logs clean-models

help:
	@echo "venv          crea el entorno virtual en $(VENV)"
	@echo "install       instala requirements.txt en el venv"
	@echo "models        descarga y cachea Florence-2 en la revision fijada"
	@echo "convert       HEIC -> JPG. Requiere INPUT= y OUTPUT="
	@echo "clean-logs    borra los .jsonl de corrida"
	@echo "clean-models  borra el cache de pesos (~1.5 GB, se vuelve a bajar)"

venv:
	python -m venv $(VENV)

install:
	$(PY) -m pip install -r requirements.txt

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

clean-logs:
	$(PY) -c "import pathlib; [p.unlink() for p in pathlib.Path('logs').glob('*.jsonl')]"

clean-models:
	$(PY) -c "import shutil, pathlib; shutil.rmtree(pathlib.Path('models'), ignore_errors=True); pathlib.Path('models').mkdir(); pathlib.Path('models/.gitkeep').touch()"
