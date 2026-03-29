import { defineConfig } from 'vite'
import { sveltekit } from '@sveltejs/kit/vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [
    sveltekit(),
    VitePWA({
      registerType: 'autoUpdate',
      scope: '/',
      base: '/',
      includeAssets: ['favicon.svg', 'favicon.png', 'icons/apple-touch-icon.png'],
      manifest: {
        name: 'Sajet ERP',
        short_name: 'Sajet',
        description: 'Sistema ERP SaaS — Gestión empresarial en la nube',
        theme_color: '#1e3a5f',
        background_color: '#0f172a',
        display: 'standalone',
        orientation: 'portrait-primary',
        start_url: '/',
        scope: '/',
        lang: 'es',
        icons: [
          {
            src: 'icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable',
          },
          {
            src: 'icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
        shortcuts: [
          {
            name: 'Dashboard',
            short_name: 'Panel',
            description: 'Ir al panel principal',
            url: '/dashboard',
            icons: [{ src: 'icons/icon-192.png', sizes: '192x192' }],
          },
          {
            name: 'Portal',
            short_name: 'Portal',
            description: 'Portal del cliente',
            url: '/portal',
            icons: [{ src: 'icons/icon-192.png', sizes: '192x192' }],
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        navigateFallback: '/200.html',
        navigateFallbackAllowlist: [/^(?!\/api)/],
        runtimeCaching: [
          // ── API GET: NetworkFirst (red → caché si offline) ──────────────
          {
            urlPattern: /^\/api\/onboarding-config\/active/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-onboarding-config',
              expiration: { maxEntries: 5, maxAgeSeconds: 60 * 60 * 24 },
              networkTimeoutSeconds: 5,
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: /^\/api\/customer-onboarding\/status/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-onboarding-status',
              expiration: { maxEntries: 5, maxAgeSeconds: 60 * 30 },
              networkTimeoutSeconds: 5,
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: /^\/api\/plans/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-plans',
              expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 },
              networkTimeoutSeconds: 5,
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: /^\/api\/dashboard/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-dashboard',
              expiration: { maxEntries: 10, maxAgeSeconds: 60 * 5 },
              networkTimeoutSeconds: 4,
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: /^\/api\/tenant-portal/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-tenant-portal',
              expiration: { maxEntries: 20, maxAgeSeconds: 60 * 15 },
              networkTimeoutSeconds: 5,
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          // ── Activos estáticos: CacheFirst ────────────────────────────────
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images',
              expiration: { maxEntries: 60, maxAgeSeconds: 60 * 60 * 24 * 30 },
            },
          },
          {
            urlPattern: /\.(?:woff|woff2|ttf|eot)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'fonts',
              expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 * 365 },
            },
          },
        ],
      },
    }),
  ],
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
