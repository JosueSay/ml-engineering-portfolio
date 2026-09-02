#!/usr/bin/env bash
# Prepara la carpeta de credenciales y reporta cuales faltan.
#
# El codigo lee siempre de keys/, sin importar el entorno. En una maquina local
# los archivos se colocan a mano; en integracion continua no hay archivos sino
# secretos del repositorio, y este script los materializa antes de ejecutar
# cualquier etapa. Asi la ruta de lectura del codigo es una sola:
#
#   secretos del repositorio  ->  este script  ->  keys/  ->  codigo
#
# Ninguna credencial se imprime. Solo se dice si esta o no esta.
#
# Uso:
#   scripts/02_keys_init.sh             materializa lo que haya y reporta
#   scripts/02_keys_init.sh --status    solo reporta, no escribe nada

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

KEYS_DIR="keys"
solo_estado=0

case "${1:-}" in
    --status) solo_estado=1 ;;
    "")       ;;
    *)        printf 'Opcion desconocida: %s\n' "$1" >&2; exit 2 ;;
esac

mkdir -p "$KEYS_DIR"
[ -f "$KEYS_DIR/.gitkeep" ] || touch "$KEYS_DIR/.gitkeep"

# Cada entrada: nombre de archivo | variable de entorno de origen | para que sirve
CREDENCIALES=(
    "google-drive-service-account.json|GDRIVE_SERVICE_ACCOUNT_JSON|leer la carpeta compartida de fotografias"
    "object-store.env|OBJECT_STORE_CREDENTIALS|acceso al almacenamiento de objetos"
    "testpypi-api.key|TESTPYPI_API_TOKEN|publicar la distribucion en el indice de pruebas"
    "huggingface.key|HF_TOKEN|descargar un modelo de acceso restringido"
)

# Escribe el contenido de una variable de entorno a un archivo, aceptando texto
# plano o base64. En integracion continua conviene base64: un secreto de varias
# lineas, como un JSON, sobrevive intacto al paso por el entorno.
materializar() {
    local destino="$1" contenido="$2"
    if printf '%s' "$contenido" | base64 -d >/dev/null 2>&1 && ! printf '%s' "$contenido" | head -c 1 | grep -q '[{[]'; then
        printf '%s' "$contenido" | base64 -d > "$destino"
    else
        printf '%s' "$contenido" > "$destino"
    fi
    chmod 600 "$destino"
}

presentes=0
ausentes=0
creados=0

echo
echo "Credenciales en $KEYS_DIR/"
echo

for entrada in "${CREDENCIALES[@]}"; do
    IFS='|' read -r archivo variable proposito <<< "$entrada"
    ruta="$KEYS_DIR/$archivo"

    if [ -f "$ruta" ] && [ -s "$ruta" ]; then
        printf '  [ok]     %-38s %s\n' "$archivo" "$proposito"
        presentes=$((presentes + 1))
        continue
    fi

    valor="${!variable:-}"
    if [ -n "$valor" ] && [ "$solo_estado" -eq 0 ]; then
        materializar "$ruta" "$valor"
        printf '  [creado] %-38s desde %s\n' "$archivo" "$variable"
        creados=$((creados + 1))
        presentes=$((presentes + 1))
    elif [ -n "$valor" ]; then
        printf '  [listo]  %-38s se crearia desde %s\n' "$archivo" "$variable"
        ausentes=$((ausentes + 1))
    else
        printf '  [falta]  %-38s %s\n' "$archivo" "$proposito"
        ausentes=$((ausentes + 1))
    fi
done

echo
printf 'Presentes: %d   Faltantes: %d' "$presentes" "$ausentes"
[ "$creados" -gt 0 ] && printf '   Creados ahora: %d' "$creados"
printf '\n'

if [ "$ausentes" -gt 0 ]; then
    echo
    echo "Ninguna es obligatoria: lo que falte hace que esa parte del sistema"
    echo "use su alternativa local en vez de fallar. Como obtener cada una y"
    echo "con que permisos minimos: $KEYS_DIR/README.md"
fi

# Nunca falla: la ausencia de credenciales es un estado valido del proyecto.
exit 0
