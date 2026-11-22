import { useEffect, useState } from 'react';

const STORAGE_KEY = 'visionalert-theme';
export const THEME_MODES = ['light', 'dark', 'system'];

function readPreference() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return THEME_MODES.includes(stored) ? stored : 'system';
  } catch {
    return 'system';
  }
}

function systemQuery() {
  return typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null;
}

// Returns the user's choice ('light' | 'dark' | 'system') and the theme that
// actually applies ('light' | 'dark'), following the OS setting for 'system'.
export function useTheme() {
  const [preference, setPreferenceState] = useState(readPreference);
  const [systemDark, setSystemDark] = useState(() => systemQuery()?.matches ?? false);

  useEffect(() => {
    const query = systemQuery();
    if (!query) return undefined;
    const handleChange = (event) => setSystemDark(event.matches);
    query.addEventListener('change', handleChange);
    return () => query.removeEventListener('change', handleChange);
  }, []);

  function setPreference(next) {
    setPreferenceState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Storage can be unavailable (private mode); the choice then lasts for this visit only.
    }
  }

  const resolved = preference === 'system' ? (systemDark ? 'dark' : 'light') : preference;
  return { preference, setPreference, resolved };
}
