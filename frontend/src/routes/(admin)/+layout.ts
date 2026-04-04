import { redirect } from '@sveltejs/kit'
import { get } from 'svelte/store'
import { isAuthenticated, currentUser, authReady } from '$lib/stores'

export const ssr = false

export async function load() {
  // Wait for auth bootstrap to complete before checking state.
  // This prevents a race condition where load() runs before
  // auth.init() has finished fetching /api/auth/me.
  await authReady

  const authed = get(isAuthenticated)
  const user = get(currentUser)

  if (!authed) {
    redirect(302, '/login')
  }

  // Tenants go to portal
  if (user?.role === 'tenant') {
    redirect(302, '/portal')
  }

  // Partners go to partner-portal
  if (user?.role === 'partner') {
    redirect(302, '/partner-portal')
  }
}
