# 04 - Billing y Stripe

Estado: vigente  
Validado: 2026-03-28  
Entorno objetivo: `/opt/Erp_core`


## Objetivo
Gestionar métricas de facturación, eventos Stripe y operaciones de cobro/suscripción.

## Disparador
- Frontend: `#/billing`
- APIs de billing y webhooks

## Secuencia ASCII (métricas)

```text
[SPA Billing]
   |
   | GET /api/billing/metrics
   | GET /api/billing/invoices
   | GET /api/billing/stripe-events
   v
[billing.py]
   |
   +--> consulta subscriptions/customers
   +--> integra Stripe data
   v
[KPIs + facturas + eventos]
```

## Secuencia ASCII (evento webhook)

```text
[Stripe]
   |
   | POST webhook
   v
[Backend webhook endpoint]
   |
   +--> verifica firma
   +--> guarda stripe_events
   +--> actualiza estado subscription/customer
   v
[Consistencia de billing]
```

## Endpoints relacionados
- `GET /api/billing/metrics`
- `GET /api/billing/invoices`
- `GET /api/billing/stripe-events`
- Endpoints de checkout/onboarding según módulo activo

## Runtime config
- Stripe en onboarding, portal tenant, sync y reconciliación crítica se resuelve en runtime con `get_runtime_setting()`.
- Prioridad efectiva: `system_config` (BD) → `.env` → default.
- Claves migradas: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `APP_URL`.
- Cambios en esas claves aplican sin reinicio en los módulos migrados (`onboarding.py`, `tenant_portal.py`, `stripe_billing.py`, `stripe_connect.py`, `stripe_sync.py`, `reconciliation.py`, `background_scheduler.py`).

## Stripe Connect en onboarding comercial
- Cuando el alta llega con `partner_code` y el partner está en `billing_scenario=jeturing_collects`, el checkout ya no crea un direct charge sobre la cuenta conectada.
- Desde 2026-03-28, el flujo usa `Checkout Session` en la plataforma con `subscription_data.transfer_data.destination` + `application_fee_percent` calculado desde `partner.commission_rate`.
- Si el partner está listo para cobrar localmente (`stripe_charges_enabled=true` y misma jurisdicción de plataforma), el checkout agrega `on_behalf_of` para usar settlement merchant/branding del partner en recursos hosted compatibles.
- Si el partner está en `billing_scenario=partner_collects`, no se monta split automático de Connect en el checkout público; el cobro sigue siendo externo por el partner y la relación financiera con SAJET queda por factura/intercompany.
- El webhook `account.updated` ahora sincroniza `stripe_onboarding_complete` desde el estado real de la cuenta conectada; el `return_url` de Stripe no se considera fuente de verdad final.

## Operación
1. Después de cambiar una credencial Stripe en BD, validar checkout nuevo o `/api/billing/*`.
2. Si falla una tarea programada Stripe, revisar que el scheduler ya esté usando runtime config y no una clave congelada.
3. Si falla un checkout con `partner_code`, verificar primero:
   - partner activo
   - `partner.billing_scenario`
   - `partner.stripe_account_id`
   - `partner.stripe_onboarding_complete`
   - `partner.commission_rate`

## Errores típicos
- `Webhook signature invalid`
- `Stripe API key inválida`
- Desfase entre estado local y Stripe
