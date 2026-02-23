import { writable } from 'svelte/store';
import { locale as i18nLocale } from 'svelte-i18n';
import type { Locale } from '../i18n';

function createLocaleStore() {
  const { subscribe, set } = writable<Locale>('en');

  return {
    subscribe,
    set: (locale: Locale) => {
      if (typeof window !== 'undefined') {
        localStorage.setItem('locale', locale);
      }
      // Actualizar svelte-i18n también
      i18nLocale.set(locale);
      set(locale);
    },
    toggle: () => {
      let current: Locale = 'en';
      const unsubscribe = subscribe((value) => {
        current = value;
      });
      unsubscribe();
      const newLocale = current === 'en' ? 'es' : 'en';
      i18nLocale.set(newLocale);
      set(newLocale);
      if (typeof window !== 'undefined') {
        localStorage.setItem('locale', newLocale);
      }
    },
  };
}

export const localeStore = createLocaleStore();
