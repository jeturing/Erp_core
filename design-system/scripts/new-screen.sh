#!/usr/bin/env bash
# =============================================================================
# new-screen.sh — argo-web screen scaffolding (interactivo)
#
# Uso:
#   bash design-system/scripts/new-screen.sh "<slug>" "<descripcion>"
#   bash design-system/scripts/new-screen.sh login "Pantalla de inicio de sesión"
#
# Funciona con: React · Svelte · Vue · Vanilla JS · cualquier stack
# Repo: https://github.com/jeturing/Jeturing-design-web
# =============================================================================

set -e

SCREEN_SLUG="${1}"
SCREEN_DESC="${2}"
DATE=$(date '+%Y-%m-%d')

# ─── Buscar template Pencil ────────────────────────────────────────────────────
PEN_TEMPLATE=""
for loc in \
  "$(dirname "$0")/../skill/pencil-new.pen" \
  "/opt/Erp_core/.claude/skills/design-web/pencil-new.pen" \
  "design-system/skill/pencil-new.pen"
do
  [ -f "$loc" ] && PEN_TEMPLATE="$loc" && break
done

# ─── Colores de terminal ───────────────────────────────────────────────────────
BOLD="\033[1m"
DIM="\033[2m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

# ─── Banner ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${CYAN}  ┌─────────────────────────────────────────────────┐${RESET}"
echo -e "${BOLD}${CYAN}  │  argo-web  ·  new-screen scaffold               │${RESET}"
echo -e "${BOLD}${CYAN}  │  Pencil → Approve → Build                       │${RESET}"
echo -e "${BOLD}${CYAN}  └─────────────────────────────────────────────────┘${RESET}"
echo ""

# ─── Paso 1: Slug y descripción ───────────────────────────────────────────────
if [ -z "$SCREEN_SLUG" ]; then
  echo -e "${BOLD}Nombre de la pantalla (slug, sin espacios):${RESET}"
  echo -e "${DIM}  Ejemplo: login · dashboard · checkout · tenant-detail${RESET}"
  read -r -p "  > " SCREEN_SLUG
fi

[ -z "$SCREEN_SLUG" ] && echo -e "${RED}Error: slug requerido.${RESET}" && exit 1

if [ -z "$SCREEN_DESC" ]; then
  echo ""
  echo -e "${BOLD}Descripción corta de la pantalla:${RESET}"
  read -r -p "  > " SCREEN_DESC
fi

BASE_DIR="design/screens/${SCREEN_SLUG}"

if [ -d "$BASE_DIR" ]; then
  echo -e "\n${RED}❌  Ya existe: ${BASE_DIR}${RESET}"
  exit 1
fi

# ─── Paso 2: Elegir paleta ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━ PALETA DE COLOR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${DIM}  Elige una paleta curada para evitar colores AI-genéricos${RESET}"
echo ""
echo -e "   ${BOLD} 1)${RESET} Dark Tech          ${DIM}#003B73 + #00FF9F${RESET}  · SaaS, Dashboards, Tech Premium        [dark]"
echo -e "   ${BOLD} 2)${RESET} Oxford Legal        ${DIM}#1B3A6B + #E8C96B${RESET}  · Profesional, Corporativo, Legal       [light]"
echo -e "   ${BOLD} 3)${RESET} Navy Power          ${DIM}#1B2E3C + #4B0000${RESET}  · Lujo, Poder, Alta Gama                [dark]"
echo -e "   ${BOLD} 4)${RESET} Dark Luxury         ${DIM}#201315 + #E76D57${RESET}  · Elegante, Sofisticado, Premium         [dark]"
echo -e "   ${BOLD} 5)${RESET} Warm Gold           ${DIM}#532200 + #E1A140${RESET}  · Moderno, Lujoso, Cálido               [dark]"
echo -e "   ${BOLD} 6)${RESET} Warm Glam           ${DIM}#28221E + #7F6951${RESET}  · Glamuroso, Real Estate Premium        [light]"
echo -e "   ${BOLD} 7)${RESET} Forest Gold         ${DIM}#122620 + #D6AD60${RESET}  · Luxury Professional, Naturaleza       [dark]"
echo -e "   ${BOLD} 8)${RESET} Marsala Classic     ${DIM}#663635 + #DEB3AD${RESET}  · Clásico, Femenino, Minimalista        [light]"
echo -e "   ${BOLD} 9)${RESET} Deep Blue Premium   ${DIM}#091235 + #88A9C3${RESET}  · Tech, Premium, Profundo               [dark]"
echo -e "   ${BOLD}10)${RESET} Trust Warm          ${DIM}#532200 + #E1A140${RESET}  · Confianza, Calidez, Profesional       [light]"
echo -e "   ${BOLD} 0)${RESET} Personalizada       ${DIM}(definir mis propios tokens)${RESET}"
echo ""
read -r -p "  Paleta [1-10, 0=custom, Enter=Dark Tech]: " PALETTE_NUM

case "$PALETTE_NUM" in
  1|"")  PALETTE_NAME="Dark Tech";         PALETTE_FILE="01-dark-tech";         P_PRIMARY="#003B73"; P_ACCENT="#00FF9F"; P_BG_BASE="#0a0f1e";  P_BG_SURFACE="#111827"; P_TEXT="#f0f4ff";  P_MODE="dark"  ;;
  2)     PALETTE_NAME="Oxford Legal";      PALETTE_FILE="02-oxford-legal";      P_PRIMARY="#1B3A6B"; P_ACCENT="#E8C96B"; P_BG_BASE="#F5F6FA";  P_BG_SURFACE="#FFFFFF"; P_TEXT="#1C1C2E";  P_MODE="light" ;;
  3)     PALETTE_NAME="Navy Power";        PALETTE_FILE="03-navy-power";        P_PRIMARY="#1B2E3C"; P_ACCENT="#4B0000"; P_BG_BASE="#0C0C1E";  P_BG_SURFACE="#1B2E3C"; P_TEXT="#F3E3E2";  P_MODE="dark"  ;;
  4)     PALETTE_NAME="Dark Luxury";       PALETTE_FILE="04-dark-luxury";       P_PRIMARY="#201315"; P_ACCENT="#E76D57"; P_BG_BASE="#201315";  P_BG_SURFACE="#2E1A1A"; P_TEXT="#F8F3EB";  P_MODE="dark"  ;;
  5)     PALETTE_NAME="Warm Gold";         PALETTE_FILE="05-warm-gold";         P_PRIMARY="#532200"; P_ACCENT="#E1A140"; P_BG_BASE="#3A1500";  P_BG_SURFACE="#532200"; P_TEXT="#EFCFA0";  P_MODE="dark"  ;;
  6)     PALETTE_NAME="Warm Glam";         PALETTE_FILE="06-warm-glam";         P_PRIMARY="#28221E"; P_ACCENT="#7F6951"; P_BG_BASE="#CECBC8";  P_BG_SURFACE="#FFFFFF"; P_TEXT="#28221E";  P_MODE="light" ;;
  7)     PALETTE_NAME="Forest Gold";       PALETTE_FILE="07-forest-gold";       P_PRIMARY="#122620"; P_ACCENT="#D6AD60"; P_BG_BASE="#0E1E1A";  P_BG_SURFACE="#122620"; P_TEXT="#F4EBD0";  P_MODE="dark"  ;;
  8)     PALETTE_NAME="Marsala Classic";   PALETTE_FILE="08-marsala-classic";   P_PRIMARY="#663635"; P_ACCENT="#DEB3AD"; P_BG_BASE="#F9F1F0";  P_BG_SURFACE="#FFFFFF"; P_TEXT="#3D1F1F";  P_MODE="light" ;;
  9)     PALETTE_NAME="Deep Blue Premium"; PALETTE_FILE="09-deep-blue-premium"; P_PRIMARY="#091235"; P_ACCENT="#88A9C3"; P_BG_BASE="#091235";  P_BG_SURFACE="#14202E"; P_TEXT="#E8EEF8";  P_MODE="dark"  ;;
  10)    PALETTE_NAME="Trust Warm";        PALETTE_FILE="10-trust-warm";        P_PRIMARY="#532200"; P_ACCENT="#E1A140"; P_BG_BASE="#FDF6EC";  P_BG_SURFACE="#FFFFFF"; P_TEXT="#2C1A0E";  P_MODE="light" ;;
  0)
    PALETTE_NAME="Custom"; PALETTE_FILE="custom"
    echo ""
    read -r -p "  --color-primary  (marca, headers): " P_PRIMARY
    read -r -p "  --color-accent   (highlights, CTAs): " P_ACCENT
    read -r -p "  --bg-base        (background): " P_BG_BASE
    read -r -p "  --bg-surface     (cards, panels): " P_BG_SURFACE
    read -r -p "  --text-primary   (texto principal): " P_TEXT
    read -r -p "  Modo [dark/light]: " P_MODE
    ;;
  *)
    echo -e "${YELLOW}  Opción inválida — usando Dark Tech por defecto${RESET}"
    PALETTE_NAME="Dark Tech"; PALETTE_FILE="01-dark-tech"
    P_PRIMARY="#003B73"; P_ACCENT="#00FF9F"; P_BG_BASE="#0a0f1e"
    P_BG_SURFACE="#111827"; P_TEXT="#f0f4ff"; P_MODE="dark"
    ;;
esac

# ─── Paso 3: Elegir stack ─────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━ STACK TECNOLÓGICO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "   ${BOLD}1)${RESET} Svelte 5       (runes, SvelteKit)"
echo -e "   ${BOLD}2)${RESET} React          (hooks, Next.js, Vite)"
echo -e "   ${BOLD}3)${RESET} Vue 3          (Composition API, Nuxt)"
echo -e "   ${BOLD}4)${RESET} Vanilla JS/TS  (sin framework)"
echo -e "   ${BOLD}5)${RESET} Otro"
echo ""
read -r -p "  Stack [1-5, Enter=Svelte 5]: " STACK_NUM

case "$STACK_NUM" in
  1|"") STACK_NAME="Svelte 5"      ;;
  2)    STACK_NAME="React"         ;;
  3)    STACK_NAME="Vue 3"         ;;
  4)    STACK_NAME="Vanilla JS/TS" ;;
  5)
    read -r -p "  Nombre del stack: " STACK_NAME
    STACK_NAME="${STACK_NAME:-Other}"
    ;;
  *)    STACK_NAME="Svelte 5"      ;;
esac

# ─── Crear carpeta ────────────────────────────────────────────────────────────
mkdir -p "$BASE_DIR"

# ─── 01 — Pencil ──────────────────────────────────────────────────────────────
if [ -n "$PEN_TEMPLATE" ]; then
  cp "$PEN_TEMPLATE" "${BASE_DIR}/01-pencil.pen"
else
  printf '{"version":"2.10","_screen":"%s","_palette":"%s","children":[]}' \
    "$SCREEN_SLUG" "$PALETTE_NAME" > "${BASE_DIR}/01-pencil.pen"
fi

# ─── 02 — Approval ────────────────────────────────────────────────────────────
cat > "${BASE_DIR}/02-approval.md" << EOF
# Aprobación de Diseño — ${SCREEN_DESC}

**Slug:** \`${SCREEN_SLUG}\`
**Stack:** ${STACK_NAME}
**Paleta:** ${PALETTE_NAME} (${P_MODE})
**Fecha creación:** ${DATE}
**Estado:** ⏳ Pendiente de aprobación

---

## Tokens de la Paleta

\`\`\`css
:root {
  --color-primary:  ${P_PRIMARY};
  --color-accent:   ${P_ACCENT};
  --bg-base:        ${P_BG_BASE};
  --bg-surface:     ${P_BG_SURFACE};
  --text-primary:   ${P_TEXT};
}
\`\`\`

> ⚠️ Usar **siempre variables CSS** — nunca valores hardcoded.

---

## Checklist de Aprobación

- [ ] Paleta de colores aplicada mediante variables CSS
- [ ] Tipografía definida y alineada con el estilo de la paleta
- [ ] Responsive revisado: 375px (mobile) y 1280px (desktop)
- [ ] Motion plan documentado (ver \`06-motion-plan.md\`)
- [ ] Componentes seleccionados y confirmados (ver \`04-components.md\`)
- [ ] Estados presentes: loading, empty, error
- [ ] Contraste WCAG AA verificado (4.5:1 texto, 3:1 UI)
- [ ] Íconos SVG — no emoji

---

## Firma

**Aprobado por:** _______________
**Fecha de aprobación:** _______________
**Versión aprobada:** v0.1

> ⛔ **SIN ESTE ARCHIVO FIRMADO NO SE INICIA EL DESARROLLO**
EOF

# ─── 03 — Flow ASCII ──────────────────────────────────────────────────────────
cat > "${BASE_DIR}/03-flow-ascii.md" << EOF
# Flujo ASCII — ${SCREEN_DESC}

**Pantalla:** \`${SCREEN_SLUG}\` · **Stack:** ${STACK_NAME}
**Fecha:** ${DATE}

---

## Flujo de Navegación y Elementos

\`\`\`
USER ARRIVES
     │
     ▼
┌──────────────────────────────────┐
│  [ Elemento 1 ]                  │  ← fadeIn (0.3s)
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  [ Elemento 2 ] (×N)            │  ← stagger (0.07s each)
└──────────────────────────────────┘
         │
         ▼
[ Completar flujo... ]
\`\`\`

## Estados de la Pantalla

\`\`\`
ESTADO INICIAL
│
├─▶ LOADING → [ Skeleton loader — NO spinner genérico ]
├─▶ EMPTY   → [ Ilustración SVG + mensaje + CTA ]
├─▶ ERROR   → [ Mensaje claro + acción de recuperación ]
└─▶ SUCCESS → [ Datos reales con animaciones ]
\`\`\`

## Interacciones Clave

| Elemento | Acción | Resultado | Animación |
|----------|--------|-----------|-----------|
| [ CTA btn ] | click | [ ] | scale 0.98 |
| [ Form ] | submit invalid | Error inline | shakeError |
| [ Card ] | hover | [ ] | scale 1.02 |
EOF

# ─── 04 — Components ──────────────────────────────────────────────────────────
cat > "${BASE_DIR}/04-components.md" << EOF
# Componentes — ${SCREEN_DESC}

**Pantalla:** \`${SCREEN_SLUG}\` · **Stack:** ${STACK_NAME}
**Fecha:** ${DATE}

> Siempre presentar lista de opciones antes de implementar.
> Usar MCP magic para explorar variantes.

---

## [ Componente Principal ]

**Opciones presentadas:**
1. Opción A — [ descripción + estilo visual ]
2. Opción B — [ descripción + estilo visual ]
3. Opción C — [ descripción + estilo visual ]
4. Custom desde argo-web design system

**Seleccionado:** _______________
**Fuente:** MCP magic / design system / custom

---

<!-- Duplicar bloque por cada componente adicional -->
EOF

# ─── 05 — DB Model ────────────────────────────────────────────────────────────
cat > "${BASE_DIR}/05-db-model.md" << EOF
# Modelo BDA — ${SCREEN_DESC}

**Pantalla:** \`${SCREEN_SLUG}\` · **Stack:** ${STACK_NAME}
**Fecha:** ${DATE}

> Si la pantalla no consume datos, marcar como N/A.

---

## Estado: [ Completo | En progreso | N/A ]

## Tablas / Colecciones Involucradas

| Tabla/Colección | Operación | Campos leídos | Campos escritos |
|-----------------|-----------|---------------|-----------------|
| \`[ nombre ]\` | SELECT | id, name, status | — |

## Queries / Mutations Principales

\`\`\`sql
-- Query 1
SELECT ... FROM ... WHERE ...;
\`\`\`

## API / Endpoints

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | \`/api/[]\` | [ ] | JWT / API Key |

## Permisos

| Rol | Acción |
|-----|--------|
| admin | CRUD |
| user | Read |
EOF

# ─── 06 — Motion Plan ─────────────────────────────────────────────────────────
cat > "${BASE_DIR}/06-motion-plan.md" << EOF
# Motion Plan — ${SCREEN_DESC}

**Pantalla:** \`${SCREEN_SLUG}\` · **Stack:** ${STACK_NAME}
**Fecha:** ${DATE}
**Librería:** \`motion\` v12 — \`import { animate, stagger, inView } from "motion"\`

> motion es framework-agnostic: funciona con React, Svelte, Vue y Vanilla JS.

---

## Animaciones por Elemento

| Elemento | Selector | Trigger | Función | Duración | Easing |
|----------|----------|---------|---------|----------|--------|
| [ ] | \`.[ cls ]\` | onMount/useEffect | \`fadeIn\` | 0.5s | easeOutExpo |
| [ ] | \`.[ cls ]\` | onMount/useEffect | \`staggerReveal\` | 0.5s | easeOutExpo |
| [ ] | \`.[ cls ]\` | scroll | \`scrollReveal\` | 0.6s | easeOutExpo |
| [ ] | \`.[ cls ]\` | hover | \`magnetic\` | 0.2s | easeOutExpo |
| [ ] | \`.[ cls ]\` | error | \`shakeError\` | 0.5s | easeInOut |

---

## Implementación base

\`\`\`typescript
import { animate, stagger, inView } from 'motion'

// Al montar el componente
// Svelte: onMount | React: useEffect | Vue: onMounted
animate('.hero-title', { opacity: [0, 1], y: [20, 0] }, { duration: 0.5 })
animate('.card-item', { opacity: [0, 1], y: [16, 0] },
  { delay: stagger(0.07), duration: 0.5 })

// Scroll reveal
inView('.section', ({ target }) => {
  animate(target, { opacity: [0, 1], y: [24, 0] }, { duration: 0.6 })
}, { margin: '-10% 0px' })
\`\`\`

---

## prefers-reduced-motion

- [ ] Implementado

\`\`\`typescript
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
// ... animaciones
\`\`\`
EOF

# ─── Resumen final ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}─────────────────────────────────────────────────────────${RESET}"
echo -e "${BOLD}${GREEN}  ✅  argo-web — Pantalla lista: ${SCREEN_SLUG}${RESET}"
echo -e "${BOLD}${GREEN}─────────────────────────────────────────────────────────${RESET}"
echo ""
echo -e "  ${BOLD}Paleta:${RESET} ${PALETTE_NAME} (${P_MODE})  ${DIM}primary: ${P_PRIMARY}  accent: ${P_ACCENT}${RESET}"
echo -e "  ${BOLD}Stack:${RESET}  ${STACK_NAME}"
echo ""
echo -e "  ${CYAN}📁 ${BASE_DIR}/${RESET}"
echo -e "  ${DIM}    ├── 01-pencil.pen       ← ABRIR EN PENCIL y diseñar${RESET}"
echo -e "  ${YELLOW}    ├── 02-approval.md      ← FIRMAR antes de codear ⛔${RESET}"
echo -e "  ${DIM}    ├── 03-flow-ascii.md    ← Flujo elemento a elemento${RESET}"
echo -e "  ${DIM}    ├── 04-components.md    ← Opciones MCP magic + selección${RESET}"
echo -e "  ${DIM}    ├── 05-db-model.md      ← Modelo BDA/DB${RESET}"
echo -e "  ${DIM}    └── 06-motion-plan.md   ← Animaciones Motion${RESET}"
echo ""
echo -e "  ${BOLD}Próximos pasos:${RESET}"
echo -e "  ${DIM}  1. Abrir 01-pencil.pen en Pencil${RESET}"
echo -e "  ${DIM}  2. Diseñar con la paleta ${PALETTE_NAME}${RESET}"
echo -e "  ${DIM}  3. Firmar 02-approval.md${RESET}"
echo -e "  ${DIM}  4. Desarrollar 1:1 con el diseño aprobado${RESET}"
echo ""
echo -e "  ${DIM}argo-web: https://github.com/jeturing/Jeturing-design-web${RESET}"
echo ""
