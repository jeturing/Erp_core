import { init, addMessages, getLocaleFromNavigator } from 'svelte-i18n';
import en from './en.json';
import es from './es.json';

export function initializeI18n() {
  // Register messages BEFORE init — ensures they are available on first render
  addMessages('en', en);
  addMessages('es', es);

  init({
    fallbackLocale: 'en',
    initialLocale: getInitialLocale(),
  });
}

export function getInitialLocale(): string {
  // Si está en localStorage, usar ese
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('locale');
    if (saved && ['en', 'es'].includes(saved)) {
      return saved;
    }

    // Auto-detect desde navigator.language
    const navigatorLang = getLocaleFromNavigator();
    if (navigatorLang?.startsWith('es')) {
      return 'es';
    }
  }

  return 'en';
}

export function setLocale(locale: 'en' | 'es') {
  if (typeof window !== 'undefined') {
    localStorage.setItem('locale', locale);
  }
}

export type Locale = 'en' | 'es';
