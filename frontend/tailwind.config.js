/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{svelte,js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // ═══ Sajet Landing — Jeturing Brand System v2 ═══
        // Inspired by Linear.app, Stripe & Vercel DESIGN.md patterns
        primary: { DEFAULT: "#1B4FD8", dark: "#0F2D7A", light: "#EFF6FF" },
        secondary: "#0EA5E9", // Sky blue — charts, info, gradients
        accent: "#10B981", // Emerald — success, status indicators
        navy: "#0F2D7A", // Legacy hover states
        // ── Jeturing Brand ──────────────────────────────────────────────────
        "jet-blue": "#003B73", // Jeturing Deep Blue — hero base, brand dark
        "jet-green": "#00FF9F", // Electric Green — THE accent (CTAs only)
        // ── Dark Canvas Surfaces (Linear-inspired) ──────────────────────────
        canvas: "#020e1f", // Marketing black — deepest bg
        // ── Text Hierarchy ──────────────────────────────────────────────────
        "text-hero": "#f0f4ff", // Near-white hero headings
        "text-body": "#c8d3e8", // Cool silver-blue body text
        "text-muted": "#7a8fa6", // Muted text / metadata
        // ── Legacy ──────────────────────────────────────────────────────────
        slate: { DEFAULT: "#64748B", dark: "#0F172A", night: "#0F172A" },
        surface: "#FFFFFF",
        cloud: "#F8FAFC", // Fondo general landing
        border: "#E2E8F0", // Divisores landing
        coral: "#EF4444", // Error states

        // ═══ Admin Panel — Pencil Design System ═══
        charcoal: "#1a1a1a",
        terracotta: "#C05A3C",
        "bg-page": "#F5F3EF",
        "bg-card": "#E8E4DC",
        "bg-sidebar": "#1a1a1a",
        "border-light": "#D1CCC4",
        "border-dark": "#3a3a3a",
        // Text
        "text-primary": "#1a1a1a",
        "text-secondary": "#555555",
        "text-tertiary": "#888888",
        "text-light": "#F5F3EF",
        // Status
        success: "#4A7C59",
        warning: "#C05A3C",
        error: "#B54A4A",
        info: "#5C7C8A",
        // Grays
        "gray-400": "#888888",
        "gray-500": "#666666",
        "gray-600": "#555555",
        // Dark surfaces
        "dark-surface": "#2a2a2a",
        "dark-card": "#1a1a1a",
        "dark-subtle": "#3a3a3a",
      },
      fontFamily: {
        // Landing — Plus Jakarta Sans + Inter
        jakarta: ['"Plus Jakarta Sans"', "system-ui", "sans-serif"],
        inter: ['"Inter"', "system-ui", "sans-serif"],
        // Admin — Space Grotesk + Inter + JetBrains Mono
        sans: ['"Space Grotesk"', "system-ui", "sans-serif"],
        body: ['"Inter"', "system-ui", "sans-serif"],
        heading: ['"Space Grotesk"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      borderRadius: {
        "card-sm": "12px",
        "card-lg": "20px",
        btn: "8px",
      },
      boxShadow: {
        soft: "0 1px 3px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.06)",
        medium: "0 8px 32px rgba(15,45,122,0.12)",
        elevated: "0 20px 60px rgba(15,45,122,0.18)",
        // Jeturing brand shadows
        "green-glow": "0 8px 24px rgba(0,255,159,0.25)",
        "green-sm": "0 0 16px rgba(0,255,159,0.15)",
        "dark-card": "0 4px 24px rgba(0,0,0,0.4)",
      },
      backgroundImage: {
        // v2 — Jeturing brand hero (deep navy → jet-blue)
        "gradient-hero":
          "linear-gradient(135deg, #020e1f 0%, #003B73 60%, #0a2540 100%)",
        "gradient-hero-v1":
          "linear-gradient(135deg, #0F2D7A 0%, #1B4FD8 50%, #0EA5E9 100%)",
        "gradient-subtle": "linear-gradient(180deg, #F8FAFC 0%, #EFF6FF 100%)",
        // Dark subtle for feature sections
        "gradient-dark": "linear-gradient(180deg, #020e1f 0%, #001525 100%)",
      },
      letterSpacing: {
        widest: "0.1em",
      },
    },
  },
  plugins: [],
};
