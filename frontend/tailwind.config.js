/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{svelte,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Jeturing Brand Colors
        primary: {
          50: '#E6EEF5',
          100: '#B3CDE0',
          200: '#80ABCB',
          300: '#4D89B6',
          400: '#1A67A1',
          500: '#003B73', // Main brand color - Deep Blue
          600: '#003265',
          700: '#002952',
          800: '#00203F',
          900: '#00172C',
        },
        secondary: {
          50: '#F8F9FA',
          100: '#E9ECEF',
          200: '#DEE2E6',
          300: '#CED4DA',
          400: '#ADB5BD',
          500: '#6C757D', // Metallic Gray
          600: '#5A6268',
          700: '#495057',
          800: '#343A40',
          900: '#212529',
        },
        accent: {
          50: '#E6FFF5',
          100: '#B3FFE0',
          200: '#80FFCB',
          300: '#4DFFB6',
          400: '#1AFFA9',
          500: '#00FF9F', // Electric Green - Tech Accent
          600: '#00CC7F',
          700: '#00995F',
          800: '#00663F',
          900: '#00331F',
        },
        innovation: {
          50: '#F3E5FF',
          100: '#E1BFFF',
          200: '#CF99FF',
          300: '#BD73FF',
          400: '#AB4DFF',
          500: '#8F00FF', // Futuristic Purple - Use sparingly
          600: '#7200CC',
          700: '#560099',
          800: '#390066',
          900: '#1D0033',
        },
        // Surface colors for dark mode
        surface: {
          dark: '#0F1419',
          card: '#1A1F26',
          highlight: '#252B33',
          border: '#2F3640',
        },
        // Status colors
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        info: '#3B82F6',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'monospace'],
      },
      boxShadow: {
        'glow': '0 0 20px rgba(0, 255, 159, 0.15)',
        'glow-primary': '0 0 20px rgba(0, 59, 115, 0.3)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
