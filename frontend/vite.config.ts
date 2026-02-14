import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  base: '/static/spa/',
  plugins: [svelte()],
  build: {
    manifest: true,
  },
})
