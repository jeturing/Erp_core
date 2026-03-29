# SvelteKit Migration Plan

Estado: propuesto  
Fecha: 2026-03-29  
Ámbito: `/opt/Erp_core/frontend`  
Owner sugerido: `engineering/sajet-platform-engineer`

## Objetivo
Migrar por completo el frontend de SAJET desde la SPA actual basada en Vite + `App.svelte` + `window.location.hash` a una aplicación SvelteKit con rutas reales por archivos, manteniendo FastAPI como backend API y sin reescribir la capa de negocio de `/api/*`.

La meta no es "usar algunas carpetas `src/routes`", sino que SvelteKit sea el runtime oficial del frontend:
- routing por pathname limpio;
- layouts públicos y privados independientes;
- carga inicial y guards por `load`;
- build/deploy SvelteKit como artefacto oficial;
- retiro del router central en `src/App.svelte`.

## Estado actual confirmado

### Frontend real hoy
- El runtime real es Vite SPA, no SvelteKit.
- `frontend/package.json` no tiene `@sveltejs/kit`.
- `frontend/svelte.config.js` solo define `vitePreprocess()`; no hay adapter configurado.
- No existe `src/app.html`.
- `src/main.ts` monta `App.svelte` manualmente.
- `src/App.svelte` contiene el router principal, guards, redirects y render condicional de todas las pantallas.

### Acoplamientos actuales
- Existen `34` pantallas en `src/pages/*.svelte`.
- Existen `13` vistas "route-like" en `src/routes/*.svelte`.
- Hay al menos `120` referencias directas a `#/`, `window.location.hash` o `hashchange`.
- `src/lib/components/Layout.svelte` fija toda la navegación admin por hash.
- FastAPI todavía sirve el shell SPA por `app/services/spa_shell.py`.
- Hay `11` rutas backend que llaman `render_spa_shell(...)`.
- `scripts/build_static.sh` hoy construye Vite y publica `frontend/dist` en `static/spa`.

### Mezcla incompleta ya presente
- Existe `src/routes/admin/+page.svelte`, pero no gobierna la aplicación real.
- Hoy conviven:
  - SPA manual;
  - intento parcial de estructura SvelteKit;
  - bootstrap HTML desde FastAPI para inyectar hashes.

### Calidad actual del frontend
- `npm run build` funciona.
- `npm run check` no está limpio; hay errores heredados de tipado y componentes legacy.
- Esto significa que la migración a SvelteKit no es solo "mover archivos": también requiere saneamiento mínimo de tipos y sintaxis incompatible.

## Decisión de arquitectura

### Recomendación
Hacer la migración completa a SvelteKit en dos etapas, pero con un solo target final:

1. **SvelteKit + `adapter-static` + fallback SPA** como primera entrega productiva.
2. **SSR/prerender selectivo** para público cuando la base ya esté estabilizada.

### Razón
- Permite seguir desplegando en el mismo perímetro con FastAPI y nginx.
- Evita introducir otro servidor Node dedicado en esta fase.
- Reduce riesgo operacional porque las rutas privadas pueden seguir siendo cliente puro mientras se migra auth y navegación.
- Permite mover público y app privada sin congelar el negocio.

### Resultado esperado
- Landing y páginas legales con pathname limpio, listas para prerender.
- Portales y admin con layouts de SvelteKit y guards propios.
- FastAPI sigue exponiendo `/api/*`, pero deja de ser el router del frontend.

## Target técnico

### Estructura objetivo sugerida
```text
frontend/
  src/
    app.html
    hooks.client.ts
    lib/
      api/
      auth/
      components/
      features/
      stores/
      views/
    routes/
      +layout.svelte
      +layout.ts
      (public)/
        +layout.svelte
        +page.svelte
        accountants/+page.svelte
        about/+page.svelte
        privacy/+page.svelte
        terms/+page.svelte
        data-processing/+page.svelte
        security/+page.svelte
        sla/+page.svelte
        plt/[slug]/+page.svelte
      (auth)/
        login/+page.svelte
        signup/+page.svelte
        partner-signup/+page.svelte
        recover-account/+page.svelte
        onboarding-access/+page.svelte
      (app)/
        +layout.svelte
        +layout.ts
        admin/
          +page.svelte
          tenants/+page.svelte
          domains/+page.svelte
          infrastructure/+page.svelte
          tunnels/+page.svelte
          migrations/+page.svelte
          billing/+page.svelte
          plans/+page.svelte
          invoices/+page.svelte
          seats/+page.svelte
          settlements/+page.svelte
          reconciliation/+page.svelte
          dispersion/+page.svelte
          partners/+page.svelte
          leads/+page.svelte
          clients/+page.svelte
          quotations/+page.svelte
          catalog/+page.svelte
          workorders/+page.svelte
          blueprints/+page.svelte
          commissions/+page.svelte
          branding/+page.svelte
          reports/+page.svelte
          communications/+page.svelte
          testimonials/+page.svelte
          landing-sections/+page.svelte
          translations/+page.svelte
          settings/+page.svelte
          onboarding-config/+page.svelte
          roles/+page.svelte
          admin-users/+page.svelte
          agreements/+page.svelte
          audit/+page.svelte
          logs/+page.svelte
        tenant/portal/+page.svelte
        partner/portal/+page.svelte
        accountant/portal/+page.svelte
        customer-onboarding/+page.svelte
```

### Decisiones clave
- `src/App.svelte` deja de ser router y se retira al final.
- `src/pages/*` y `src/routes/*` actuales deben consolidarse en:
  - `src/routes/*` para rutas reales;
  - `src/lib/views/*` para vistas reutilizables si conviene separar presentación de routing.
- La navegación interna deja de usar `href="#/..."` y pasa a `href="/admin/..."`, `goto(...)` o componentes `Link`.

## Mapa de migración de rutas

### Público
- `Landing.svelte` -> `src/routes/(public)/+page.svelte`
- `AccountantsLanding.svelte` -> `src/routes/(public)/accountants/+page.svelte`
- `PartnerLanding.svelte` -> `src/routes/(public)/plt/[slug]/+page.svelte`
- `PublicInfoPage.svelte` -> páginas explícitas:
  - `/about`
  - `/privacy`
  - `/terms`
  - `/data-processing`
  - `/security`
  - `/sla`

### Auth
- `Login.svelte` -> `/login`
- `Signup.svelte` -> `/signup`
- `PartnerSignup.svelte` -> `/partner-signup`
- `RecoverAccount.svelte` -> `/recover-account`
- `OnboardingAccess.svelte` -> `/onboarding-access`

### Portales
- `TenantPortal.svelte` -> `/tenant/portal`
- `PartnerPortal.svelte` -> `/partner/portal`
- `AccountantPortal.svelte` -> `/accountant/portal`
- `CustomerOnboarding.svelte` -> `/customer-onboarding`

### App admin
- `Dashboard.svelte` -> `/admin`
- `Tenants.svelte` -> `/admin/tenants`
- `Domains.svelte` -> `/admin/domains`
- `Infrastructure.svelte` -> `/admin/infrastructure`
- `Tunnels.svelte` -> `/admin/tunnels`
- `Migrations.svelte` -> `/admin/migrations`
- `Billing.svelte` -> `/admin/billing`
- `Plans.svelte` -> `/admin/plans`
- `Invoices.svelte` -> `/admin/invoices`
- `Seats.svelte` -> `/admin/seats`
- `Settlements.svelte` -> `/admin/settlements`
- `Reconciliation.svelte` -> `/admin/reconciliation`
- `Dispersion.svelte` -> `/admin/dispersion`
- `Partners.svelte` -> `/admin/partners`
- `Leads.svelte` -> `/admin/leads`
- `Clients.svelte` -> `/admin/clients`
- `Quotations.svelte` -> `/admin/quotations`
- `ServiceCatalog.svelte` -> `/admin/catalog`
- `WorkOrders.svelte` -> `/admin/workorders`
- `Blueprints.svelte` -> `/admin/blueprints`
- `Commissions.svelte` -> `/admin/commissions`
- `Branding.svelte` -> `/admin/branding`
- `Reports.svelte` -> `/admin/reports`
- `Communications.svelte` -> `/admin/communications`
- `Testimonials.svelte` -> `/admin/testimonials`
- `LandingSections.svelte` -> `/admin/landing-sections`
- `Translations.svelte` -> `/admin/translations`
- `Settings.svelte` -> `/admin/settings`
- `OnboardingConfig.svelte` -> `/admin/onboarding-config`
- `Roles.svelte` -> `/admin/roles`
- `AdminUsers.svelte` -> `/admin/admin-users`
- `Agreements.svelte` -> `/admin/agreements`
- `Audit.svelte` -> `/admin/audit`
- `Logs.svelte` -> `/admin/logs`

## Estrategia de autenticación y guards

### Situación actual
- `auth.init()` se ejecuta en `App.svelte`.
- Los redirects dependen de `$currentUser.role` y de `window.location.hash`.
- El cliente API mezcla bearer en `localStorage` con refresh cookie vía `/api/auth/refresh`.

### Target SvelteKit
- Crear un `src/lib/auth/session.ts` para centralizar bootstrap de sesión.
- Mover la resolución de usuario actual a `+layout.ts` del grupo `(app)`.
- Separar dos políticas:
  - rutas públicas: sin auth;
  - rutas privadas: `load` + redirect si no hay sesión.
- Resolver redirects por rol sin hash:
  - tenant -> `/tenant/portal`
  - partner -> `/partner/portal`
  - accountant -> `/accountant/portal`
  - admin/operator/viewer -> `/admin`

### Recomendación operativa
- Primera fase privada con `ssr = false` en `(app)` para no bloquearse por cookies/headers server-side.
- Cuando la app esté estable, evaluar SSR real para páginas privadas solo si aporta algo.

## Estrategia de datos

### Qué se conserva
- El backend FastAPI y todos los endpoints `/api/*`.
- `src/lib/api/*` como capa de acceso, con refactor incremental.
- Stores actuales si siguen aportando valor, pero ya no como router ni guard global.

### Qué cambia
- Los datos iniciales de página deben salir de `load` donde aplique.
- Componentes grandes pueden seguir usando llamadas en cliente al inicio, pero ya dentro de rutas reales.
- La dependencia de `window.location.hash` y `window.location.origin + '/#/...'` debe eliminarse.

## Deploy objetivo

### Estado actual
- `scripts/build_static.sh` construye con Vite y copia a `static/spa`.
- `spa_shell.py` inyecta `window.__ERP_BOOTSTRAP__` y fuerza `window.location.hash`.

### Target fase 1
- Instalar y configurar SvelteKit con `adapter-static`.
- Generar salida estática compatible con despliegue actual.
- Reemplazar el shell actual por uno neutral, sin inyección de hash.
- Mantener FastAPI sirviendo el `index.html` compilado mientras se ajusta nginx.

### Target fase 2
- Hacer que nginx/FastAPI resuelvan pathname limpio con fallback a `index.html`.
- Retirar bootstrap de hash de `spa_shell.py`.
- Mantener `static/spa` solo como artefacto build, no como hack de routing.

## Fases de ejecución

### Fase 0. Preparación y saneamiento mínimo
Objetivo: dejar base mínima para iniciar sin mezclar deudas nuevas con el cambio de runtime.

Entregables:
- Agregar `@sveltejs/kit`.
- Crear `src/app.html`.
- Configurar `svelte.config.js` con adapter.
- Ajustar `vite.config.ts` para convivir con SvelteKit y PWA.
- Documentar errores actuales de `npm run check`:
  - errores bloqueantes del nuevo árbol;
  - errores heredados que pueden quedar fuera del primer corte.

No se hace todavía:
- mover todas las pantallas;
- limpiar toda la deuda histórica de TS.

### Fase 1. Bootstrap real de SvelteKit
Objetivo: levantar la app bajo SvelteKit sin migrar aún todas las páginas.

Entregables:
- `src/routes/+layout.svelte`
- `src/routes/+layout.ts`
- grupos `(public)`, `(auth)` y `(app)`
- layout base compartido
- primer `+error.svelte`
- eliminación del `mount(App, ...)` como entrypoint principal

Resultado esperado:
- la app ya corre desde SvelteKit;
- `App.svelte` pasa a ser compat layer temporal o deja de ser el root.

### Fase 2. Público y SEO
Objetivo: sacar del hash las rutas públicas.

Entregables:
- landing en `/`
- accountants en `/accountants`
- partner landing en `/plt/[slug]`
- páginas legales limpias
- navegación de marketing sin `#/`
- scroll de secciones usando pathname limpio + hash opcional real del browser

Resultado esperado:
- público prerenderizable;
- mejor SEO;
- sin bootstrap por hash.

### Fase 3. Auth y onboarding
Objetivo: mover login/signup/recover/onboarding a rutas reales.

Entregables:
- `/login`
- `/signup`
- `/partner-signup`
- `/recover-account`
- `/onboarding-access`
- redirects por `next=` usando query params reales

Resultado esperado:
- desaparecen las redirecciones `window.location.hash = '#/login'`.

### Fase 4. Layout privado y navegación admin
Objetivo: sustituir el router manual del panel.

Entregables:
- `src/routes/(app)/+layout.svelte`
- refactor de `Layout.svelte` para navegar por pathname real
- breadcrumbs y menú derivados de `$page.url.pathname`
- guards privados en `+layout.ts`

Resultado esperado:
- el usuario entra directo a `/admin/invoices` o `/admin/migrations`;
- no pasa por landing ni por router central.

### Fase 5. Migración por verticales
Objetivo: mover la aplicación privada por bloques funcionales, no archivo por archivo desordenado.

Orden recomendado:
1. Infraestructura
   - `/admin`
   - `/admin/tenants`
   - `/admin/domains`
   - `/admin/infrastructure`
   - `/admin/tunnels`
   - `/admin/migrations`
2. Facturación
   - `/admin/billing`
   - `/admin/plans`
   - `/admin/invoices`
   - `/admin/seats`
   - `/admin/settlements`
   - `/admin/reconciliation`
   - `/admin/dispersion`
3. Comercial
   - `/admin/partners`
   - `/admin/leads`
   - `/admin/clients`
   - `/admin/quotations`
   - `/admin/catalog`
4. Operaciones / analytics
   - `/admin/workorders`
   - `/admin/blueprints`
   - `/admin/commissions`
   - `/admin/branding`
   - `/admin/reports`
   - `/admin/communications`
5. Admin / configuración
   - `/admin/settings`
   - `/admin/onboarding-config`
   - `/admin/roles`
   - `/admin/admin-users`
   - `/admin/agreements`
   - `/admin/audit`
   - `/admin/logs`
   - `/admin/testimonials`
   - `/admin/landing-sections`
   - `/admin/translations`

### Fase 6. Portales
Objetivo: cerrar la migración con los flujos sensibles por rol.

Entregables:
- `/tenant/portal`
- `/partner/portal`
- `/accountant/portal`
- `/customer-onboarding`

Resultado esperado:
- redirects por rol resueltos en load/layout;
- cero dependencia de hashes para login y portal.

### Fase 7. Retiro de compatibilidad legacy
Objetivo: eliminar el modelo viejo.

Entregables:
- retirar `App.svelte` como router;
- retirar `hashchange`;
- retirar `window.location.hash` de componentes y stores;
- simplificar o retirar `spa_shell.py`;
- ajustar `scripts/build_static.sh` al output final SvelteKit;
- actualizar deploy del PCT 160.

## Riesgos reales

### Riesgo 1. Mezclar migración y saneamiento masivo
Si se intenta corregir todos los errores TS/Svelte del repo en la misma fase, el proyecto se frena.

Mitigación:
- limpiar solo lo que bloquee SvelteKit;
- abrir backlog separado para deuda histórica.

### Riesgo 2. Romper deep links de producción
Hoy hay usuarios y documentación que apuntan a `#/dashboard`, `#/signup`, etc.

Mitigación:
- crear redirecciones temporales desde hashes comunes;
- mantener compatibilidad controlada por una fase intermedia.

### Riesgo 3. Desalinear deploy FastAPI/nginx con el nuevo build
Si SvelteKit compila pero el fallback HTTP no está listo, las rutas limpias pueden devolver 404.

Mitigación:
- probar primero en staging/PCT con fallback explícito;
- no retirar `spa_shell.py` hasta validar pathname limpio extremo a extremo.

### Riesgo 4. Auth híbrida
El cliente actual depende de `localStorage` + refresh cookie.

Mitigación:
- no rediseñar auth completa en esta migración;
- encapsular el comportamiento existente y mover el guard, no el modelo de sesión completo.

## Criterios de aceptación
- `App.svelte` ya no decide la navegación de la aplicación.
- No existen referencias activas a `window.location.hash` en navegación principal.
- Todas las rutas públicas cargan con pathname limpio.
- Todas las rutas privadas críticas abren directo por URL real:
  - `/admin`
  - `/admin/invoices`
  - `/admin/migrations`
  - `/tenant/portal`
  - `/partner/portal`
- `scripts/build_static.sh` sigue generando un artefacto reproducible.
- El despliegue al PCT 160 sirve la app SvelteKit sin hash bootstrap.
- Los enlaces viejos más comunes no rompen la experiencia de usuario durante la transición.

## Backlog explícito fuera del alcance inicial
- Saneamiento completo de `npm run check`.
- Refactor completo de componentes `src/routes/admin/components/*` rotos.
- SSR server-side real para privados.
- Revisión profunda del service worker y estrategia offline.
- Reorganización de todos los stores hacia patrones más modernos si no es necesaria para routing.

## Estimación

### Estimación técnica
- Fase 0-1: 2 a 3 días
- Fase 2-3: 2 a 3 días
- Fase 4-5: 4 a 6 días
- Fase 6-7: 2 a 3 días

Estimación total razonable:
- `10 a 15 días efectivos` si se ejecuta por un solo owner técnico;
- más si se decide limpiar deuda histórica de frontend en paralelo.

## Recomendación final
No arrancar la migración por el dashboard. Arrancarla por la base:

1. instalar SvelteKit de verdad;
2. mover público y auth;
3. montar layout privado;
4. migrar admin por verticales;
5. retirar hash routing al final.

Ese orden reduce riesgo de deploy, mantiene productividad y evita reescribir dos veces la misma navegación.
