#!/usr/bin/env bash
# Puertas deterministas que deben pasar antes de confirmar cambios.
#
# Se llama "puertas" y no "pruebas" porque incluye comprobaciones que no son
# pruebas: que no se cuele una credencial al control de versiones, que la
# plantilla de entorno y el archivo local no se hayan desincronizado, y que
# ninguna imagen haya entrado al repositorio.
#
# No arregla nada. Informa y devuelve un codigo distinto de cero si algo falla.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

fallos=0

titulo() { printf '\n%s\n' "$1"; }
ok()     { printf '  [ok]    %s\n' "$1"; }
falla()  { printf '  [falla] %s\n' "$1"; fallos=$((fallos + 1)); }

# El interprete del entorno virtual si existe; si no, el del sistema.
if [ -x ".venv/bin/python" ]; then
    PY=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
    PY=".venv/Scripts/python.exe"
else
    PY="${PY:-python3}"
fi

# --- Analisis estatico ---------------------------------------------------------
titulo "Analisis estatico"
if "$PY" -m ruff check src tests scripts >/tmp/ruff.out 2>&1; then
    ok "ruff"
else
    falla "ruff"
    sed 's/^/          /' /tmp/ruff.out | head -30
fi

# --- Pruebas -------------------------------------------------------------------
titulo "Pruebas"
if "$PY" -m pytest -q >/tmp/pytest.out 2>&1; then
    ok "pytest"
else
    falla "pytest"
    tail -20 /tmp/pytest.out | sed 's/^/          /'
fi

# --- Nada sensible en el control de versiones -------------------------------------
titulo "Credenciales fuera del control de versiones"

# Se listan los candidatos y se descartan aparte los dos archivos de keys/ que
# si deben estar versionados, en vez de usar una mirada adelantada que no todas
# las variantes de grep soportan.
sensibles=$(git ls-files \
    | grep -E '(^|/)\.env$|(^|/)\.env\.(local|development|staging|production)$|(^|/)keys/|\.(pem|key|p12|pfx)$' \
    | grep -vE '(^|/)keys/(README\.md|\.gitkeep)$' || true)

if [ -z "$sensibles" ]; then
    ok "ningun archivo de credenciales versionado"
else
    falla "hay archivos sensibles versionados:"
    printf '          %s\n' $sensibles
fi

# --- Ninguna imagen en el repositorio ----------------------------------------------
titulo "Datos fuera del control de versiones"
imagenes=$(git ls-files | grep -iE '\.(heic|jpg|jpeg|png|tif|tiff)$' | grep -v '^assets/' || true)
if [ -z "$imagenes" ]; then
    ok "ninguna imagen versionada"
else
    falla "hay imagenes versionadas:"
    printf '          %s\n' $imagenes
fi

# --- Plantilla de entorno sincronizada ----------------------------------------------
titulo "Entorno"
if [ ! -f ".env" ]; then
    ok ".env no existe todavia (nada que comparar)"
elif bash scripts/01_env_init.sh --check >/tmp/envcheck.out 2>&1; then
    ok ".env y .env.example sincronizados"
else
    falla ".env y .env.example difieren"
    sed 's/^/          /' /tmp/envcheck.out
fi

# --- Resumen ---------------------------------------------------------------------
echo
if [ "$fallos" -gt 0 ]; then
    printf 'Fallaron %d puerta(s).\n\n' "$fallos"
    exit 1
fi
printf 'Todas las puertas pasaron.\n\n'
exit 0
