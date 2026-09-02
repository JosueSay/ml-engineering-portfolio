# Registro de entregas

Qué marca cada etiqueta y qué salió de ella. Parte de la documentación; el
índice está en [README.md](README.md).

Una etiqueta `cs1-v<version>` hace dos cosas a la vez: marca una entrega en el
historial y, si la versión coincide, dispara la publicación. Este documento es
la mitad que el historial de Git no cuenta: **qué fase cerró cada una y si llegó
a publicarse.**

## Las etiquetas

| Etiqueta | Cierra | Publicó | Qué entregó |
|---|---|---|---|
| `cs1-v0.1.0` | Fase A | no | Higiene, estructura y estándares: nomenclatura en inglés, tres niveles de configuración, credenciales fuera del repositorio, imágenes fuera del control de versiones |
| `cs1-v0.2.0` | Fase B | no | Persistencia y linaje: siete tablas encadenadas, recorte y lectura, tratamiento de faltantes con procedencia declarada |
| `cs1-v0.3.0` | — | no | Primer intento de publicación. Cortó en el paso 2: la instalación mínima no arrancaba sin el extra de modelado |
| `cs1-v0.3.1` | — | no | Cortó en el paso 2, solo en Windows: su consola trae cp1252 y no sabe escribir una tilde ni una flecha |
| `cs1-v0.3.2` | Fase D | **sí** | Paquete instalable y utilizable sin clonar el repositorio |
| `cs1-v0.3.3` | — | **sí** | Republicación con el flujo corregido, tras arreglar la ruta por defecto de los trabajos que no clonan |
| `cs1-v0.3.4` | Fase F | **sí** | Primera que publica también la imagen de contenedor, desde la misma etiqueta y con el mismo número |

Las tres que no publicaron **no se borran ni se mueven**. Una etiqueta que
apunta a un intento fallido es información: dice qué se rompió y en qué paso, y
que la comprobación previa hizo su trabajo antes de subir nada.

Las dos primeras tampoco publicaron, pero por otro motivo: cerraban una fase de
trabajo interno y no había nada que entregar fuera. Marcar una entrega y
publicarla son cosas distintas, y el flujo solo hace la segunda si además la
versión declarada coincide con la etiqueta.

## Qué numero le toca a la siguiente

El número describe **el paquete**, no la fase del proyecto. Un avance grande en
documentación o en el sitio web no sube la versión si lo que se distribuye no
cambia.

- Funcionalidad nueva compatible: menor.
- Corrección, o cambio solo en la descripción que viaja en la distribución:
  parche.
- Cambio que rompe: mayor. Aquí sería renombrar un comando, un argumento o una
  clave de configuración.

## Cómo se cierra una entrega

El procedimiento completo está en [08_publishing.md](08_publishing.md). En
resumen, y en este orden:

```bash
# 1. La version, en src/fuel_price_gt/__init__.py
# 2. Las tres comprobaciones
make gates && make publish-check && make docker-smoke
# 3. Commit, rama, y despues la etiqueta
git push origin main
git tag -a cs1-v<version> -m "CS1: <que entrega>"
git push origin cs1-v<version>
```

El orden importa: etiquetar antes de que exista el commit deja la etiqueta
apuntando al anterior, que declara la versión anterior, y la comprobación la
rechaza. Corta en segundos, pero obliga a mover la etiqueta.

## Lo que queda fuera de este registro

La fase C. No tiene etiqueta y no la tendrá hasta que llegue el histórico de
fotografías: cerrarla ahora sería marcar como entregado un análisis hecho sobre
16 imágenes, que no aguanta ninguna conclusión.
