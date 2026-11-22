import { useSyncExternalStore } from 'react';

// One theme for the whole app. The choice ('light' | 'dark' | 'system') is kept
// in localStorage and the resolved theme is written to <html data-theme="...">,
// where the CSS variables in App.css pick it up. index.html applies the same
// logic before React loads so the page never flashes the wrong theme.
const STORAGE_KEY = 'visionalert-theme';
export const THEME_MODES = ['light', 'dark', 'system'];

const listeners = new Set();
const darkQuery =
  typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null;

function readPreference() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return THEME_MODES.includes(stored) ? stored : 'system';
  } catch {
    return 'system';
  }
}

let preference = readPreference();

function resolve(current) {
  if (current === 'system') return darkQuery?.matches ? 'dark' : 'light';
  return current;
}

function applyTheme() {
  document.documentElement.dataset.theme = resolve(preference);
}

function notify() {
  applyTheme();
  listeners.forEach((listener) => listener());
}

if (typeof document !== 'undefined') {
  applyTheme();
  darkQuery?.addEventListener('change', notify);
}

function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function setPreference(next) {
  preference = next;
  try {
    localStorage.setItem(STORAGE_KEY, next);
  } catch {
    // Storage can be unavailable (private mode); the choice then lasts for this visit only.
  }
  notify();
}

// Returns the user's choice and the theme that actually applies.
export function useTheme() {
  const currentPreference = useSyncExternalStore(subscribe, () => preference);
  const resolved = useSyncExternalStore(subscribe, () => resolve(preference));
  return { preference: currentPreference, setPreference, resolved };
}
