#!/usr/bin/env bash
# Comprueba que la maquina tiene lo necesario para correr el caso de estudio.
#
# Existe porque el fallo mas comun no es un error de codigo sino un interprete
# equivocado: `python3` apunta a la version del sistema, que puede estar por
# debajo del minimo del proyecto, y las pruebas revientan al importar con un
# mensaje que no dice nada sobre la causa real.
#
# No instala nada. Informa y devuelve un codigo de salida distinto de cero si
# algo bloqueante falta, para poder encadenarlo en un Makefile o en CI.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

MINIMO_MAYOR=3
MINIMO_MENOR=11
fallos=0
avisos=0

ok()    { printf '  [ok]    %s\n' "$1"; }
falla() { printf '  [falta] %s\n' "$1"; fallos=$((fallos + 1)); }
avisa() { printf '  [aviso] %s\n' "$1"; avisos=$((avisos + 1)); }

echo
echo "Entorno del caso de estudio CS1"
echo

# --- Interprete ---------------------------------------------------------------
# Se prefiere el del entorno virtual; si no existe se busca uno del sistema que
# cumpla el minimo, en vez de asumir que `python3` sirve.
echo "Interprete de Python (minimo ${MINIMO_MAYOR}.${MINIMO_MENOR})"

interprete=""
if [ -x ".venv/bin/python" ]; then
    interprete=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
    interprete=".venv/Scripts/python.exe"
fi

if [ -n "$interprete" ]; then
    ok "entorno virtual encontrado: $interprete"
else
    avisa "no hay entorno virtual en .venv (crear con: make venv)"
    for candidato in python3.13 python3.12 python3.11 python3 python; do
        if command -v "$candidato" >/dev/null 2>&1; then
            interprete="$candidato"
            break
        fi
    done
fi

if [ -z "$interprete" ]; then
    falla "no se encontro ningun interprete de Python"
else
    version=$("$interprete" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null)
    cumple=$("$interprete" -c "import sys; print(1 if sys.version_info[:2] >= (${MINIMO_MAYOR}, ${MINIMO_MENOR}) else 0)" 2>/dev/null)
    if [ "$cumple" = "1" ]; then
        ok "$interprete es $version"
    else
        falla "$interprete es $version, por debajo del minimo ${MINIMO_MAYOR}.${MINIMO_MENOR}"
        for candidato in python3.13 python3.12 python3.11; do
            if command -v "$candidato" >/dev/null 2>&1; then
                printf '          hay uno valido en: %s\n' "$(command -v "$candidato")"
                break
            fi
        done
    fi
fi

# --- Dependencias --------------------------------------------------------------
echo
echo "Dependencias del paquete"
if [ -n "$interprete" ]; then
    for modulo in numpy pandas sklearn cv2 yaml PIL; do
        if "$interprete" -c "import $modulo" >/dev/null 2>&1; then
            ok "$modulo"
        else
            falla "$modulo (instalar con: make install-dev)"
        fi
    done
    # Estas no bloquean el pipeline de datos, solo las etapas que las usan.
    for modulo in xgboost fastapi pillow_heif; do
        if "$interprete" -c "import $modulo" >/dev/null 2>&1; then
            ok "$modulo"
        else
            avisa "$modulo, necesario para entrenamiento o servicio"
        fi
    done
fi

# --- Herramientas del sistema ---------------------------------------------------
echo
echo "Herramientas del sistema"
if command -v git >/dev/null 2>&1; then ok "git"; else falla "git"; fi
if command -v docker >/dev/null 2>&1; then ok "docker"; else avisa "docker, necesario solo para los contenedores"; fi
if command -v tesseract >/dev/null 2>&1; then
    ok "tesseract (motor alterno de lectura disponible)"
else
    avisa "tesseract no esta; se usa solo el lector de siete segmentos"
fi

# --- Configuracion y credenciales -------------------------------------------------
echo
echo "Configuracion"
if [ -f ".env" ]; then ok ".env"; else avisa ".env no existe (crear con: make env-init)"; fi
if [ -f "config/config.yaml" ]; then ok "config/config.yaml"; else falla "config/config.yaml"; fi
if [ -d "keys" ]; then ok "keys/"; else avisa "keys/ no existe (crear con: make keys-init)"; fi

# --- Estructura de datos ----------------------------------------------------------
echo
echo "Estructura de datos"
for d in data/raw data/interim data/processed/bronze data/processed/silver data/processed/gold models/vendor models/trained; do
    if [ -d "$d" ]; then ok "$d"; else falla "$d"; fi
done

imagenes=$(find data/raw -type f \( -iname '*.heic' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) 2>/dev/null | wc -l)
if [ "$imagenes" -gt 0 ]; then
    ok "$imagenes imagen(es) en data/raw"
else
    avisa "data/raw esta vacia (poblar con: make ingest)"
fi

# --- Resumen -----------------------------------------------------------------------
echo
if [ "$fallos" -gt 0 ]; then
    printf 'Faltan %d cosa(s) para poder ejecutar. %d aviso(s).\n\n' "$fallos" "$avisos"
    exit 1
fi
printf 'Entorno listo. %d aviso(s).\n\n' "$avisos"
exit 0
