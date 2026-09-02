/**
 * sidebar.js — Collapsible sidebar behaviour.
 *
 * Desktop: toggles a persistent collapsed state (icons only).
 * Mobile (<=820px): toggles an overlay drawer instead.
 */

const STORAGE_KEY = "portfolio.sidebar.collapsed";
const MOBILE_QUERY = "(max-width: 820px)";

function isMobile() {
  return window.matchMedia(MOBILE_QUERY).matches;
}

/**
 * ¿Debe nacer plegada la barra?
 *
 * Lo consulta layout.js al crear el armazón, antes de meterlo en el documento.
 * Restaurar el estado después de montarlo hacía que la barra se pintara
 * desplegada y se plegara a la vista, con su animación: al navegar entre
 * páginas se veía expandir y contraer en vez de quedarse como estaba.
 */
export function shouldStartCollapsed() {
  return !isMobile() && localStorage.getItem(STORAGE_KEY) === "true";
}

export function initSidebar(shell) {

  const toggle = () => {
    if (isMobile()) {
      shell.classList.toggle("is-mobile-open");
      return;
    }
    const collapsed = shell.classList.toggle("is-collapsed");
    localStorage.setItem(STORAGE_KEY, String(collapsed));
  };

  const closeMobile = () => shell.classList.remove("is-mobile-open");

  shell.querySelectorAll("[data-sidebar-toggle]").forEach((btn) => {
    btn.addEventListener("click", toggle);
  });

  // Close the mobile drawer when tapping the backdrop or a nav link.
  const backdrop = shell.querySelector(".sidebar__backdrop");
  if (backdrop) backdrop.addEventListener("click", closeMobile);
  shell.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      if (isMobile()) closeMobile();
    });
  });

  // El punto de corte se puede cruzar después de cargar, girando el dispositivo
  // o redimensionando. Sin esto, `is-mobile-open` se quedaba puesta al pasar a
  // escritorio, donde ya no significa nada, y el estado plegado guardado no se
  // recuperaba al volver.
  window.matchMedia(MOBILE_QUERY).addEventListener("change", (e) => {
    if (e.matches) {
      shell.classList.remove("is-collapsed");
    } else {
      closeMobile();
      shell.classList.toggle("is-collapsed", shouldStartCollapsed());
    }
  });

  return { toggle, closeMobile };
}
