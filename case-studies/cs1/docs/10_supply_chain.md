# Dependencias y cadena de suministro

Cómo se mantienen al día las dependencias, qué publica el repositorio además
del paquete, y qué hay que activar en la configuración de GitHub para que nada
de esto sea decorativo. Parte de la documentación; el índice está en
[README.md](README.md).

Esto empieza a importar al publicar. Mientras el código solo corría aquí, una
dependencia vieja era un problema propio. Publicado, viaja dentro de la
distribución y llega a quien la instale.

## Actualización automática

`.github/dependabot.yml` declara tres cosas que el repositorio consume de
fuera:

| Qué | Dónde | Prefijo del commit |
|---|---|---|
| Acciones de los flujos | `/` y `/.github/actions/setup-cs1-env` | `ci` |
| Dependencias del paquete | `/case-studies/cs1` | `build` (producción), `chore` (desarrollo) |
| Imagen base del contenedor | `/case-studies/cs1` | `build` |

La segunda ruta de las acciones no es redundante: la acción compuesta propia
declara sus dependencias en su propio archivo y no se ve desde la raíz.

Las dependencias del paquete van en dos grupos porque el riesgo no es el mismo.
Una subida de las de producción viaja dentro de la distribución publicada y
llega a quien la instale; una de las de desarrollo se queda aquí y en la
integración continua.

Las acciones van en un solo grupo por el motivo contrario: son diez que se
mueven juntas, y abrir diez propuestas semanales garantiza que no se lea
ninguna.

### Qué queda fuera y por qué

Los experimentos descartados no declaran manifiesto. `florence2-vision` tenía
un `requirements.txt` con versiones fijas, y eso generaba 24 avisos de
vulnerabilidad permanentes —de `torch` y `transformers`, las dos bibliotecas
que ese mismo experimento explica por qué no quedaron— sobre algo que nadie va
a instalar. Las 24 eran el total del repositorio: el paquete publicado no
aportaba ninguna.

Lo que se quería conservar era el registro de con qué se probó, y eso vive
ahora en `experiments/README.md`. Un `requirements.txt` no es un registro: es
una declaración de dependencias vivas, y las herramientas lo tratan como tal.

Los dos ejercicios de `workshop/` tampoco se actualizan. Son entregas cerradas, sin
flujo que las verifique, y una propuesta semanal sobre ellas sería ruido. La
regla es que lo que no se comprueba no se actualiza solo: una propuesta de
cambio que nadie sabe si rompe algo acaba fusionándose por costumbre, que es
peor que una versión vieja.

## La imagen de contenedor

Sale de la misma etiqueta que el paquete, con el mismo número de versión:

```bash
docker pull ghcr.io/josuesay/fuel-price-gt:0.3.4
```

Va **después** de publicar el paquete y no en paralelo. Si la publicación se
rechaza en la aprobación, una imagen ya publicada anunciaría una versión que no
existe en el índice.

No pide aprobación propia, y la asimetría es deliberada: una versión del
registro de contenedores se puede borrar, una del índice de paquetes no. Lo
irreversible es lo que se detiene a mirar.

Los datos y los modelos no van dentro. Entran por volumen:

```bash
docker run -p 19010:8000 \
  -v "$PWD/data:/app/data" \
  -v "$PWD/models:/app/models" \
  ghcr.io/josuesay/fuel-price-gt:0.3.4
```

## Análisis de vulnerabilidades de la imagen

Dependabot no cubre la imagen. Ve dos cosas: lo que `pyproject.toml` declara y
la etiqueta de la imagen base. No ve lo que hay realmente dentro del
contenedor, que son 192 paquetes de la distribución y 39 de Python una vez
resueltas las dependencias transitivas.

Ese hueco se midió antes de decidir si hacía falta un escáner. El primer
análisis de la imagen dio 68 vulnerabilidades graves, **todas de paquetes de la
distribución y ninguna del lado de Python**. Es decir: Dependabot cubre bien lo
que le toca, y lo que quedaba fuera era justo lo que no ve.

De las 68, treinta tenían arreglo publicado. No eran un problema del escáner
sino del `Dockerfile`: la imagen base se reconstruye cada cierto tiempo y entre
reconstrucciones acumula actualizaciones de seguridad de la distribución ya
disponibles. Un `apt-get upgrade` en la construcción cerró las treinta. Las 38
restantes no tienen arreglo publicado.

### Qué se informa, y por qué no todo

El primer informe subió 299 avisos: 159 de gravedad baja, 94 media, 34 alta,
5 crítica. Ninguno accionable, porque los accionables ya se habían cerrado en
la construcción. A ese volumen la pestaña de seguridad deja de mirarse, y un
análisis que nadie mira no es un análisis.

Ahora se informa con **los mismos filtros que usa la compuerta de
publicación**: grave y con arreglo disponible. Así lo que aparece en la pestaña
de seguridad es exactamente lo que impediría publicar. Lo que la distribución
aún no ha arreglado sigue visible en el registro del trabajo, que es donde
corresponde consultarlo.

### Lo que el análisis encontró y se cerró

Con el informe ya filtrado quedaron seis avisos, todos del mismo sitio: el
`pip` que trae la imagen base. Se cerraron en dos pasos, y ninguno de los dos
consistió en silenciar nada.

Actualizar `pip` cerró los seis y destapó dos que estaban debajo, `msgpack` y
`setuptools`. Esos dos viven **dentro** de `pip`, en su árbol de dependencias
empotradas: no se pueden actualizar por separado, haría falta una versión de
`pip` que cambie lo que empotra. `ignore-unfixed` no los filtra porque el
arreglo existe para el paquete suelto, no para la copia empotrada.

La salida fue quitar `pip` de la imagen de producción. Un contenedor que ya
tiene su código instalado no necesita un instalador dentro, y tenerlo amplía lo
que se puede hacer ahí si alguien llega. Eso cerró el frente entero.

La consecuencia de estructura: la etapa de pruebas ya no puede colgar de
producción, porque allí no queda con qué instalar las herramientas de
desarrollo. Cuelga de la base, y lo que las dos comparten —la estructura de
carpetas y la raíz declarada— subió ahí.

Resultado: **cero hallazgos accionables**. Quedan 38 graves sin arreglo
publicado, que se informan y no bloquean.

### Dónde corta y dónde solo informa

| Flujo | Qué analiza | Qué hace |
|---|---|---|
| Pipeline, trabajo 7 | La imagen recién construida | Informa. El resultado va a la pestaña de seguridad |
| Publicación, trabajo 4 | La imagen candidata, antes de subirla | **Corta** si hay algo grave con arreglo disponible |

La diferencia es deliberada. La mayor parte de lo que un escáner encuentra en
una imagen son paquetes de la distribución sin arreglo publicado: cortar el
pipeline por algo que nadie puede arreglar entrena a ignorar el rojo, y a
partir de ahí el rojo deja de significar nada.

En la publicación sí corta, y solo por lo que tiene arreglo. Una imagen
publicada con una vulnerabilidad que se podía cerrar la hereda quien la
descargue. Sin `ignore-unfixed` la compuerta estaría permanentemente en rojo y
sería igual de inútil.

## Lo que hay que activar en GitHub

El archivo de configuración solo describe qué actualizar. Que se actualice
depende de ajustes del repositorio, y ninguno se activa escribiendo código.

En Settings, Advanced Security:

| Ajuste | Para qué | Sin él |
|---|---|---|
| **Dependabot version updates** | Es lo que lee `dependabot.yml` | El archivo no hace nada |
| Dependabot malware alerts | Avisa de dependencias con software malicioso | Solo se avisa de vulnerabilidades conocidas |
| Grouped security updates | Agrupa también las propuestas de seguridad | Una propuesta por vulnerabilidad |
| CodeQL analysis | Análisis de seguridad del código propio | Solo se revisa lo que viene de fuera |
| Code scanning | Recibe el resultado del análisis de la imagen | El análisis corre y su resultado no se ve en ningún sitio |

Y en el registro de contenedores, hacer pública la imagen la primera vez: nace
privada, y una imagen que nadie puede descargar no sirve de entregable. Ya
hecho; comprobado descargándola sin credenciales.

### La condición que se olvida

**Dependabot lee `dependabot.yml` solo de la rama por defecto.** Mientras el
archivo viva en una rama de trabajo, no pasa nada: ni error, ni aviso, ni
propuestas. Parece configurado y no lo está.

Es el mismo tipo de fallo silencioso que el resto del proyecto trata de evitar:
algo que aparenta funcionar sin hacerlo. La diferencia es que aquí no hay
comprobación que lo detecte, así que queda escrito.

## Qué revisar cuando llegue una propuesta

Una actualización automática no se fusiona por venir de una máquina.

1. Que la integración continua esté en verde. Cubre el análisis estático, las
   pruebas y el contenedor.
2. Si toca una dependencia de producción, que el cambio de versión no sea
   mayor. Un salto de mayor puede cambiar la interfaz.
3. Si toca la imagen base, que `make docker-smoke` siga pasando en local, y
   mirar si el análisis de la imagen mejoró o empeoró.

### El hueco que hay que conocer

En una propuesta de cambio, **el trabajo del contenedor se salta**. Eso deja sin
comprobar todo lo que solo ocurre ahí: la construcción de la imagen, el análisis
de vulnerabilidades y la subida del informe. Y el flujo de publicación no corre
en absoluto, porque solo lo dispara una etiqueta.

Consecuencia concreta: una propuesta que suba la acción de subir informes o las
del registro de contenedores **pasa en verde sin que nada las haya ejecutado**.
Son justo las que su propia comprobación no cubre.

Por eso una actualización de acciones no se da por buena al fusionarla, sino al
ver la corrida siguiente sobre `main` —que sí ejecuta el trabajo del
contenedor— y, para las del registro, en la publicación siguiente.

Está descrito en [09_ci.md](09_ci.md).
