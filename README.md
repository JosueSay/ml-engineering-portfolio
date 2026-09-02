# ml-engineering-portfolio

Sitio estatico del portafolio de Ingenieria en Machine Learning, publicado con
GitHub Pages. Incluye tema claro/oscuro, multidioma (espanol/ingles), sidebar
contraible y una escena de pixel-art de Sonic como pagina extra.

## Caracteristicas

- **Multipagina sin duplicacion**: el shell (topbar + sidebar) se inyecta en
  tiempo de ejecucion, asi cada HTML solo contiene su contenido unico.
- **El contenido no depende de JavaScript**: los textos se sirven escritos en el
  HTML y el modulo los reescribe. Si el modulo falla o el visitante no ejecuta
  scripts, la pagina queda sin navegacion pero legible, no en blanco. Es tambien
  lo que ve un rastreador que no ejecuta JavaScript.
- **Sin salto al cargar**: los modulos y los diccionarios se declaran en el
  `head` con `modulepreload` y `preload`, asi se piden todos a la vez en vez de
  descubrirse en cascada, un nivel por viaje de red.
- **Tema claro/oscuro**: persistente en `localStorage`, respeta la preferencia
  del sistema y se aplica antes del primer render (sin parpadeo).
- **i18n (es/en)**: diccionarios JSON en `assets/i18n/`, siguiendo el estandar
  del skill `i18n`. Los textos se declaran con `data-i18n`.
- **Sidebar contraible**: modo colapsado (solo iconos) en escritorio y modo
  drawer en pantallas pequenas.
- **CI/CD**: GitHub Actions compila el SCSS y despliega a GitHub Pages.

## Estructura

```
.
├── index.html                  # Landing con accesos a las secciones
├── pages/
│   ├── projects.html           # Proyectos (sin material todavia)
│   ├── labs.html               # Laboratorios (sin material todavia)
│   ├── case-studies.html       # Casos de Estudio
│   ├── cs1-fuel-prices.html    # Caso 01: precios de combustible
│   ├── workshops.html          # Talleres
│   └── sonic.html              # Escena de pixel-art de Sonic
├── assets/
│   ├── css/
│   │   ├── branding.css        # Tokens de diseno y temas
│   │   └── layout.css          # Shell: sidebar, topbar, contenido
│   ├── scss/
│   │   └── sonic.scss          # Fuente de la animacion (se compila)
│   ├── js/
│   │   ├── app.js              # Punto de entrada
│   │   ├── layout.js           # Construye el shell y la navegacion
│   │   ├── i18n.js             # Carga de diccionarios y traduccion
│   │   ├── theme.js            # Tema claro/oscuro
│   │   └── sidebar.js          # Comportamiento del sidebar
│   ├── i18n/
│   │   ├── es.json             # Diccionario espanol
│   │   └── en.json             # Diccionario ingles
│   └── favicon.svg             # Icono de la pestana / logo
└── .github/workflows/deploy.yml
```

## Desarrollo local

Requisitos: Node.js 18+ y Python 3 (para el servidor estatico).

```bash
npm install          # instala el compilador de SCSS (sass)
npm run build        # compila assets/scss/sonic.scss -> assets/css/sonic.css
npm run serve        # sirve el sitio en http://localhost:8080
```

Durante el desarrollo del SCSS se puede usar `npm run watch` para recompilar
al guardar. El archivo `assets/css/sonic.css` es generado y esta en
`.gitignore`.

## Agregar un nuevo texto (i18n)

1. Agregar la clave y su valor en `assets/i18n/es.json` y `assets/i18n/en.json`.
   Las dos lenguas tienen que declarar exactamente las mismas claves.
2. Referenciarla en el HTML con `data-i18n="mi.clave"` (o
   `data-i18n-attr="title:mi.clave"` para atributos).
3. **Escribir el texto en espanol dentro del elemento**, no dejarlo vacio:

   ```html
   <h1 data-i18n="mi.clave">El texto en espanol</h1>
   ```

   El modulo lo reescribe con el mismo valor, asi que no cambia nada de tamano
   al cargar. Dejarlo vacio devuelve el salto de contenido y la pagina en blanco
   sin JavaScript.

## Agregar una nueva pagina

1. Copiar una pagina de `pages/` como plantilla. Trae ya las precargas de
   modulos y diccionarios, y el `<main id="content">` sin `hidden`.
2. Ajustar `data-page`, el `<title>` y las claves `data-i18n` del contenido.
3. Registrar la entrada en el arreglo `NAV` de `assets/js/layout.js`, salvo que
   sea una pagina de detalle: esas conservan el `data-page` de su seccion para
   que la navegacion siga marcando la entrada correcta.

## Despliegue

Cada push a `main` dispara el workflow `deploy.yml`, que compila el SCSS,
ensambla el sitio en `_site/` y lo publica en GitHub Pages. Para habilitarlo,
en el repositorio: **Settings -> Pages -> Build and deployment -> Source:
GitHub Actions**.

## Que hay publicado y que falta

| Pagina | Estado |
|---|---|
| Inicio | Publicada |
| Casos de Estudio | Publicada. Un caso: precios de combustible en Guatemala |
| Talleres | Publicada. Dos actividades, con enlace a su codigo |
| Sonic | Publicada |
| Laboratorios | Sin material. Lo entregado en el curso vive fuera del repositorio |
| Proyectos | Sin material |

Las dos ultimas no son un pendiente tecnico sino de contenido: no hay nada en el
repositorio que publicar. Cuando lo haya, se sigue el patron de Talleres, que es
el mas simple: una tarjeta por entrada, enlazada a su carpeta.

## Decisiones que conviene no deshacer sin querer

- **La animacion de la barra lateral es cara y se acepta a conciencia.** Anima
  `grid-template-columns`, que obliga a recalcular la geometria en cada
  fotograma. Es la unica animacion del sitio y solo ocurre al pulsarla. La
  alternativa barata seria moverla con `transform`, pero eso dejaria el hueco de
  la barra desplegada sin reflujo del contenido. Si alguna vez pesa, lo que hay
  que quitar es la animacion, no cambiarla por otra que mienta sobre la
  disposicion.
- **Lo que se oculta al contraer la barra sale del flujo.** Las etiquetas de
  seccion usan `display: none`, no `opacity: 0`: no tienen icono que dejar en su
  sitio, y ocultarlas sin sacarlas dejaba dos huecos de 38 px entre los iconos.
- **La barra nace plegada si asi quedo guardada, no se pliega despues.**
  `layout.js` consulta el estado antes de meter el armazon en el documento.
  Aplicarlo despues lo pintaba desplegado y lo plegaba a la vista, con su
  animacion, en cada navegacion. Si se mueve esa consulta detras del montaje,
  vuelve el efecto.
- **El contenido, antes de que exista el armazon, ya ocupa su caja final.**
  `layout.js` es un modulo y por tanto diferido: el navegador pinta antes de
  ejecutarlo. Si lo que se pinta en ese momento no coincide con la posicion
  definitiva, el contenido salta al montarse el armazon. Las reglas de
  `#content:not(.content)` reproducen esa caja a proposito; cambiar el ancho de
  la barra o el alto de la topbar obliga a revisarlas.
- **La rejilla de tarjetas usa `auto-fit`, no `auto-fill`.** Con `auto-fill` el
  navegador crea tantas columnas como quepan y deja vacias las que sobran, asi
  que dos tarjetas en un area ancha se quedan estrechas con el hueco al lado.
- **`100dvh`, no `100vh`.** En movil la barra de direcciones aparece y
  desaparece, y `vh` no la cuenta.
