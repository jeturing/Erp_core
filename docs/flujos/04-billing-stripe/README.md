# 04 - Billing y Stripe

Estado: vigente  
Validado: 2026-02-22  
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

## Errores típicos
- `Webhook signature invalid`
- `Stripe API key inválida`
- Desfase entre estado local y Stripe
