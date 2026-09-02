#!/usr/bin/env bash
# Crea el archivo de entorno local a partir de la plantilla versionada.
#
# La plantilla es la unica fuente de verdad de que variables existen. Copiarla
# en vez de escribir el archivo aqui evita que las dos se desincronicen: si se
# agrega una variable, se agrega en la plantilla y todos la reciben.
#
# Uso:
#   scripts/01_env_init.sh              crea .env si no existe
#   scripts/01_env_init.sh --force      lo reescribe, guardando copia del anterior
#   scripts/01_env_init.sh --check      solo compara, no escribe

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

PLANTILLA=".env.example"
DESTINO=".env"
modo="crear"

case "${1:-}" in
    --force) modo="forzar" ;;
    --check) modo="revisar" ;;
    "")      ;;
    *)       printf 'Opcion desconocida: %s\n' "$1" >&2; exit 2 ;;
esac

if [ ! -f "$PLANTILLA" ]; then
    printf 'No existe %s. Es la plantilla versionada y sin ella no hay de donde copiar.\n' "$PLANTILLA" >&2
    exit 1
fi

# Nombres de variable declarados en un archivo, ignorando comentarios y vacios.
variables_de() {
    grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$1" | cut -d= -f1 | sort
}

if [ "$modo" = "revisar" ]; then
    if [ ! -f "$DESTINO" ]; then
        printf 'No existe %s. Crear con: make env-init\n' "$DESTINO"
        exit 1
    fi
    faltan=$(comm -23 <(variables_de "$PLANTILLA") <(variables_de "$DESTINO"))
    sobran=$(comm -13 <(variables_de "$PLANTILLA") <(variables_de "$DESTINO"))
    estado=0
    if [ -n "$faltan" ]; then
        printf 'Variables en la plantilla que faltan en %s:\n' "$DESTINO"
        printf '  %s\n' $faltan
        estado=1
    fi
    if [ -n "$sobran" ]; then
        printf 'Variables en %s que ya no estan en la plantilla:\n' "$DESTINO"
        printf '  %s\n' $sobran
        estado=1
    fi
    [ "$estado" -eq 0 ] && printf '%s y %s estan sincronizados.\n' "$DESTINO" "$PLANTILLA"
    exit "$estado"
fi

if [ -f "$DESTINO" ] && [ "$modo" != "forzar" ]; then
    printf '%s ya existe. Se conserva.\n' "$DESTINO"
    printf 'Para comparar contra la plantilla:  scripts/01_env_init.sh --check\n'
    printf 'Para reescribirlo:                  scripts/01_env_init.sh --force\n'
    exit 0
fi

if [ -f "$DESTINO" ]; then
    respaldo="${DESTINO}.anterior"
    cp "$DESTINO" "$respaldo"
    printf 'Copia del anterior en %s\n' "$respaldo"
fi

cp "$PLANTILLA" "$DESTINO"
printf 'Creado %s desde %s\n' "$DESTINO" "$PLANTILLA"
printf '\nRevisar los valores vacios antes de usarlo. Recordar que aqui no va\n'
printf 'ninguna credencial: las que hacen falta se colocan en keys/ y este\n'
printf 'archivo solo guarda su ruta. Ver keys/README.md\n'
