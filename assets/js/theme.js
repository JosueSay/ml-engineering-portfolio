/**
 * theme.js — Dark/light theme handling.
 *
 * The active theme is stored on <html data-theme> and persisted in
 * localStorage. When no explicit choice exists we defer to the OS preference
 * (handled by branding.css via prefers-color-scheme).
 */

const STORAGE_KEY = "portfolio.theme";
const THEMES = ["light", "dark"];

export function getTheme() {
  const explicit = document.documentElement.getAttribute("data-theme");
  if (explicit) return explicit;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function setTheme(theme) {
  if (!THEMES.includes(theme)) return;
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem(STORAGE_KEY, theme);
}

export function toggleTheme() {
  setTheme(getTheme() === "dark" ? "light" : "dark");
  return getTheme();
}

/**
 * Apply the stored theme as early as possible to avoid a flash of the wrong
 * theme. Call this from an inline script in <head> before paint.
 */
export function initTheme() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && THEMES.includes(stored)) {
    document.documentElement.setAttribute("data-theme", stored);
  }
}
