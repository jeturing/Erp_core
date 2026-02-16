/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{svelte,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Design system tokens – Sajet ERP (Pencil design)
        charcoal:   '#1a1a1a',   // sidebar / left panel
        terracotta: '#C05A3C',   // primary accent (active nav, buttons)
        'bg-page':  '#F5F3EF',   // main content background
        'bg-card':  '#E8E4DC',   // card / panel background
        'bg-sidebar': '#1a1a1a', // sidebar background
        'border-light': '#D1CCC4',
        'border-dark':  '#3a3a3a',
        // Text
        'text-primary':   '#1a1a1a',
        'text-secondary': '#555555',
        'text-tertiary':  '#888888',
        'text-light':     '#F5F3EF',
        // Status
        success: '#4A7C59',
        warning: '#C05A3C',
        error:   '#B54A4A',
        info:    '#5C7C8A',
        // Grays
        'gray-400': '#888888',
        'gray-500': '#666666',
        'gray-600': '#555555',
        // Dark surfaces (for landing/auth panels)
        'dark-surface': '#2a2a2a',
        'dark-card':    '#1a1a1a',
        'dark-subtle':  '#3a3a3a',
      },
      fontFamily: {
        sans:    ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        body:    ['"Inter"', 'system-ui', 'sans-serif'],
        heading: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      letterSpacing: {
        widest: '0.1em',
      },
    },
  },
  plugins: [],
}
