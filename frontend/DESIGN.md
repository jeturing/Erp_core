# Design System: SAJET ERP

> Inspired by Linear.app, Vercel, and Stripe design systems from awesome-design-md.
> Adapted for Jeturing brand identity.

---

## 1. Visual Theme & Atmosphere

SAJET's landing page is a **dark-mode-first SaaS product site** built on near-black deep navy canvases where content emerges through precise luminance gradients. The design philosophy is "precision engineering for business" — every element occupies a calibrated position in a luminance hierarchy.

The hero section uses Jeturing's signature **Deep Blue** (`#003B73`) as the foundational dark surface, elevated by **Electric Green** (`#00FF9F`) as the single chromatic accent — a neon-clean signal against the dark canvas. This creates a high-contrast, modern enterprise aesthetic that communicates both trust and innovation.

**Key Characteristics:**

- Dark-mode-native: `#020e1f` marketing bg → `#003B73` brand dark → `#001a3a` panel
- Inter Variable for all text with negative letter-spacing on display sizes
- Plus Jakarta Sans for brand wordmarks and bold section headers
- Electric Green (`#00FF9F`) is the **only chromatic accent** — reserved strictly for primary CTAs, active states, and key brand moments
- Semi-transparent borders throughout: `rgba(255,255,255,0.06)` to `rgba(255,255,255,0.12)`
- Luminance-based elevation: deeper = darker bg, elevated = slightly lighter bg opacity
- Backdrop blur on all floating surfaces (nav, cards, modals)

---

## 2. Color Palette & Roles

### Background Surfaces

- **Marketing Black** (`#020e1f`): Deepest hero background — near-pure dark navy
- **Jeturing Deep Blue** (`#003B73`): Brand primary dark — panel backgrounds, hero
- **Surface Dark** (`#001a3a`): Elevated surface areas, card backgrounds
- **Surface Elevated** (`#0a2540`): Higher elevation — hover states, dropdowns
- **Surface Light** (`#0f3460`): Lightest dark surface — selected states

### Text & Content

- **Primary Text** (`#f0f4ff`): Near-white with blue tint — default heading color
- **Body Text** (`#c8d3e8`): Cool silver-blue for body text and descriptions
- **Muted Text** (`#7a8fa6`): De-emphasized content, metadata, labels
- **Subtle Text** (`#4a6080`): Timestamps, disabled states, placeholders

### Brand Accent (use sparingly)

- **Electric Green** (`#00FF9F`): THE accent — primary CTAs, active indicators, hero highlights
- **Electric Green Hover** (`#00e68f`): Slightly darker on hover
- **Electric Green Dim** (`rgba(0,255,159,0.15)`): Backgrounds for green-tinted elements
- **Electric Green Glow** (`rgba(0,255,159,0.08)`): Subtle ambient glow on dark

### Secondary Brand

- **Jeturing Deep Blue** (`#003B73`): Brand identity color
- **Sky Accent** (`#0EA5E9`): Secondary blue — chart lines, info states
- **Indigo Accent** (`#6366f1`): Tertiary — partner/accountant role differentiation

### Status Colors

- **Success** (`#10b981`): Positive states, uptime indicators
- **Warning** (`#f59e0b`): Alerts, pending states
- **Error** (`#ef4444`): Destructive actions, error states

### Border & Divider

- **Border Subtle** (`rgba(255,255,255,0.06)`): Default card border
- **Border Standard** (`rgba(255,255,255,0.10)`): Inputs, prominent containers
- **Border Green** (`rgba(0,255,159,0.25)`): CTA hover border
- **Divider** (`rgba(255,255,255,0.04)`): Section separators

---

## 3. Typography Rules

### Font Families

- **Display/Brand**: `Plus Jakarta Sans` — hero headlines, brand wordmark, section titles
- **UI/Body**: `Inter Variable` — body text, navigation, labels, descriptions
- **Code/Tech**: `JetBrains Mono` — URL bars, code snippets, metric values

### Hierarchy

| Role          | Font           | Size | Weight | Letter Spacing               | Color     |
| ------------- | -------------- | ---- | ------ | ---------------------------- | --------- |
| Display XL    | Jakarta        | 72px | 800    | -2px                         | `#f0f4ff` |
| Display L     | Jakarta        | 56px | 800    | -1.5px                       | `#f0f4ff` |
| Display       | Jakarta        | 48px | 700    | -1.2px                       | `#f0f4ff` |
| Heading 1     | Jakarta        | 36px | 700    | -0.8px                       | `#f0f4ff` |
| Heading 2     | Jakarta        | 28px | 600    | -0.5px                       | `#f0f4ff` |
| Section Label | Inter          | 13px | 600    | 0.08em (positive, uppercase) | `#00FF9F` |
| Body Large    | Inter          | 18px | 400    | -0.2px                       | `#c8d3e8` |
| Body          | Inter          | 16px | 400    | normal                       | `#c8d3e8` |
| Body Small    | Inter          | 14px | 400    | -0.1px                       | `#7a8fa6` |
| Caption       | Inter          | 12px | 500    | 0.05em                       | `#4a6080` |
| Metric/Value  | JetBrains Mono | 14px | 400    | normal                       | `#f0f4ff` |

### Principles

- **Negative letter-spacing at scale**: -2px at 72px, -1.2px at 48px, -0.5px at 28px
- **Display text compression**: headlines feel engineered, not decorative
- **Body text relaxed**: 1.6 line-height for readability on dark backgrounds
- **Section labels uppercase**: 13px, 0.08em tracking, `#00FF9F` color — signal a new section

---

## 4. Component Stylings

### Primary CTA Button (Electric Green)

```css
background: #00ff9f;
color: #020e1f; /* near-black text on green */
padding: 12px 28px;
border-radius: 8px;
font: Inter 600 15px;
letter-spacing: -0.1px;
transition: all 0.15s;
hover: {
  background: #00e68f;
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(0, 255, 159, 0.25);
}
```

### Ghost Button

```css
background: rgba(255, 255, 255, 0.04);
color: #c8d3e8;
padding: 12px 24px;
border-radius: 8px;
border: 1px solid rgba(255, 255, 255, 0.1);
font: Inter 500 15px;
hover: {
  background: rgba(255, 255, 255, 0.08);
}
```

### Feature Card

```css
background: rgba(255, 255, 255, 0.03);
border: 1px solid rgba(255, 255, 255, 0.06);
border-radius: 12px;
padding: 24px;
hover: {
  border-color: rgba(0, 255, 159, 0.2);
  background: rgba(0, 255, 159, 0.04);
}
```

### Navigation (dark transparent)

```css
background: rgba(2, 14, 31, 0.8);
backdrop-filter: blur(16px);
border-bottom: 1px solid rgba(255, 255, 255, 0.06);
/* on scroll: border-bottom strengthens to rgba(255,255,255,0.10) */
```

### Pill Badge

```css
background: rgba(0, 255, 159, 0.1);
border: 1px solid rgba(0, 255, 159, 0.25);
border-radius: 9999px;
padding: 4px 14px;
color: #00ff9f;
font: Inter 600 12px;
letter-spacing: 0.08em;
text-transform: uppercase;
```

### Stat Badge

```css
background: rgba(255, 255, 255, 0.05);
border: 1px solid rgba(255, 255, 255, 0.08);
border-radius: 9999px;
padding: 8px 20px;
backdrop-filter: blur(8px);
```

---

## 5. Layout Principles

### Grid & Container

- Max content width: `1200px` (`max-w-6xl`)
- Hero: centered single-column, generous vertical padding (min-height: 100vh)
- Feature grid: 3-column on desktop, 2 on tablet, 1 on mobile
- Section spacing: `py-24` (96px) standard, `py-32` (128px) for hero
- Internal padding: `px-6` standard, `px-4` on mobile

### Spacing

- Base: 8px grid
- Component padding: 24px (cards), 28px (major CTAs), 32px (sections)
- Section gap: 96px–128px vertical

---

## 6. Depth & Elevation

| Level     | Background                  | Border                   | Use                   |
| --------- | --------------------------- | ------------------------ | --------------------- |
| Canvas    | `#020e1f`                   | none                     | Page background       |
| Surface 1 | `rgba(255,255,255,0.02)`    | `rgba(255,255,255,0.06)` | Cards                 |
| Surface 2 | `rgba(255,255,255,0.04)`    | `rgba(255,255,255,0.10)` | Hover cards, inputs   |
| Floating  | `rgba(2,14,31,0.90)` + blur | `rgba(255,255,255,0.10)` | Nav, modals           |
| Active    | `rgba(0,255,159,0.08)`      | `rgba(0,255,159,0.25)`   | Selected, highlighted |

**Glow effects** (Electric Green):

- CTA hover: `box-shadow: 0 8px 24px rgba(0,255,159,0.25)`
- Icon hover: `filter: drop-shadow(0 0 8px rgba(0,255,159,0.4))`
- Badge ambient: `box-shadow: 0 0 16px rgba(0,255,159,0.08)`

---

## 7. Do's and Don'ts

### Do

- Use Electric Green (`#00FF9F`) ONLY for primary CTAs, active states, and the hero highlight word
- Set `letter-spacing: -1.2px` or tighter on all display headlines
- Use backdrop-blur on all floating elements (nav, cards on dark)
- Apply luminance stepping: each elevation level slightly brightens the surface
- Keep borders semi-transparent white — never solid dark borders on dark bg
- Use `#020e1f` as the deep background anchor (marketing black with navy tint)
- Use JetBrains Mono for all numeric/metric values in the dashboard mockup

### Don't

- Don't use Electric Green decoratively — it's reserved for interactive/CTA moments
- Don't use solid white text (`#ffffff`) — use `#f0f4ff` to prevent eye strain
- Don't use warm colors (yellow/orange/red) in UI chrome — only for status indicators
- Don't use positive letter-spacing on display text — always negative at scale
- Don't apply the landing design to admin panels — admin has its own design system
- Don't mix the landing palette with Pencil/admin terracotta colors

---

## 8. Responsive Behavior

| Breakpoint | Width      | Changes                                           |
| ---------- | ---------- | ------------------------------------------------- |
| Mobile     | < 640px    | Single column, 40px display text, compact padding |
| Tablet     | 640–1024px | Two columns, 48px display text                    |
| Desktop    | > 1024px   | Full 3-col grid, 56–72px display text             |

- Nav: horizontal links → hamburger at 768px
- Hero h1: 56px → 48px → 40px with letter-spacing scaling
- Feature grid: 3col → 2col → 1col
- CTA buttons: full-width on mobile

---

## 9. Agent Prompt Guide

### Quick Color Reference

- Page Background: `#020e1f`
- Brand Dark: `#003B73`
- Electric Green (CTA/Accent): `#00FF9F`
- Electric Green Glow: `rgba(0,255,159,0.15)`
- Heading text: `#f0f4ff`
- Body text: `#c8d3e8`
- Muted text: `#7a8fa6`
- Border (default): `rgba(255,255,255,0.06)`
- Border (hover): `rgba(0,255,159,0.25)`
- Nav background: `rgba(2,14,31,0.80)` + blur

### Example Prompts

- "Hero headline at 56px Plus Jakarta Sans weight 800, letter-spacing -1.5px, color `#f0f4ff`. Highlight word in `#00FF9F`. Subheading at 18px Inter weight 400, color `#c8d3e8`. Primary CTA: `#00FF9F` bg, `#020e1f` text, 8px radius, hover glow `rgba(0,255,159,0.25)`."
- "Feature card: `rgba(255,255,255,0.03)` bg, `1px solid rgba(255,255,255,0.06)` border, 12px radius. Icon container: `rgba(0,255,159,0.10)` bg, `#00FF9F` icon. Hover: border `rgba(0,255,159,0.20)`, bg `rgba(0,255,159,0.04)`."
- "Nav: `rgba(2,14,31,0.80)` bg, `blur(16px)`, `1px solid rgba(255,255,255,0.06)` border. Logo text: Plus Jakarta Sans 700 white. Links: Inter 14px `#c8d3e8`. CTA: Electric Green button."
