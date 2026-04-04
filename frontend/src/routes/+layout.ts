import { auth } from '$lib/stores'
import { getInitialLocale } from '$lib/i18n'
import { localeStore } from '$lib/stores/locale'

// SPA mode — disable SSR, enable client-side rendering only
export const ssr = false
export const prerender = false

// Initialize auth in the root load() so it runs BEFORE child layout load()
// functions. This resolves the race condition where (admin)/+layout.ts would
// check isAuthenticated before auth.init() had completed.
export async function load() {
  if (typeof window !== 'undefined') {
    const initialLocale = getInitialLocale()
    localeStore.set(initialLocale as any)
    await auth.init()
  }
}
