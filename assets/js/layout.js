/**
 * layout.js — Builds the shared application shell (topbar + collapsible
 * sidebar) and slots the page-specific <main id="content"> into it.
 *
 * Keeping the shell here means each page only ships its unique content, so no
 * HTML file grows large or duplicates navigation/theme markup.
 */

import { SUPPORTED } from "./i18n.js";
import { shouldStartCollapsed } from "./sidebar.js";

/* Minimal inline icon set (stroke = currentColor). */
const icons = {
  home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>',
  projects: '<path d="M3 7h7l2 2h9v11H3z"/>',
  labs: '<path d="M9 3v7L4 19a2 2 0 0 0 2 3h12a2 2 0 0 0 2-3l-5-9V3"/><path d="M8 3h8"/>',
  cases: '<path d="M4 5h16v14H4z"/><path d="M4 9h16"/><path d="M8 5v4"/>',
  workshops: '<path d="M14 7l6 6-3 3-6-6"/><path d="M3 21l6-6"/><path d="M11 5l3-3 4 4-3 3"/>',
  sonic: '<circle cx="12" cy="12" r="9"/><path d="M8 13c2 2 6 2 8 0"/><circle cx="9" cy="10" r="1"/><circle cx="15" cy="10" r="1"/>',
  menu: '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.5 1.5M17.5 17.5 19 19M19 5l-1.5 1.5M6.5 17.5 5 19"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
};

function svg(name, cls) {
  return `<svg class="${cls}" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
    stroke-linejoin="round" aria-hidden="true">${icons[name] || ""}</svg>`;
}

/**
 * Navigation model. `href` is relative to the site root; layout.js prefixes it
 * with the correct depth so links work from both `/` and `/pages/`.
 */
const NAV = [
  { id: "home", href: "index.html", icon: "home", i18n: "nav.home" },
  { section: "nav.section.work" },
  { id: "projects", href: "pages/projects.html", icon: "projects", i18n: "nav.projects" },
  { id: "labs", href: "pages/labs.html", icon: "labs", i18n: "nav.labs" },
  { id: "case-studies", href: "pages/case-studies.html", icon: "cases", i18n: "nav.caseStudies" },
  { id: "workshops", href: "pages/workshops.html", icon: "workshops", i18n: "nav.workshops" },
  { section: "nav.section.extra" },
  { id: "sonic", href: "pages/sonic.html", icon: "sonic", i18n: "nav.sonic" },
];

function root() {
  return window.location.pathname.includes("/pages/") ? "../" : "./";
}

function navMarkup(activeId) {
  const prefix = root();
  return NAV.map((item) => {
    if (item.section) {
      return `<div class="sidebar__section-label" data-i18n="${item.section}"></div>`;
    }
    const active = item.id === activeId ? " is-active" : "";
    // is-active es solo color; aria-current es lo que anuncia un lector de
    // pantalla al llegar al enlace de la pagina en la que ya se esta.
    const current = item.id === activeId ? ' aria-current="page"' : "";
    return `
      <a class="nav-link${active}" href="${prefix}${item.href}"${current}
         data-i18n-attr="title:${item.i18n}">
        <span class="nav-link__icon">${svg(item.icon, "")}</span>
        <span class="nav-link__label" data-i18n="${item.i18n}"></span>
      </a>`;
  }).join("");
}

function langSwitchMarkup() {
  return SUPPORTED.map(
    (lang) =>
      `<button class="lang-switch__btn" data-lang="${lang}">${lang.toUpperCase()}</button>`
  ).join("");
}

/**
 * Build the shell around the existing #content element.
 * @returns {{shell: HTMLElement}}
 */
export function buildShell() {
  const prefix = root();
  const content = document.getElementById("content");
  const activeId = document.body.getAttribute("data-page") || "home";

  const shell = document.createElement("div");
  // El estado plegado se decide aqui, antes de que el armazon entre en el
  // documento. Aplicarlo despues lo pintaba desplegado y luego lo plegaba a la
  // vista: al navegar se veia expandir y contraer en cada pagina.
  shell.className = shouldStartCollapsed() ? "app-shell is-collapsed" : "app-shell";
  shell.innerHTML = `
    <aside class="sidebar">
      <a class="sidebar__brand" href="${prefix}index.html">
        <img class="sidebar__logo" src="${prefix}assets/favicon.svg" alt="" />
        <span class="sidebar__brand-text" data-i18n="brand.name"></span>
      </a>
      <nav class="sidebar__nav">${navMarkup(activeId)}</nav>
    </aside>

    <div class="app-main">
      <header class="topbar">
        <button class="icon-btn" data-sidebar-toggle
                data-i18n-attr="aria-label:action.toggleSidebar">
          ${svg("menu", "")}
        </button>
        <div class="topbar__spacer"></div>
        <div class="lang-switch" role="group"
             data-i18n-attr="aria-label:action.language">
          ${langSwitchMarkup()}
        </div>
        <button class="icon-btn" data-theme-toggle
                data-i18n-attr="aria-label:action.toggleTheme">
          <span data-theme-icon></span>
        </button>
      </header>
      <div class="content-host"></div>
    </div>

    <div class="sidebar__backdrop"></div>
  `;

  // El contenido se sirve visible y con sus textos escritos: aqui solo se
  // reubica dentro del armazon, en la misma caja que ya ocupaba.
  const host = shell.querySelector(".content-host");
  host.replaceWith(content);
  content.classList.add("content");
  document.body.prepend(shell);

  return { shell };
}
