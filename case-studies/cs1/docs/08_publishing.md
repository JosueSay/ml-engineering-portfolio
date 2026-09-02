# Publicar el paquete

Cómo se construye, se verifica y se publica la distribución. Parte de la
documentación; el índice está en [README.md](README.md).

## Estado

Publicado: <https://test.pypi.org/project/fuel-price-gt/0.3.2/>

Comprobado instalando desde el índice en un entorno limpio, desde una carpeta
vacía: `build-data` da 212 filas, `train` da un error medio de 3.22 y
`recommend` devuelve su decisión. Sin el extra de modelado, `train` dice qué
instalar.

## Qué se publica y para qué

El criterio que se fijó: **quien instale el paquete debe poder usarlo sin
clonar el repositorio**. No un envoltorio que demuestre que se sabe empaquetar,
sino algo que sirva.

Comprobado en instalación limpia:

```bash
pip install fuel-price-gt
cd ~/cualquier-carpeta
fuel-price-gt build-data                 # con la instalacion minima
pip install "fuel-price-gt[modeling]"
fuel-price-gt train --fuel regular
fuel-price-gt recommend --fuel regular
```

Eso funciona porque la configuración de referencia **viaja dentro del
paquete**. Sin ella, el módulo instalado busca `config/config.yaml` junto al
código, no lo encuentra, y falla con un error que no dice nada útil. Era el
fallo principal que arreglaba esta fase.

## Cómo está armado

| Decisión | Motivo |
|---|---|
| `hatchling` como sistema de construcción | Es el que se probó en el ejercicio de empaquetado propio; no se inventa un procedimiento distinto por proyecto |
| Versión leída del propio paquete | Dos números que tienen que coincidir acaban por no hacerlo |
| Disposición bajo `src/` | Evita que las pruebas importen del árbol de fuentes en vez de lo instalado |
| Licencia por expresión y archivo por patrón | Formato actual de metadatos |
| Extras opcionales | Quien instale esto para leer el precio de su foto no debería bajarse el motor de entrenamiento ni el servidor web |

### Los extras

```bash
pip install fuel-price-gt              # leer fotografias y construir capas
pip install "fuel-price-gt[modeling]"  # + entrenamiento
pip install "fuel-price-gt[serving]"   # + servicio web
pip install "fuel-price-gt[gdrive]"    # + carpeta privada de Drive
pip install "fuel-price-gt[all]"       # todo
```

Las otras dos vías de ingesta —manifiesto y clave de API— no necesitan extra:
usan el cliente HTTP que ya viene.

Repartir dependencias tiene un coste que se paga en todos los sitios que daban
por hecho lo que antes venía de serie —la interfaz de línea de comandos, la
imagen de contenedor— y se paga la primera vez: una
importación de módulo se ejecuta siempre, también al pedir la ayuda, así que
basta importar arriba algo que vive en un extra para que la instalación mínima
no arranque. Lo que un extra provee se importa dentro del comando que lo usa, y
si falta, el comando dice qué instalar en vez de terminar en un rastro de
importación. El flujo lo comprueba en cada publicación: primero la instalación
mínima, después el extra, en ese orden. Al revés no distinguiría una
dependencia opcional de una obligatoria.

## Las etiquetas

Una etiqueta `cs1-v<version>` hace dos cosas a la vez: marca una entrega en el
historial y dispara la publicación. Por eso **la versión del paquete y la
etiqueta tienen que coincidir**, y el flujo lo comprueba antes de construir:

```
version del paquete: 0.1.0
etiqueta:            0.2.0
::error:: La etiqueta y la version del paquete no coinciden.
```

Publicar con versiones distintas dejaría en el índice una versión que el código
no declara, y a partir de ahí nadie sabría qué contiene realmente.

Las etiquetas `cs1-v0.1.0` y `cs1-v0.2.0` existentes marcan el cierre de las
fases A y B; ninguna se publicó. Son marcas de entrega, y eso es legítimo: la
publicación solo ocurre si además la versión coincide.

Al subir versión, según versionado semántico:

- Funcionalidad nueva compatible: menor. `0.2.0` a `0.3.0`.
- Corrección sin cambio de interfaz: parche. `0.3.0` a `0.3.1`.
- Cambio que rompe: mayor. Aquí sería cambiar el nombre de un comando, de un
  argumento o de una clave de configuración.

## Publicar

### Preparación

La versión declarada en `src/fuel_price_gt/__init__.py` es la que manda. Para
la primera publicación quedó en `0.3.0`; para las siguientes se sube ahí antes
de etiquetar.

```bash
cd case-studies/cs1
make gates           # todas las puertas
make publish-check   # construye y revisa que quedo dentro
make docker-smoke    # la imagen construye y la API responde
```

`docker-smoke` no es opcional aquí: la imagen instala extras distintos de los
que instala una comprobación en entorno virtual, y ese desajuste ya rompió una
publicación.

### Disparar la publicación

```bash
git tag -a cs1-v0.3.0 -m "CS1: paquete publicable"
git push origin cs1-v0.3.0
```

El flujo hace tres cosas en orden, y solo sigue si la anterior pasó:

1. **Construir y verificar.** Comprueba que la etiqueta coincide con la
   versión, construye las dos distribuciones, valida los metadatos y revisa que
   no se cuele nada indebido: ni `.env`, ni `keys/`, ni fotografías, ni la base
   de datos, ni modelos entrenados. También comprueba lo contrario: que la
   configuración de referencia **sí** esté dentro, porque sin ella el paquete
   instalado no arranca.

2. **Instalar en limpio y ejecutar**, en Linux y en Windows. Las dos
   plataformas encontraron cosas distintas: Linux, que la instalación mínima no
   arrancaba sin el extra; Windows, que su consola trae cp1252 y no sabe
   escribir una tilde ni una flecha, y todo lo que este programa imprime está
   en español. Ninguna de las dos se ve desarrollando en una sola máquina. Es lo que la
   Es lo que la actividad pedía demostrar —que corre en máquinas distintas—
   comprobado en cada publicación en vez de con una captura de pantalla. Primero la
   instalación mínima, luego que lo que necesita un extra lo diga, y por último
   el flujo completo con el extra puesto.

3. **Publicar**, tras aprobación manual en el entorno `testpypi`.

Ese último paso pide aprobación a propósito: publicar tiene efecto fuera del
repositorio y **no se deshace**. Una versión subida no se puede reemplazar,
solo retirar.

### Sin publicar

Para probar el flujo entero sin subir nada, lanzarlo a mano desde la interfaz
de Actions con la opción de ensayo activada. Construye, verifica e instala en
las dos plataformas, y se detiene antes de publicar.

## Configuración necesaria

Una sola vez, y los detalles están en
[05_operations.md](05_operations.md):

```bash
gh secret set TESTPYPI_API_TOKEN < case-studies/cs1/keys/testpypi-api.key
```

Y crear el entorno `testpypi` en la configuración del repositorio, con revisión
requerida. Sin el entorno el trabajo de publicación no encuentra dónde correr;
sin la revisión, publica sin preguntar.

## Instalar lo publicado

```bash
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ fuel-price-gt
```

El segundo índice hace falta porque las dependencias viven en el índice normal,
no en el de pruebas. Sin él, la instalación falla buscando `pandas` en un índice
donde no está.

## Qué comprobar después

```bash
python -m venv /tmp/prueba && source /tmp/prueba/bin/activate
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ fuel-price-gt
cd /tmp && fuel-price-gt build-data
```

Si eso funciona desde una carpeta vacía, la publicación sirve. Si falla
buscando configuración, algo quedó fuera de la distribución.
