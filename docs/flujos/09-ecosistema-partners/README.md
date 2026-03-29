# 09 - Ecosistema Partners (Leads/Comisiones/Cotizaciones)

Estado: vigente  
Validado: 2026-03-28  
Entorno objetivo: `/opt/Erp_core`


## Objetivo
Gestionar ciclo comercial de partners: leads, comisiones y cotizaciones con integración de cobro.

## Disparador
- Frontend:
  - `#/partners`
  - `#/leads`
  - `#/commissions`
  - `#/quotations`
  - `#/partner-signup`
  - tarjeta/CTA partner dentro de `#/signup`

## Secuencia ASCII

```text
[Partner/Admin en SPA]
   |
   +--> CRUD Partners (/api/partners)
   +--> CRUD Leads (/api/leads)
   +--> CRUD Commissions (/api/commissions)
   +--> CRUD Quotations (/api/quotations)
   v
[Backend routes]
   |
   +--> persistencia SQLAlchemy
   +--> reglas de estado/pipeline
   +--> notificaciones (email)
   +--> opcional Stripe Connect (split/payout)
   v
[Reportes y operación comercial]
```

## Stripe Connect (resumen)
- `/api/stripe-connect/create-account`
- `/api/stripe-connect/{partner_id}/onboarding-link`
- `/api/stripe-connect/{partner_id}/status`
- `/api/stripe-connect/transfer`
- `/api/partner-portal/onboarding/start-stripe`
- `/api/partner-portal/onboarding/verify-stripe`

## Hallazgos operativos 2026-03-28
- La entrada publica de partners ya no depende de encontrar el link escondido en el login: la home publica y `#/signup` exponen la ruta partner junto con empresa y firma contable. — Confirmado 2026-03-28 [frontend landing/signup]
- El acceso partner productivo fue validado E2E con reset admin, login por email verification y lectura de endpoints del portal. — Confirmado 2026-03-28 [HTTP E2E]
- `onboarding_step < 4` mantiene al usuario dentro del onboarding del portal partner; el shell principal no carga tabs operativos hasta completar ese estado. — Confirmado 2026-03-28 [inspección `PartnerPortal.svelte` + API]
- Existe endpoint backend para `POST /api/partner-portal/change-password`, pero la recuperación de acceso previa al login sigue siendo soporte asistido; `#/recover-account` no resetea contraseña del partner por sí mismo. — Confirmado 2026-03-28 [frontend + backend]
- El onboarding Stripe del partner quedó endurecido:
  - exige `contract_signed_at`
  - exige `country` del partner antes de crear la cuenta Connect
  - `skip-stripe` solo funciona con `onboarding_bypass=true`
  - el portal muestra requisitos pendientes de Stripe y deja de asumir que volver del hosted onboarding equivale a activación real
- El routing comercial del checkout con `partner_code` quedó alineado al modelo actual:
  - `jeturing_collects` → checkout en plataforma + dispersión automática por Connect usando la comisión firmada del partner
  - `partner_collects` → cobro externo del partner; no se fuerza split automático en el checkout público
- Se corrigieron bugs previos del flujo:
  - comparación inválida `partner.billing_scenario == "B"`
  - uso de enums inexistentes (`PayerType.END_CUSTOMER`, `CollectorType.PARTNER_COLLECTS`)
  - filtro a campo inexistente `Partner.is_active`
  - creación de `Lead` con columnas inexistentes y con `partner_id` nulo en altas sin partner

## Errores típicos
- Partner sin onboarding completo
- comisión en estado no transferible
- tasas/fees mal configuradas
