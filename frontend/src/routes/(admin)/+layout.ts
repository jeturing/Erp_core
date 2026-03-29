import { redirect } from '@sveltejs/kit'
import { get } from 'svelte/store'
import { isAuthenticated, currentUser } from '$lib/stores'

export const ssr = false

export function load() {
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
