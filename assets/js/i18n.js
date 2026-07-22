/**
 * i18n.js — Lightweight internationalization for the static portfolio.
 *
 * Follows the project i18n standard: translations live in JSON dictionaries
 * (assets/i18n/<lang>.json), keyed by a stable `code`. UI elements declare the
 * key they consume through a `data-i18n` attribute; this module resolves the
 * active language, applies it to the DOM and persists the choice.
 *
 * Resolution order for a key: active language -> fallback (en) -> raw key.
 */

const FALLBACK_LANG = "en";
const SUPPORTED = ["es", "en"];
const STORAGE_KEY = "portfolio.lang";

const state = {
  lang: FALLBACK_LANG,
  dictionaries: {}, // { es: {...}, en: {...} }
  root: "./",
  listeners: new Set(),
};

/** Resolve the relative prefix to the site root (handles /pages/ depth). */
function detectRoot() {
  return window.location.pathname.includes("/pages/") ? "../" : "./";
}

/** Pick an initial language: stored choice -> browser -> fallback. */
function resolveInitialLang() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && SUPPORTED.includes(stored)) return stored;
  const browser = (navigator.language || FALLBACK_LANG).slice(0, 2);
  return SUPPORTED.includes(browser) ? browser : FALLBACK_LANG;
}

async function loadDictionary(lang) {
  if (state.dictionaries[lang]) return state.dictionaries[lang];
  const res = await fetch(`${state.root}assets/i18n/${lang}.json`);
  if (!res.ok) throw new Error(`Missing dictionary for "${lang}"`);
  const dict = await res.json();
  state.dictionaries[lang] = dict;
  return dict;
}

/** Translate a key using the active language, with fallback chain. */
export function t(key) {
  const active = state.dictionaries[state.lang] || {};
  const fallback = state.dictionaries[FALLBACK_LANG] || {};
  return active[key] ?? fallback[key] ?? key;
}

export function getLang() {
  return state.lang;
}

export function onLangChange(fn) {
  state.listeners.add(fn);
  return () => state.listeners.delete(fn);
}

/** Apply the current dictionary to every element that declares a key. */
export function applyTranslations(scope = document) {
  scope.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  scope.querySelectorAll("[data-i18n-attr]").forEach((el) => {
    // Format: "attr:key,attr:key" e.g. "aria-label:nav.home,title:nav.home"
    el.getAttribute("data-i18n-attr")
      .split(",")
      .forEach((pair) => {
        const [attr, key] = pair.split(":").map((s) => s.trim());
        if (attr && key) el.setAttribute(attr, t(key));
      });
  });
  document.documentElement.lang = state.lang;
}

/** Switch language: load dictionary if needed, persist, re-render, notify. */
export async function setLang(lang) {
  if (!SUPPORTED.includes(lang)) return;
  await loadDictionary(lang);
  state.lang = lang;
  localStorage.setItem(STORAGE_KEY, lang);
  applyTranslations();
  state.listeners.forEach((fn) => fn(lang));
}

/** Bootstrap: always load the fallback plus the active language. */
export async function initI18n() {
  state.root = detectRoot();
  state.lang = resolveInitialLang();
  await Promise.all([
    loadDictionary(FALLBACK_LANG),
    loadDictionary(state.lang),
  ]);
  applyTranslations();
}

export { SUPPORTED };
