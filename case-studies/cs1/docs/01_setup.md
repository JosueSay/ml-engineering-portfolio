# Puesta en marcha

Cómo dejar el caso de estudio funcionando en una máquina nueva. Parte de la
documentación; el índice está en [README.md](README.md).

## Requisitos

- Python 3.11 o superior. Es un requisito real, no una recomendación: el código
  usa construcciones que no existen antes de esa versión.
- Git.
- Docker, solo si se va a levantar el stack de contenedores.

Opcional: el motor externo de reconocimiento de texto. Si está instalado se usa
como segunda opinión al leer los dígitos; si no, se trabaja solo con el lector
de siete segmentos, que es el motor principal.

## Todos los comandos van desde `case-studies/cs1/`

No desde la raíz del repositorio. Si hace falta ejecutar desde otro sitio, se
declara la raíz con `FUEL_PRICE_GT_ROOT`.

## Pasos

### 1. Comprobar la máquina

```bash
make verify
```

Va primero porque el fallo más común no es un error de código sino un
intérprete equivocado: `python3` puede apuntar a una versión del sistema
anterior a la mínima, y entonces las pruebas fallan al importar con un mensaje
que no dice nada sobre la causa real. El comando lo detecta y señala dónde hay
un intérprete válido.

También informa de dependencias ausentes, de si falta `.env` y de si la
estructura de datos está completa. Distingue entre lo que impide ejecutar y lo
que solo conviene tener.

### 2. Entorno virtual y dependencias

```bash
make venv
make install-dev
```

Si `python3` no cumple el mínimo, hay que crear el entorno con el intérprete
correcto:

```bash
python3.12 -m venv .venv
make install-dev
```

El `Makefile` detecta el intérprete del entorno virtual automáticamente, en
Windows y en el resto de sistemas.

### 3. Entorno local

```bash
make env-init
```

Copia `.env.example` a `.env`. La plantilla es la fuente de verdad de qué
variables existen y sí está versionada; `.env` no.

Los valores por defecto sirven para trabajar en local sin tocar nada. La
referencia completa está en [02_environment.md](02_environment.md).

### 4. Credenciales

```bash
make keys-status
```

Dice qué falta sin crear ni imprimir nada. **Ninguna credencial es
obligatoria**: lo que falte hace que esa parte del sistema use su alternativa
local en vez de fallar.

Qué archivo va en `keys/`, cómo se obtiene y con qué permisos mínimos:
[keys/README.md](../keys/README.md).

### 5. Comprobar que todo está bien

```bash
make gates
```

Linter, pruebas, y tres comprobaciones que ninguna de las dos hace: que no se
haya versionado una credencial, que no se haya versionado una imagen, y que
`.env` siga sincronizado con su plantilla.

## Datos

Un clon nuevo tiene `data/raw` vacía, y eso es lo normal: las fotografías no se
versionan. Hasta poblarla, las etapas del pipeline no tienen sobre qué
trabajar.

Mientras tanto sí funcionan la verificación, las puertas de calidad, la
construcción de la imagen y la prueba de humo de la API, porque ninguna de esas
depende de los datos.

## Ejecutar el pipeline

```bash
make pipeline
```

O etapa por etapa, que es lo habitual mientras se trabaja:

```bash
make extract     # Bronze
make transform   # Silver y Gold
make train       # entrenamiento
make evaluate    # compuerta de calidad
make recommend   # inferencia
```

La referencia completa de comandos y sus parámetros está en
[03_commands.md](03_commands.md).

## Con contenedores

```bash
make up
make ps
make logs
make down
```

Los puertos salen del rango reservado del proyecto, 19000 a 19099, para no
chocar con otras aplicaciones de la máquina. Se cambian desde `.env` sin tocar
la composición.

## Problemas frecuentes

**`ImportError` al importar, o las pruebas fallan al recolectar**

El intérprete es anterior a 3.11. `make verify` lo confirma y señala uno
válido.

**`FileNotFoundError` buscando `config/config.yaml`**

Se está ejecutando desde el directorio equivocado, o el paquete está instalado
de forma no editable fuera de su árbol. Se resuelve declarando
`FUEL_PRICE_GT_ROOT`.

**El pipeline no encuentra fotografías**

`data/raw` está vacía. Es el estado normal de un clon nuevo.

**`make gates` falla en las pruebas pero el código parece bien**

Casi siempre es el entorno, no el código. Correr `make verify` antes de buscar
el problema en otro sitio.
