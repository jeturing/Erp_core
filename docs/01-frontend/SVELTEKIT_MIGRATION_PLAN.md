# SvelteKit Migration Plan

Estado: propuesto  
Fecha: 2026-03-29  
Ámbito: `/opt/Erp_core/frontend`

## Objetivo
Eliminar el router manual basado en `window.location.hash`, estabilizar navegación pública/privada y mover la SPA actual a una estructura de rutas mantenible sobre SvelteKit sin reescribir el backend FastAPI.

## Diagnóstico actual
- La app mezcla navegación por hash (`#/dashboard`, `#/signup`) con anclas de secciones (`#pricing`, `#faq`).
- `App.svelte` concentra routing, guards por auth y render de todas las páginas.
- Existen restos de enfoque SvelteKit en `src/routes/admin/+page.svelte`, pero la app efectiva corre como Vite + Svelte con montaje manual.
- El despliegue productivo publica `frontend/dist` en `static/spa` y FastAPI sirve el shell desde `app/services/spa_shell.py`.
- El check de frontend no está limpio: `svelte-check` reporta errores de tipos que hoy el build tolera.

## Qué resolvería SvelteKit
- Routing real por archivos en vez de un `switch` central.
- Separación limpia entre páginas públicas y privadas con layouts independientes.
- SSR/prerender para landing, legal, pricing y páginas públicas con mejor SEO.
- Navegación interna sin flashes de landing ni dependencia de hashes manuales.
- `load` por ruta para auth, datos iniciales y redirects.
- Menor riesgo de links muertos porque cada destino existe como archivo/ruta explícita.

## Recomendación de arquitectura
Mantener Svelte y migrar a SvelteKit con `adapter-static` en una primera fase.

Razón:
- Permite seguir publicando el build en `static/spa` sin rediseñar toda la infraestructura.
- Las páginas públicas pueden prerenderizarse.
- Las rutas privadas pueden seguir funcionando como app cliente con fallback estático.
- Evita abrir ahora un frente extra de SSR server-side o despliegue separado.

## Target técnico
- Public pages:
  - `/`
  - `/accountants`
  - `/about`
  - `/privacy`
  - `/terms`
  - `/data-processing`
  - `/security`
  - `/sla`
- Auth and onboarding:
  - `/login`
  - `/signup`
  - `/partner-signup`
  - `/recover-account`
  - `/plt/[slug]`
- Private app:
  - `/admin`
  - `/admin/tenants`
  - `/admin/domains`
  - `/admin/infrastructure`
  - `/tenant/portal`
  - `/partner/portal`
  - y el resto de vistas administrativas actuales

## Fases

### Fase 1: Preparación
- Crear rama de migración.
- Limpiar lockfile y pipeline de build para que `npm ci` vuelva a ser determinístico.
- Reducir errores de tipado de alto impacto que bloqueen mover componentes.
- Definir convención única de rutas y nombres.

### Fase 2: Shell base SvelteKit
- Inicializar estructura efectiva de SvelteKit en el frontend actual.
- Crear `+layout.svelte` público y `+layout.svelte` privado.
- Mover `NavBar`, `Footer` y wrappers de landing/layout a layouts reutilizables.
- Sustituir navegación basada en `window.location.hash` por enlaces/rutas de SvelteKit.

### Fase 3: Landing pública
- Migrar primero:
  - `Landing.svelte`
  - `AccountantsLanding.svelte`
  - `PartnerLanding.svelte`
  - páginas legales
- Implementar scroll de secciones con pathname limpio más hash opcional.
- Prerenderizar páginas públicas.

### Fase 4: Auth y guards
- Mover auth bootstrap a `load`/stores compartidos.
- Implementar protección de rutas privadas en layout de app.
- Evitar render intermedio de landing en rutas internas.

### Fase 5: Dashboard y portales
- Extraer cada vista del router central a rutas reales:
  - `/admin/*`
  - `/tenant/portal`
  - `/partner/portal`
- Dejar `App.svelte` fuera de la ruta crítica o retirarlo por completo.

### Fase 6: Deploy
- Reemplazar build actual por build SvelteKit estático.
- Ajustar `build_static.sh` para publicar el output nuevo.
- Ajustar `spa_shell.py` o retirarlo donde ya no haga falta bootstrap por hash.

## Riesgos
- La migración toca navegación, auth y deploy al mismo tiempo si no se fracciona.
- La app actual tiene deuda de tipos; parte del trabajo será saneamiento, no solo routing.
- El PWA/service worker debe revisarse después de cambiar estructura de rutas.
- Algunas rutas actuales dependen de `pathname` + hash de forma híbrida y requieren remapeo cuidadoso.

## Criterios de aceptación
- Ningún link público o privado apunta a rutas inexistentes.
- No hay flash de landing al entrar a rutas internas.
- Las rutas públicas cargan con pathname limpio.
- `build_static.sh` vuelve a generar un artefacto reproducible.
- El router manual deja de ser el punto central de navegación.

## Orden recomendado de ejecución
1. Corregir navegación muerta de la landing actual.
2. Arreglar pipeline de build y lockfile.
3. Migrar landing pública a SvelteKit.
4. Migrar auth y dashboard.
5. Retirar router manual.
