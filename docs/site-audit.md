# Auditoría del sitio del portafolio

Diagnóstico de los problemas visuales y de carga del sitio publicado en GitHub
Pages. Cada hallazgo incluye el culpable concreto con archivo y línea, y la
evidencia con la que se comprobó.

- Fecha: 1 de septiembre de 2026
- URL auditada: <https://josuesay.github.io/ml-engineering-portfolio/index.html>
- Método: Chrome DevTools sobre la página en producción (traza de rendimiento,
  medición del árbol de layout y de la cascada de red)

## 1. Resumen

Tres problemas distintos, con una causa común de fondo: **el sitio no existe
hasta que JavaScript termina de ejecutarse**. El HTML que se sirve está vacío
de contenido visible y de estructura; ambos se construyen en tiempo de
ejecución.

| Síntoma reportado | Culpable | Gravedad |
| --- | --- | --- |
| Espacio vacío al contraer el menú | `layout.css:110-117` oculta las etiquetas sin sacarlas del flujo | Media |
| La página "recarga feo" | Cascada de tres saltos de red antes del primer pintado | Alta |
| Salto del contenido al cargar | Los textos llegan por `fetch` después del primer pintado | Media |
| Faltan laboratorios, talleres, proyectos y casos | Las páginas solo tienen un marcador de contenido vacío | Alta |

## 2. Hallazgo 1 — El hueco del menú contraído

### Qué se ve

Al contraer la barra lateral quedan dos huecos verticales entre los iconos: uno
antes del icono de Proyectos y otro antes del de Sonic.

### Culpable

`assets/css/layout.css`, líneas 110 a 117:

```css
.app-shell.is-collapsed .sidebar__brand-text,
.app-shell.is-collapsed .sidebar__section-label,
.app-shell.is-collapsed .nav-link__label {
  opacity: 0;
  width: 0;
  pointer-events: none;
}
```

`opacity: 0` vuelve el elemento invisible pero **no lo saca del flujo**, y
`width: 0` no elimina ni el relleno lateral ni la altura. Las dos etiquetas de
sección, `Portafolio` y `Extra`, siguen ocupando su caja completa.

### Evidencia

Medición del árbol de layout con la barra contraída:

| Elemento | Texto | Alto | Opacidad |
| --- | --- | --- | --- |
| `nav-link` | Inicio | 46 px | 1 |
| `sidebar__section-label` | Portafolio | **38 px** | **0** |
| `nav-link` | Proyectos | 46 px | 1 |
| `nav-link` | Laboratorios | 46 px | 1 |
| `nav-link` | Casos de Estudio | 46 px | 1 |
| `nav-link` | Talleres | 46 px | 1 |
| `sidebar__section-label` | Extra | **38 px** | **0** |
| `nav-link` | Sonic | 46 px | 1 |

Son 76 px de espacio invisible pero ocupado. Las etiquetas conservan además
24 px de ancho por el relleno lateral de `padding: 14px 12px 6px`, dentro de una
barra de 72 px.

### Corrección propuesta

Sacar del flujo lo que se oculta. Para las etiquetas de sección basta
`display: none`. Para los textos que sí deben poder animarse, anular también
relleno, margen y alto, no solo el ancho.

## 3. Hallazgo 2 — El parpadeo al navegar

### Qué se ve

Cada vez que se pulsa una entrada del menú la pantalla queda en blanco un
instante y luego aparece todo de golpe. Se repite en cada navegación porque
cada página es un documento independiente.

### Culpable

Dos decisiones que se suman:

**Primera.** Todas las páginas ocultan su contenido en el HTML servido:

```html
<main id="content" hidden>
```

El atributo `hidden` solo se retira en `assets/js/layout.js:118`, cuando el
módulo ya se descargó y ejecutó. Hasta ese momento el documento está en blanco.

**Segunda.** Los módulos se descubren en cascada, no en paralelo. El navegador
no puede adelantar ninguna petición porque cada nivel se entera del siguiente
solo al ejecutar el anterior:

```
HTML  ->  app.js  ->  layout.js, i18n.js, sidebar.js, theme.js  ->  es.json, en.json
```

### Evidencia

Cascada de red medida en la carga real:

| Momento | Qué se pide |
| --- | --- |
| 11 ms | `branding.css`, `layout.css`, `app.js` |
| 37 ms | `layout.js`, `theme.js`, `i18n.js`, `sidebar.js` |
| 47 ms | `en.json`, `es.json` |
| 88 ms | Primer pintado |

Son tres viajes de ida y vuelta encadenados antes de que aparezca nada. La
medición se hizo con red rápida y sin limitación de CPU: con una conexión móvil
la ventana en blanco se multiplica.

### Corrección propuesta

Por orden de impacto y de esfuerzo:

- Quitar `hidden` del HTML y ocultar en su lugar solo lo que aún no está
  estilizado, o mejor, servir el contenido visible desde el principio.
- Declarar los módulos y los diccionarios con `<link rel="modulepreload">` y
  `<link rel="preload" as="fetch">` en el `head`, para que los tres niveles se
  pidan a la vez en lugar de en fila.
- Considerar escribir el armazón directamente en el HTML en lugar de
  construirlo en tiempo de ejecución. El motivo original era no duplicar el
  menú en cada página; se puede conservar generándolo en el paso de compilación
  del workflow, que ya existe y ya ensambla el sitio.

## 4. Hallazgo 3 — El contenido salta al cargar

### Qué se ve

Un desplazamiento del contenido y de los enlaces del menú poco después de que
la página aparece.

### Culpable

Los textos no están en el HTML. Cada elemento se sirve vacío y se rellena
después:

```html
<h1 data-i18n="home.title"></h1>
```

`assets/js/i18n.js:62-76` los completa con `applyTranslations()`, ya pasado el
primer pintado. Los enlaces del menú, que estaban vacíos, cambian de tamaño y
empujan al resto.

### Evidencia

La traza mide un desplazamiento acumulado de 0.0364 a los 120 ms. Los elementos
afectados que identifica son exactamente `div.content-inner` y cuatro enlaces
`a.nav-link`.

Está dentro del umbral que se considera bueno, así que no es urgente, pero es
la causa visible del salto y desaparece sola si se corrige el hallazgo 2.

## 5. Hallazgo 4 — Sin JavaScript no hay nada

Consecuencia de lo anterior que conviene anotar aparte, porque es la más grave
en un portafolio destinado a que otros lo lean.

El HTML servido no contiene ni un solo texto: ni títulos, ni descripciones, ni
navegación. Todo depende de que se ejecute el módulo. Si falla la descarga de
un archivo, si hay un error de ejecución o si el visitante llega con un agente
que no ejecuta scripts, la página queda **completamente en blanco**, no
degradada.

Tiene además un efecto colateral: para cualquier rastreador que no ejecute
JavaScript, el portafolio es un documento vacío.

## 6. Hallazgos menores

Detectados al revisar el código, sin relación con lo reportado.

### 6.1 Altura fija en unidades de ventana

`assets/css/layout.css:10` fija `grid-template-rows: 100vh`. En navegadores
móviles la barra de direcciones aparece y desaparece, y `100vh` no la tiene en
cuenta: parte del contenido queda recortada. La unidad `100dvh` corrige esto.

### 6.2 Se anima una propiedad de rejilla

`assets/css/layout.css:11` aplica una transición sobre `grid-template-columns`.
Es una propiedad de disposición, así que el navegador recalcula la geometría en
cada fotograma de la animación. Funciona, pero es de las transiciones más caras
que se pueden pedir.

### 6.3 El estado del menú no se recalcula al cambiar el tamaño

`assets/js/sidebar.js:17` decide si está en móvil una sola vez, al iniciar. Si
la ventana cruza el punto de corte de 820 px después, el estado no se revisa. La
clase `is-mobile-open` puede quedarse puesta al pasar a escritorio, donde ya no
significa nada.

### 6.4 Falta marcar la página activa para lectores de pantalla

`assets/js/layout.js:56` marca el enlace activo solo con la clase `is-active`,
que es puramente visual. Falta `aria-current="page"`, que es lo que anuncia un
lector de pantalla.

## 7. Contenido pendiente de publicar

Cuatro de las cinco páginas muestran únicamente el marcador
`Contenido en camino. Pronto habrá material aquí.`, pese a que el trabajo ya
existe en el repositorio.

| Página | Estado | Material disponible sin publicar |
| --- | --- | --- |
| Proyectos | Vacía | Nada todavía |
| Laboratorios | Vacía | Los ejercicios y tareas del curso |
| Casos de Estudio | Vacía | `case-studies/cs1`, el caso de la gasolina |
| Talleres | Vacía | `workshop/activity-01-sklearn-pipeline` y `workshop/activity-03-hyperparameter-tuning` |
| Sonic | Publicada | — |

### 7.1 Talleres

- `workshop/activity-01-sklearn-pipeline/pipeline_sklearn`: pipeline de sklearn con extracción,
  filtrado, manejo de tipos y separación del conjunto, empaquetado y con su
  cuaderno.
- `workshop/activity-03-hyperparameter-tuning`: pipeline de regresión lineal con calibración de
  hiperparámetros, empaquetado como biblioteca instalable.

### 7.2 Laboratorios

Material entregado a lo largo del curso que hoy solo vive como documentos
sueltos fuera del repositorio: investigación de comandos por plataforma,
análisis del conjunto de datos, roles en proyectos de aprendizaje automático,
ambientes e integración continua, y publicación de paquetes.

### 7.3 Casos de Estudio

El caso de precios de gasolina, con su pipeline de extracción, sus capas de
datos, su entrenamiento y su interfaz. Su plan de trabajo está en
`case-studies/cs1/docs/work-plan.md`.

## 8. Orden sugerido

1. Corregir el hueco del menú contraído. Es un cambio de tres líneas de estilo
   y resuelve lo más visible.
2. Precargar módulos y diccionarios, y dejar de servir el contenido oculto.
   Elimina el parpadeo y, de paso, el salto del contenido.
3. Publicar el material que ya existe. Es lo que más cambia la utilidad del
   sitio.
4. Los hallazgos menores, cuando se toque cada archivo.

La decisión de fondo que conviene tomar antes del punto 2 es si el armazón se
sigue construyendo en tiempo de ejecución o se genera en el paso de compilación
del workflow. La segunda opción conserva la ventaja de no duplicar el menú y
elimina la causa raíz de los tres primeros hallazgos.
