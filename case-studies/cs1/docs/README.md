# Documentación de CS1

Caso de estudio de extracción y pronóstico de precios de combustible en
Guatemala. La visión general está en el [README del caso](../README.md); aquí
está el detalle.

## Índice

| Documento | Para qué |
|---|---|
| [01_setup.md](01_setup.md) | Dejar el proyecto funcionando en una máquina nueva |
| [02_environment.md](02_environment.md) | Referencia de variables de entorno y credenciales |
| [03_commands.md](03_commands.md) | Referencia de comandos y scripts |
| [04_structure.md](04_structure.md) | Qué hay en cada carpeta y por qué |
| [07_image_source.md](07_image_source.md) | Conectar Google Drive paso a paso |
| [06_data_model.md](06_data_model.md) | Modelo de datos, linaje y tratamiento de faltantes |
| [05_operations.md](05_operations.md) | Tareas que requieren una persona: credenciales, cuentas y publicación |
| [work-plan.md](work-plan.md) | Diagnóstico, decisiones tomadas y pendientes |

Además, [keys/README.md](../keys/README.md) documenta qué credencial hace falta
para qué, cómo se obtiene y con qué permisos mínimos; y
[experiments/README.md](../experiments/README.md) recoge lo que se exploró y no
quedó, con el motivo del descarte.

## Por dónde empezar

- **Primera vez en el proyecto**: [01_setup.md](01_setup.md).
- **Buscando un comando**: [03_commands.md](03_commands.md), o `make help`.
- **Añadiendo un valor de configuración**: [02_environment.md](02_environment.md)
  explica los tres niveles y cómo decidir en cuál va.
- **Entendiendo el estado del caso**: [work-plan.md](work-plan.md).

## Las tres reglas que explican casi todo

Cualquier decisión de estructura de este proyecto sale de una de estas tres.

**Ninguna imagen entra al control de versiones.** El repositorio guarda código
y documentación; las fotografías viven en el almacenamiento externo y se
descargan. De ahí que `data/` esté ignorada, que la imagen de contenedor monte
volúmenes en vez de copiar, y que la integración continua tenga que decidir si
hay fuente de datos antes de ejecutar las etapas que dependen de ellas.

**`.env` nunca contiene el valor de una credencial, solo la ruta al archivo que
la guarda.** Las variables sensibles terminan en `_FILE` y apuntan dentro de
`keys/`. De ahí que exista esa carpeta, que se excluya entera y no por patrón
de nombre, y que la integración continua materialice los secretos en ella antes
de ejecutar nada.

**La lógica vive en `scripts/` y en el paquete; el `Makefile` es solo el
atajo.** De ahí que todo comando pueda correrse sin `make`, que la integración
continua no dependa de él, y que en el `Makefile` solo se declare lo que
existe.

## Un dato que no se puede rastrear no sirve

El eje del caso no es el modelo sino la trazabilidad. Cada precio que llega al
conjunto de modelado tiene que poder seguirse hacia atrás hasta el recorte y la
fotografía de los que salió, con qué versión del código y con qué
configuración.

Sin eso, ante una predicción mala no se puede saber si falló el modelo o si
falló la lectura de la imagen, que son dos problemas distintos con dos
soluciones distintas.
