import { writable } from 'svelte/store';

const STORAGE_KEY = 'sajet_dark_mode';

function readPreference(): boolean {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved !== null) return saved === 'true';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  } catch {
    return false;
  }
}

function applyClass(dark: boolean) {
  try {
    if (dark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  } catch { /* SSR safety */ }
}

function createDarkMode() {
  const { subscribe, set, update } = writable<boolean>(false);

  return {
    subscribe,
    init() {
      const dark = readPreference();
      set(dark);
      applyClass(dark);
    },
    toggle() {
      update((current) => {
        const next = !current;
        applyClass(next);
        try { localStorage.setItem(STORAGE_KEY, String(next)); } catch { /* */ }
        return next;
      });
    },
    setDark(value: boolean) {
      set(value);
      applyClass(value);
      try { localStorage.setItem(STORAGE_KEY, String(value)); } catch { /* */ }
    },
  };
}

export const darkMode = createDarkMode();
