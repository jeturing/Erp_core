import { redirect } from '@sveltejs/kit'
import { get } from 'svelte/store'
import { isAuthenticated, authReady } from '$lib/stores'

export const ssr = false

export async function load() {
  // Wait for auth bootstrap to complete before checking state.
  await authReady

  const authed = get(isAuthenticated)
  if (!authed) {
    redirect(302, '/login')
  }
}
