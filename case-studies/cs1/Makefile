# Atajos del caso de estudio CS1. Correr desde case-studies/cs1/.
#
# Doble interfaz: la logica vive en scripts/ y en el CLI del paquete; este
# archivo es solo el atajo. Asi el mismo comando corre sin make, y la
# integracion continua no depende de make para nada.
#
# Aqui solo se declara lo que existe. Un objetivo que apunta a un script
# inexistente es una promesa rota. Lo pendiente esta en docs/work-plan.md.

.DEFAULT_GOAL := help
SHELL := /bin/bash

VENV := .venv

# La ruta al interprete se detecta, no se quema: Windows pone el entorno en
# Scripts/ y el resto en bin/.
ifeq ($(OS),Windows_NT)
	DEFAULT_PY := $(if $(wildcard $(VENV)/Scripts/python.exe),$(VENV)/Scripts/python.exe,python)
else
	DEFAULT_PY := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)
endif
PY ?= $(DEFAULT_PY)

# Parametros de las etapas. Se sobreescriben en la linea de comandos:
#   make train FUEL=super
FUEL ?= regular
HORIZON ?= 1
HOUR ?= 18
IMAGE ?= fuel-price-gt:ci

.PHONY: help verify ingest env-init env-check keys-init keys-status venv install install-dev \
        lint test format gates extract transform train evaluate recommend pipeline \
        models-status db-init db-browser \
        up down logs ps docker-build docker-smoke clean clean-logs clean-vendor clean-trained

define ayuda
	@grep -E '^($(1)):.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[36m%-16s\033[0m %s\n", $$1, $$2}'
endef

help: ## Muestra esta ayuda
	@echo ""
	@echo "  --- Puesta en marcha ---"
	$(call ayuda,verify|venv|install|install-dev|env-init|env-check|keys-init|keys-status)
	@echo ""
	@echo "  --- Pipeline de datos   (FUEL=regular|super|diesel|vpower) ---"
	$(call ayuda,ingest|extract|transform|train|evaluate|recommend|pipeline)
	@echo ""
	@echo "  --- Base de datos ---"
	$(call ayuda,db-init|db-browser)
	@echo ""
	@echo "  --- Modelos ---"
	$(call ayuda,models-status|clean-vendor|clean-trained)
	@echo ""
	@echo "  --- Contenedores ---"
	$(call ayuda,up|down|logs|ps|docker-build|docker-smoke)
	@echo ""
	@echo "  --- Calidad ---"
	$(call ayuda,gates|lint|test|format)
	@echo ""
	@echo "  --- Limpieza ---"
	$(call ayuda,clean|clean-logs)
	@echo ""
	@echo "  Lo pendiente por implementar esta en docs/work-plan.md"
	@echo ""

# --- Puesta en marcha ------------------------------------------------------------

verify: ## Comprueba que la maquina tiene lo necesario
	@bash scripts/00_verify_environment.sh

venv: ## Crea el entorno virtual en .venv
	@python3 -m venv $(VENV)

install: ## Instala el paquete
	@$(PY) -m pip install -e .

install-dev: ## Instala el paquete y las herramientas de desarrollo
	@$(PY) -m pip install -e '.[dev]'

env-init: ## Crea .env desde la plantilla versionada
	@bash scripts/01_env_init.sh

env-check: ## Compara .env contra la plantilla, sin escribir
	@bash scripts/01_env_init.sh --check

keys-init: ## Prepara keys/ y materializa lo que haya en el entorno
	@bash scripts/02_keys_init.sh

keys-status: ## Informa que credenciales faltan, sin crear nada
	@bash scripts/02_keys_init.sh --status

# --- Pipeline de datos -------------------------------------------------------------
# Las etapas del pipeline son parte del paquete y se invocan por su interfaz de
# linea de comandos, no por un script envoltorio: una capa que solo reenvia
# argumentos es una capa que hay que mantener sin que aporte nada.

ingest: ## Trae las fotografias de la fuente configurada. LIMIT=10 para probar
	@$(PY) scripts/10_ingest_images.py $(if $(LIMIT),--limit $(LIMIT),)

extract: ## Lee los precios de las fotografias (Bronze)
	@$(PY) scripts/12_extract_prices.py

transform: ## Construye Silver y Gold
	@$(PY) -m fuel_price_gt.cli build-data

train: ## Entrena y evalua los horizontes configurados
	@$(PY) -m fuel_price_gt.cli train --fuel $(FUEL)

evaluate: ## Compuerta de calidad sobre el modelo entrenado
	@$(PY) scripts/15_quality_gate.py

recommend: ## Recomendacion de carga
	@$(PY) -m fuel_price_gt.cli recommend --fuel $(FUEL) --horizon $(HORIZON) --hour $(HOUR)

pipeline: ingest extract transform train evaluate recommend ## Encadena todas las etapas

# --- Base de datos -----------------------------------------------------------------------

db-init: ## Crea el esquema si falta y muestra cuantas filas hay en cada tabla
	@$(PY) scripts/20_db_init.py

db-browser: ## Levanta el explorador web de la base para recorrer el linaje
	@docker compose --profile tools up -d db-browser
	@echo "  explorador en http://localhost:$${DB_BROWSER_PORT:-19030}"

# --- Modelos ---------------------------------------------------------------------------

models-status: ## Que hay en cada almacen de modelos y con que datos se entreno
	@$(PY) scripts/31_models_status.py

# --- Contenedores --------------------------------------------------------------------

up: ## Levanta el stack
	@docker compose up -d

down: ## Detiene el stack conservando los volumenes
	@docker compose down

logs: ## Sigue los logs. SERVICE=api para uno solo
	@docker compose logs -f $(SERVICE)

ps: ## Estado de los contenedores
	@docker compose ps

docker-build: ## Construye la imagen de produccion
	@docker build --target production -t $(IMAGE) .

docker-smoke: docker-build ## Construye y verifica que la API responda
	@bash -c 'set -e; \
	  port=$${API_PORT:-19010}; \
	  docker run -d --rm --name fuel-price-gt-smoke -p $$port:8000 $(IMAGE) >/dev/null; \
	  trap "docker stop fuel-price-gt-smoke >/dev/null 2>&1 || true" EXIT; \
	  for _ in $$(seq 1 30); do \
	    curl -sf http://localhost:$$port/health >/dev/null && { echo "  API respondiendo en $$port"; exit 0; }; \
	    sleep 2; \
	  done; \
	  echo "  la API no respondio a tiempo"; docker logs fuel-price-gt-smoke; exit 1'

# --- Calidad ---------------------------------------------------------------------------

gates: ## Todas las puertas: linter, pruebas y revision de secretos
	@bash scripts/03_gates.sh

lint: ## Analisis estatico
	@$(PY) -m ruff check src tests scripts

test: ## Pruebas
	@$(PY) -m pytest -q

format: ## Reformatea el codigo. Reescribe archivos
	@$(PY) -m ruff format src tests scripts
	@$(PY) -m ruff check --fix src tests scripts

# --- Limpieza ------------------------------------------------------------------------------

clean: ## Borra artefactos derivados. No toca data/, keys/ ni los modelos
	@$(PY) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('reports', '.ruff_cache', '.pytest_cache')]"
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "  limpio"

clean-logs: ## Borra los registros de corrida
	@$(PY) -c "import pathlib; [p.unlink() for p in pathlib.Path('logs').glob('*.jsonl')]"

clean-vendor: ## Borra los pesos descargados de terceros. Se vuelven a bajar
	@$(PY) -c "import pathlib, shutil; d = pathlib.Path('models/vendor'); shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True); (d / '.gitkeep').touch()"
	@echo "  models/vendor vaciado"

clean-trained: ## Borra los modelos entrenados propios
	@$(PY) -c "import pathlib, shutil; d = pathlib.Path('models/trained'); shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True); (d / '.gitkeep').touch()"
	@echo "  models/trained vaciado"
