# Commits de la fase B

Propuesta de división, en el mismo estilo que la
[fase A](fase-a-commits.md): Conventional Commits en español.

El orden va de dentro hacia fuera: primero el modelo de datos, luego lo que lo
alimenta, después lo que lo consume, y al final la infraestructura y la
documentación. Así cada commit apoya sobre el anterior.

Ejecutar todo desde la raíz del repositorio.

## 0. Comprobar el punto de partida

```bash
cd case-studies/cs1 && make gates && cd ../..
git status --short
git reset   # solo si quedara algo preparado de antes
```

## 1. Acciones al día

Quedó pendiente del cierre de la fase A.

```bash
git add .github/
git commit -m "ci: actualizar las acciones a versiones con Node 24

El aviso de deprecacion senalaba checkout y setup-python, que seguian en Node
20. Se aprovecha para poner al dia las diez acciones del repositorio.

Los dos cambios incompatibles declarados no afectan a este flujo: el de
download-artifact v5 aplica a descargas por identificador y aqui se descarga
por nombre, y el de v8 hace que un hash que no coincida falle en vez de avisar,
que es el comportamiento deseable."
```

## 2. El modelo de datos

```bash
git add case-studies/cs1/src/fuel_price_gt/db/ \
        case-studies/cs1/scripts/20_db_init.py \
        case-studies/cs1/tests/unit/test_lineage.py \
        case-studies/cs1/pyproject.toml
git commit -m "feat(cs1): modelar la cadena de custodia de cada precio

Siete tablas encadenadas por claves foraneas, de la fotografia al modelo
entrenado. El linaje no es un campo que alguien rellena: es la forma de los
datos, y por eso no se puede desincronizar.

Ante una prediccion mala hay que poder saber si fallo el modelo o si fallo la
lectura de la imagen. Son dos problemas distintos y desde fuera se ven igual.

Detalles que evitan roturas silenciosas:

- El motor embebido no aplica las claves foraneas salvo que se le pida en cada
  conexion. Sin eso, una lectura podria apuntar a una imagen ya borrada.
- La consulta de linaje declara sus rupturas en vez de devolver huecos: una
  fila sintetica no tiene fotografia detras, y esa es una respuesta legitima.
- lineage_coverage mide que porcentaje del conjunto llega hasta una foto. Si da
  cero, el modelo se entrena solo sobre datos generados, y conviene que eso sea
  un numero y no una advertencia en prosa."
```

## 3. El recorte como evidencia

```bash
git add case-studies/cs1/src/fuel_price_gt/extraction/display_detector.py \
        case-studies/cs1/src/fuel_price_gt/extraction/extractor.py \
        case-studies/cs1/src/fuel_price_gt/extraction/heic_loader.py \
        case-studies/cs1/src/fuel_price_gt/extraction/preprocess.py
git commit -m "feat(cs1): guardar el recorte de cada lectura como evidencia

Cada panel leido deja su porcion de pixeles en data/interim, con su caja
delimitadora y el metodo con que se localizo. No es solo ahorro de computo:
ante una lectura sospechosa se puede abrir exactamente lo que se leyo.

Se nombra por la huella de la imagen y no por su nombre de archivo, porque los
nombres se repiten entre lotes y las huellas no.

Se anade la localizacion del visor por su aspecto. Con la calibracion por
encuadre fijo, diez de dieciseis recortes apuntaban a la carcasa o al bisel, y
ningun reconocedor puede leer lo que no esta. Donde no hay visor ya no se
intenta leer: un reconocedor sobre carcasa lisa devuelve numeros inventados que
entran en la serie sin que nada los detecte."
```

## 4. Medir el reconocimiento

```bash
git add case-studies/cs1/src/fuel_price_gt/extraction/digit_ocr.py \
        case-studies/cs1/scripts/tools/ \
        case-studies/cs1/tests/fixtures/ocr_ground_truth.json
git commit -m "feat(cs1): medir el reconocimiento y corregir la inclinacion del display

Se anade un conjunto de referencia con los precios legibles anotados a mano y
los recortes vacios como casos negativos, y una herramienta que compara motores
sobre los mismos datos. Sin eso, 'mejorar el reconocimiento' no era una
afirmacion comprobable.

La herramienta separa dos fallos que se confundian en el valor final: leer mal
un digito, que exige otro reconocedor, y colocar mal el separador decimal, que
se resuelve por posicion. Y mide la tasa de invencion sobre los recortes sin
visor: un motor que puntua alto inventando es peor que uno que se calla.

Dos hallazgos con su arreglo:

- Los digitos son italicos por diseno, como los de un reloj digital. No es
  perspectiva de la fotografia; rectificarla no cambiaba nada. Las plantillas de
  comparacion son de trazos rectos, y por eso se confundian justo los digitos
  que mas se parecen al inclinarse. Enderezar antes de comparar llevo la lectura
  de cero digitos correctos a cuatro de cinco en el mejor caso.
- El separador decimal se perdia: se llego a leer 4609 donde decia 40.09. Un
  precio en quetzales por galon siempre tiene dos decimales, asi que el punto se
  recoloca por posicion cuando el numero de digitos es el esperado, y solo
  entonces."
```

## 5. Recuperar lo que no se pudo leer

```bash
git add case-studies/cs1/src/fuel_price_gt/data/recovery.py \
        case-studies/cs1/tests/unit/test_recovery.py
git commit -m "feat(cs1): recuperar precios ilegibles y marcar como se obtuvo cada valor

Con fotografias tomadas en la calle siempre habra lecturas que no salgan, y ese
es el estado normal. Lo que decide la calidad del caso no es leer el cien por
cien sino que se hace con lo que falta.

Dos vias, muy distintas entre si:

- Reconstruccion aritmetica desde el total pagado y el volumen. No se inventa
  nada: el dato estaba en la foto por otra via.
- Relleno estadistico cuando no hay redundancia que explotar. Aqui si se pone un
  numero donde no habia medida, y por eso la marca importa.

Tres comprobaciones que evitan errores que nadie veria:

- Si el dispensador marca litros y se divide como si fueran galones, el precio
  sale casi cuatro veces menor y dentro de un rango plausible.
- Una division valida puede dar un precio absurdo si el total se leyo mal; sin
  la cota, ese numero entra en la serie como bueno.
- Sin ni un valor medido no hay de donde estimar, y no se estima.

Solo se marca lo que se relleno: una fila medida nunca queda marcada como
estimada, porque si no la distincion dejaria de servir."
```

## 6. Las capas en la base

```bash
git add case-studies/cs1/src/fuel_price_gt/data/pipeline.py \
        case-studies/cs1/src/fuel_price_gt/data/features.py \
        case-studies/cs1/src/fuel_price_gt/modeling/training.py \
        case-studies/cs1/scripts/12_extract_prices.py
git commit -m "refactor(cs1): llevar las capas de datos a la base y evitar el reprocesado

La base pasa a ser la fuente de verdad de Bronze, Silver y Gold; los archivos
tabulares quedan como exportacion. Un CSV no puede responder de que fotografia
salio un precio, que es la pregunta que sostiene el caso.

Silver lee de la base en vez de reprocesar las fotografias: la extraccion es la
etapa cara y repetirla para reconstruir una tabla derivada no aporta nada.

La extraccion consulta antes de leer si esa imagen ya se proceso con el mismo
codigo y la misma configuracion. La comprobacion va contra las tres cosas a la
vez: basta que cambie un umbral para que la lectura pueda dar otro resultado.

Los modelos entrenados quedan registrados con la huella del conjunto que los
produjo, en la base ademas del manifiesto: responden preguntas distintas.

Dos incoherencias corregidas, del tipo que no rompe nada visiblemente y
envenena las conclusiones:

- La procedencia se perdia al construir las variables, porque build_features
  devolvia una lista fija de columnas y el metodo no estaba en ella.
- Las filas generadas decian venir de una lectura. Nadie las habia leido."
```

## 7. Contenedor de base de datos

```bash
git add case-studies/cs1/compose.yaml \
        case-studies/cs1/Dockerfile \
        case-studies/cs1/Makefile \
        case-studies/cs1/.gitignore
git commit -m "feat(cs1): anadir el contenedor de base de datos y su explorador

La base va en volumen propio, separada de las fotografias: asi se puede
respaldar o inspeccionar sin arrastrar los binarios, que pesan mucho mas.

El motor embebido es un archivo, asi que el servicio no es un motor sino un
explorador web para recorrer el linaje sin instalar cliente alguno.

El manifiesto de modelos queda excluido del control de versiones, con el motivo
escrito: deberia versionarse por ser texto, pero la serie sintetica se genera
hasta la fecha actual y su huella cambia cada dia, lo que ensuciaria el
historial sin que nada real hubiera cambiado."
```

## 8. Documentación

```bash
git add case-studies/cs1/docs/
git commit -m "docs(cs1): documentar el modelo de datos y el tratamiento de faltantes

Recoge la pregunta que justifica el modelo relacional, las siete tablas con el
porque de cada campo, los seis metodos de procedencia y donde puede aparecer
cada uno, las dos vias de recuperacion con sus comprobaciones, como consultar
el linaje y la politica de cache.

Se anaden al plan de trabajo dos hallazgos:

- La extraccion lee poco, y eso es parte del problema a resolver, no una averia
  que haya que eliminar antes de seguir.
- El conjunto sintetico no es reproducible porque se genera hasta la fecha
  actual, y la reproducibilidad es un requisito del caso."
```

## Antes de empujar

```bash
cd case-studies/cs1 && make gates && cd ../..
git log --oneline -8
git status --short
```

`git status` debe quedar limpio salvo lo ignorado: `.env`, `.venv/`, `data/`,
`keys/`, `models/` y los recortes.

## Etiqueta

```bash
git tag -a cs1-v0.2.0 -m "CS1: persistencia, recorte y linaje"
git push origin fuel-case-study --follow-tags
```

Es una versión menor y no un parche porque añade funcionalidad compatible: el
modelo de datos, la recuperación de faltantes y el linaje consultable.
