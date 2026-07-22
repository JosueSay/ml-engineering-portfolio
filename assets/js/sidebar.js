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

export function initSidebar(shell) {
  // Restore persisted collapsed state on desktop.
  if (!isMobile() && localStorage.getItem(STORAGE_KEY) === "true") {
    shell.classList.add("is-collapsed");
  }

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

  return { toggle, closeMobile };
}
