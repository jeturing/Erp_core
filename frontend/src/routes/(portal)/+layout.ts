import { redirect } from '@sveltejs/kit'
import { get } from 'svelte/store'
import { isAuthenticated } from '$lib/stores'

export const ssr = false

export function load() {
  const authed = get(isAuthenticated)
  if (!authed) {
    redirect(302, '/login')
  }
}
