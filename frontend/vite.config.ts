import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  base: command === 'serve' ? '/' : '/static/spa/',
  plugins: [svelte()],
  build: {
    manifest: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:4443',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:4443',
        changeOrigin: true,
      },
    },
  },
}))
