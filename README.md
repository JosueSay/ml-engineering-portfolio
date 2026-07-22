# ml-engineering-portfolio

Sitio estatico del portafolio de Ingenieria en Machine Learning, publicado con
GitHub Pages. Incluye tema claro/oscuro, multidioma (espanol/ingles), sidebar
contraible y una escena de pixel-art de Sonic como pagina extra.

## Caracteristicas

- **Multipagina sin duplicacion**: el shell (topbar + sidebar) se inyecta en
  tiempo de ejecucion, asi cada HTML solo contiene su contenido unico.
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
│   ├── projects.html           # Proyectos (vacia, solo titulo)
│   ├── labs.html               # Laboratorios
│   ├── case-studies.html       # Casos de Estudio
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
2. Referenciarla en el HTML con `data-i18n="mi.clave"` (o
   `data-i18n-attr="title:mi.clave"` para atributos).

## Agregar una nueva pagina

1. Copiar una pagina de `pages/` como plantilla.
2. Ajustar `data-page`, el `<title>` y las claves `data-i18n` del contenido.
3. Registrar la entrada en el arreglo `NAV` de `assets/js/layout.js`.

## Despliegue

Cada push a `main` dispara el workflow `deploy.yml`, que compila el SCSS,
ensambla el sitio en `_site/` y lo publica en GitHub Pages. Para habilitarlo,
en el repositorio: **Settings -> Pages -> Build and deployment -> Source:
GitHub Actions**.
