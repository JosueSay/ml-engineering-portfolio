# Commits de la fase D

Propuesta de división, en el mismo estilo que la
[fase A](fase-a-commits.md) y la [fase B](fase-b-commits.md): Conventional
Commits en español.

El orden importa aquí más que en las fases anteriores, porque el último paso
publica: primero el arreglo que hace utilizable la distribución, luego cómo se
construye, luego quién la publica, y solo al final la versión y la etiqueta.

Ejecutar todo desde la raíz del repositorio.

## 0. Comprobar el punto de partida

```bash
cd case-studies/cs1 && make gates && make publish-check && cd ../..
git status --short
git reset   # solo si quedara algo preparado de antes
```

`publish-check` tiene que decir `distribucion correcta`. Si dice que falta la
configuración de referencia, el commit 1 no está completo.

## 1. El paquete instalado, utilizable

```bash
git add case-studies/cs1/src/fuel_price_gt/resources/ \
        case-studies/cs1/src/fuel_price_gt/config.py \
        case-studies/cs1/src/fuel_price_gt/cli.py \
        case-studies/cs1/src/fuel_price_gt/data/pipeline.py
git commit -m "fix(cs1): hacer que la distribucion instalada funcione sin el repositorio

Instalado fuera del arbol de fuentes, el paquete fallaba con un archivo no
encontrado: buscaba config/config.yaml junto al codigo y ahi no existe. Quien
instalara la distribucion no podia ejecutar nada.

La configuracion de referencia ahora viaja dentro del paquete y se lee como
recurso. Sigue ganando lo que haya en disco -lo que declare quien ejecuta,
despues el repositorio- y el recurso empaquetado queda como respaldo. Asi el
desarrollo no cambia: se sigue editando config/config.yaml sin reinstalar.

El punto de entrada crea el esquema antes de atender cualquier orden. Sin eso
cada consulta tendria que defenderse por su cuenta de que la base no exista
todavia, y bastaba una sin proteger para que la primera ejecucion terminara en
un error de SQL en vez de decir que aun no hay datos.

Comprobado en entorno limpio: instalar, situarse en una carpeta cualquiera y
completar build-data, train y recommend."
```

## 2. Cómo se construye

```bash
git add case-studies/cs1/pyproject.toml
git commit -m "build(cs1): empaquetar con hatchling y declarar extras opcionales

Mismo procedimiento que el ejercicio de empaquetado propio, para no inventar
uno distinto por proyecto. La version se lee del propio paquete y no se repite
en los metadatos: dos numeros que tienen que coincidir acaban por no hacerlo.

Las dependencias se parten. Lo minimo es leer una fotografia y construir las
capas de datos; quien instale esto para eso no deberia bajarse el motor de
entrenamiento ni el servidor web. Entrenamiento, servicio y acceso a la carpeta
privada de Drive quedan en extras.

El paquete de fuentes lleva lo necesario para reconstruir y verificar, y nada
mas: ni datos, ni credenciales, ni artefactos de ejecucion."
```

## 3. Construir y verificar en local

```bash
git add case-studies/cs1/Makefile
git commit -m "build(cs1): objetivos para construir y revisar la distribucion

publish-check comprueba las dos direcciones. Que no se cuele lo que no debe
-.env, keys/, fotografias, la base de datos, modelos entrenados- y que si este
la configuracion de referencia, porque sin ella el paquete instalado arranca
buscando un archivo que en esa maquina no existe.

Publicar no tiene objetivo aqui a proposito: no deberia bastar una orden de
consola para subir algo que no se puede retirar."
```

## 4. Quién publica

```bash
git add .github/workflows/cs1-publish.yml
git commit -m "ci(cs1): publicar por etiqueta, con verificacion y aprobacion

Tres pasos en orden y cada uno condiciona al siguiente: construir y verificar,
instalar en limpio y ejecutar en Linux y en Windows, publicar.

Se dispara por etiqueta y no en cada empujon porque publicar tiene efecto fuera
del repositorio y no se deshace: una version subida no se puede reemplazar,
solo retirar. Por lo mismo el ultimo paso pide aprobacion manual en un entorno
declarado.

Antes de construir comprueba que la etiqueta y la version del paquete
coinciden. Publicar con versiones distintas dejaria en el indice una version
que el codigo no declara, y a partir de ahi nadie sabe que contiene.

Las dos plataformas son el punto: la actividad pedia demostrar que el paquete
corre en maquinas distintas, y esto lo comprueba en cada publicacion en vez de
con una captura de pantalla."
```

## 5. La credencial de Drive

Quedó pendiente del cierre de la fase C.

```bash
git add case-studies/cs1/scripts/02_keys_init.sh
git commit -m "chore(cs1): declarar la clave de API de Drive entre las credenciales

Son dos vias distintas con permisos distintos: la cuenta de servicio abre una
carpeta privada, la clave de API solo lee una carpeta ya compartida por enlace.
Reportarlas como una sola dejaba sin explicar cual hacia falta."
```

## 6. La documentación

```bash
git add case-studies/cs1/docs/ case-studies/cs1/README.md
git commit -m "docs(cs1): documentar la construccion y publicacion del paquete

08_publishing.md recoge que se publica y por que, como esta armado, el papel de
las etiquetas y el procedimiento completo. 03_commands.md incorpora los
objetivos nuevos.

El README pasa a servir tambien como descripcion en el indice de paquetes: la
instalacion va primero, porque quien llega desde ahi no ha clonado nada, y el
enlace al plan de trabajo se vuelve absoluto porque uno relativo no lleva a
ninguna parte fuera del repositorio."
```

## 7. La versión

```bash
git add case-studies/cs1/src/fuel_price_gt/__init__.py
git commit -m "chore(cs1): version 0.3.0

Primera version publicable. Las dos anteriores marcaron el cierre de las fases
A y B sin salir del repositorio."
```

## 7b. El reparto de extras, arreglado

La etiqueta `cs1-v0.3.0` disparó el flujo y falló en el paso 2, antes de
publicar. Nada llegó al índice.

```bash
git add case-studies/cs1/src/fuel_price_gt/cli.py \
        case-studies/cs1/src/fuel_price_gt/__init__.py \
        case-studies/cs1/README.md \
        case-studies/cs1/docs/ \
        .github/workflows/cs1-publish.yml
git commit -m "fix(cs1): que la instalacion minima arranque sin los extras

Sacar xgboost a un extra dejo el paquete sin poder ejecutar ni --help: la
interfaz importaba el modulo de entrenamiento arriba, y una importacion de
modulo se ejecuta siempre, tambien al pedir la ayuda.

Lo que provee un extra se importa ahora dentro del comando que lo usa. Sin el
extra puesto, train y recommend dicen que instalar en vez de terminar en un
rastro de importacion que no explica por que falta algo que nadie quito.

El fallo se colo porque la comprobacion en entorno limpio se hizo antes de
partir las dependencias, con xgboost todavia entre las obligatorias. El flujo
pasa a probar las dos instalaciones y en orden: primero la minima, despues el
extra. Al reves no distinguiria una dependencia opcional de una obligatoria y
el reparto seria decorativo.

Version 0.3.1: 0.3.0 quedo etiquetada y no publicable."
```

## 7c. La consola de Windows

Con el extra arreglado, Linux pasó y Windows no.

```bash
git add case-studies/cs1/src/fuel_price_gt/cli.py \
        case-studies/cs1/src/fuel_price_gt/__init__.py \
        case-studies/cs1/docs/
git commit -m "fix(cs1): imprimir en UTF-8 sin depender de la consola

La consola de Windows trae cp1252 y no sabe escribir ni una tilde ni una
flecha. Todo lo que este programa imprime esta en espanol -la ayuda, y la razon
que acompana a cada recomendacion- asi que pedir --help terminaba en un error
de codificacion.

Se reconfigura la salida en el propio programa y no con una variable de
entorno: eso arreglaria la maquina donde se declara, no la de quien instale el
paquete.

Version 0.3.2."
```

## 8. Publicar

Antes de etiquetar hay que tener puesto lo que la publicación necesita, y eso
no está en el repositorio:

```bash
# La credencial, en el repositorio de GitHub
gh secret set TESTPYPI_API_TOKEN < case-studies/cs1/keys/testpypi-api.key
gh secret list
```

Y crear el entorno `testpypi` en Settings, Environments, con revisión
requerida. Sin el entorno el paso de publicación no encuentra dónde correr;
sin la revisión, publica sin preguntar.

Conviene un ensayo antes de la etiqueta. Desde Actions, lanzar el flujo a mano
con la opción de ensayo activada: construye, verifica e instala en las dos
plataformas, y se detiene antes de publicar.

```bash
git push origin fuel-case-study

git tag -a cs1-v0.3.2 -m "CS1: paquete publicable en el indice de pruebas"
git push origin cs1-v0.3.2
```

La etiqueta dispara el flujo. Aprobar el último paso cuando los dos primeros
estén en verde.

## 9. Comprobar lo publicado

```bash
python3 -m venv /tmp/prueba && source /tmp/prueba/bin/activate
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ fuel-price-gt
cd /tmp && fuel-price-gt build-data
pip install "fuel-price-gt[modeling]"
fuel-price-gt train --fuel regular
deactivate
```

Si eso funciona desde una carpeta vacía, la publicación sirve. El procedimiento
completo y qué hacer si falla está en [08_publishing.md](08_publishing.md).
