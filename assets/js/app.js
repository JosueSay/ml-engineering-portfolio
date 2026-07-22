/**
 * app.js — Entry point loaded by every page.
 *
 * Orchestrates the shared modules: builds the shell, wires the theme and
 * language controls, initializes the collapsible sidebar and renders the
 * active translations. Page-specific content stays in each page's HTML.
 */

import { buildShell } from "./layout.js";
import { initI18n, setLang, getLang } from "./i18n.js";
import { initSidebar } from "./sidebar.js";
import { getTheme, toggleTheme } from "./theme.js";

const sunIcon = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none"
  stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
  stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/>
  <path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.5 1.5M17.5 17.5 19 19M19 5l-1.5 1.5M6.5 17.5 5 19"/></svg>`;
const moonIcon = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none"
  stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
  stroke-linejoin="round" aria-hidden="true">
  <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>`;

function renderThemeIcon(shell) {
  const slot = shell.querySelector("[data-theme-icon]");
  if (slot) slot.innerHTML = getTheme() === "dark" ? sunIcon : moonIcon;
}

function syncLangButtons(shell) {
  shell.querySelectorAll("[data-lang]").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.lang === getLang());
  });
}

async function main() {
  const { shell } = buildShell();

  // Translations (loads dictionaries, applies data-i18n across the DOM).
  await initI18n();
  syncLangButtons(shell);

  // Collapsible / drawer sidebar.
  initSidebar(shell);

  // Theme toggle.
  renderThemeIcon(shell);
  shell
    .querySelector("[data-theme-toggle]")
    .addEventListener("click", () => {
      toggleTheme();
      renderThemeIcon(shell);
    });

  // Language switch.
  shell.querySelectorAll("[data-lang]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await setLang(btn.dataset.lang);
      syncLangButtons(shell);
    });
  });
}

main();
