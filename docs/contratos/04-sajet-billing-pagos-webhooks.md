# Contratos SAJET — Billing, Pagos y Webhooks

Estado: vigente  
Validado: 2026-03-27  
Fuente de verdad: `app.main`, routers FastAPI en `app/routes/` y OpenAPI runtime.

Contratos financieros, de pago, facturación, conciliación y webhooks externos que afectan dinero o metering.

## Cobertura

- Contratos unicos documentados en este archivo: **96**
- Registros duplicados detectados en runtime dentro de este dominio: **30**
- Los duplicados se marcan en la columna `estado` para no inflar el inventario.

## Entradas y salidas

### `/webhook/stripe`

- Entrada: body firmado por Stripe y header `stripe-signature`.
- Salida: persistencia de `StripeEvent`, creación/actualización de `Subscription` y disparo de provisioning/tunnel lifecycle.

### `/api/mercury/webhook`

- Entrada: body webhook + `X-Mercury-Signature`.
- Salida: conciliación de pagos directos vía `PaymentProcessor.reconcile_direct_payment_webhook(payload)`.

### `/api/v1/webhooks/postal-delivery`

- Entrada: JSON Postal + `X-Postal-Signature`.
- Salida: actualización de consumo/costo de correo por tenant.

### `/api/plans`, `/api/invoices`, `/api/payments`, `/api/seats`

- Entrada: admin JWT o headers operativos según router.
- Salida: pricing, facturación, pago, reconciliación, payouts, seats y treasury.

## Inventario /api/billing

Contratos unicos en este grupo: **4**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/billing/comparison | cookie JWT / rol aplicado | frontend/admin | FastAPI → billing.py | app/routes/billing.py | admin | activo |
| GET | /api/billing/invoices | cookie JWT / rol aplicado | frontend/admin | FastAPI → billing.py | app/routes/billing.py | admin | activo |
| GET | /api/billing/metrics | cookie JWT / rol aplicado | frontend/admin | FastAPI → billing.py | app/routes/billing.py | admin | activo |
| GET | /api/billing/stripe-events | cookie JWT / rol aplicado | frontend/admin | FastAPI → billing.py | app/routes/billing.py | admin | activo |

## Inventario /api/checkout

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/checkout | cookie JWT / rol aplicado | frontend/admin | FastAPI → onboarding.py | app/routes/onboarding.py | admin | activo |

## Inventario /api/commissions

Contratos unicos en este grupo: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/commissions | cookie JWT / rol aplicado | frontend/admin | FastAPI → commissions.py | app/routes/commissions.py | admin | activo |
| POST | /api/commissions | cookie JWT / rol aplicado | frontend/admin | FastAPI → commissions.py | app/routes/commissions.py | admin | activo |
| GET | /api/commissions/{commission_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → commissions.py | app/routes/commissions.py | admin | activo |
| PUT | /api/commissions/{commission_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → commissions.py | app/routes/commissions.py | admin | activo |
| POST | /api/commissions/{commission_id}/approve | cookie JWT / rol aplicado | frontend/admin | FastAPI → commissions.py | app/routes/commissions.py | admin | activo |
| POST | /api/commissions/{commission_id}/pay | cookie JWT / rol aplicado | frontend/admin | FastAPI → commissions.py | app/routes/commissions.py | admin | activo |

## Inventario /api/dispersion

Contratos unicos en este grupo: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/dispersion/feature-flag | cookie JWT / rol aplicado | frontend/admin | FastAPI → dispersion.py | app/routes/dispersion.py | admin | activo; registro duplicado x2 |
| GET | /api/dispersion/payouts | cookie JWT / rol aplicado | frontend/admin | FastAPI → dispersion.py | app/routes/dispersion.py | admin | activo; registro duplicado x2 |
| POST | /api/dispersion/payouts/authorize | cookie JWT / rol aplicado | frontend/admin | FastAPI → dispersion.py | app/routes/dispersion.py | admin | activo; registro duplicado x2 |
| POST | /api/dispersion/payouts/create | cookie JWT / rol aplicado | frontend/admin | FastAPI → dispersion.py | app/routes/dispersion.py | admin | activo; registro duplicado x2 |
| POST | /api/dispersion/payouts/reject | cookie JWT / rol aplicado | frontend/admin | FastAPI → dispersion.py | app/routes/dispersion.py | admin | activo; registro duplicado x2 |
| GET | /api/dispersion/status | cookie JWT / rol aplicado | frontend/admin | FastAPI → dispersion.py | app/routes/dispersion.py | admin | activo; registro duplicado x2 |

## Inventario /api/invoices

Contratos unicos en este grupo: **10**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/invoices | cookie JWT / rol aplicado | frontend/admin | FastAPI → invoices.py | app/routes/invoices.py | admin | activo |
| POST | /api/invoices/change-plan | cookie JWT / rol aplicado | frontend/admin | FastAPI → invoices.py | app/routes/invoices.py | admin | activo |
| POST | /api/invoices/generate-consumption | cookie JWT / rol aplicado | frontend/admin | FastAPI → invoices.py | app/routes/invoices.py | admin | activo |
| POST | /api/invoices/generate-on-ready | cookie JWT / rol aplicado | frontend/admin | FastAPI → invoices.py | app/routes/invoices.py | admin | activo |
| POST | /api/invoices/sync-quantity | cookie JWT / rol aplicado | frontend/admin | FastAPI → invoices.py | app/routes/invoices.py | admin | activo |
| GET | /api/invoices/{invoice_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → invoices.py | app/routes/invoices.py | admin | activo |
| POST | /api/invoices/{invoice_id}/checkout | cookie JWT / rol aplicado | frontend/admin | FastAPI → invoices.py | app/routes/invoices.py | admin | activo |
| POST | /api/invoices/{invoice_id}/mark-paid | cookie JWT / rol aplicado | frontend/admin | FastAPI → invoices.py | app/routes/invoices.py | admin | activo |
| POST | /api/invoices/{invoice_id}/payment-link | cookie JWT / rol aplicado | frontend/admin | FastAPI → invoices.py | app/routes/invoices.py | admin | activo |
| POST | /api/invoices/{invoice_id}/push-to-stripe | cookie JWT / rol aplicado | frontend/admin | FastAPI → invoices.py | app/routes/invoices.py | admin | activo |

## Inventario /api/mercury

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/mercury/webhook | X-Mercury-Signature | Mercury | FastAPI → mercury_webhooks.py | app/routes/mercury_webhooks.py | webhook | activo; registro duplicado x2 |

## Inventario /api/payments

Contratos unicos en este grupo: **4**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/payments/balance | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| POST | /api/payments/direct/instructions | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| POST | /api/payments/process-invoice | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| GET | /api/payments/summary | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |

## Inventario /api/payouts

Contratos unicos en este grupo: **5**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/payouts | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| POST | /api/payouts/create | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| GET | /api/payouts/{payout_id} | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| POST | /api/payouts/{payout_id}/authorize | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| POST | /api/payouts/{payout_id}/execute | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |

## Inventario /api/plan-migration

Contratos unicos en este grupo: **7**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/plan-migration/auto-migrate | X-API-KEY | automation/ops | FastAPI → plan_migration.py | app/routes/plan_migration.py | admin | activo |
| POST | /api/plan-migration/batch-migrate | X-API-KEY | automation/ops | FastAPI → plan_migration.py | app/routes/plan_migration.py | admin | activo |
| POST | /api/plan-migration/evaluate | X-API-KEY | automation/ops | FastAPI → plan_migration.py | app/routes/plan_migration.py | admin | activo |
| GET | /api/plan-migration/evaluate-all | X-API-KEY | automation/ops | FastAPI → plan_migration.py | app/routes/plan_migration.py | admin | activo |
| GET | /api/plan-migration/plans | X-API-KEY | automation/ops | FastAPI → plan_migration.py | app/routes/plan_migration.py | admin | activo |
| GET | /api/plan-migration/summary | X-API-KEY | automation/ops | FastAPI → plan_migration.py | app/routes/plan_migration.py | admin | activo |
| GET | /api/plan-migration/tenant/{tenant_db}/size | X-API-KEY | automation/ops | FastAPI → plan_migration.py | app/routes/plan_migration.py | admin | activo |

## Inventario /api/plans

Contratos unicos en este grupo: **5**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/plans | cookie JWT / rol aplicado | frontend/admin | FastAPI → plans.py | app/routes/plans.py | admin | activo |
| POST | /api/plans | cookie JWT / rol aplicado | frontend/admin | FastAPI → plans.py | app/routes/plans.py | admin | activo |
| POST | /api/plans/calculate | cookie JWT / rol aplicado | frontend/admin | FastAPI → plans.py | app/routes/plans.py | admin | activo |
| DELETE | /api/plans/{plan_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → plans.py | app/routes/plans.py | admin | activo |
| PUT | /api/plans/{plan_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → plans.py | app/routes/plans.py | admin | activo |

## Inventario /api/providers

Contratos unicos en este grupo: **2**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/providers/accounts | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| POST | /api/providers/kyc-check | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |

## Inventario /api/quotas

Contratos unicos en este grupo: **4**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/quotas | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotas.py | app/routes/quotas.py | admin | activo |
| GET | /api/quotas/{customer_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotas.py | app/routes/quotas.py | admin | activo |
| GET | /api/quotas/{customer_id}/check/{resource} | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotas.py | app/routes/quotas.py | admin | activo |
| GET | /api/quotas/{customer_id}/{resource} | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotas.py | app/routes/quotas.py | admin | activo |

## Inventario /api/reconciliation

Contratos unicos en este grupo: **5**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/reconciliation | cookie JWT / rol aplicado | frontend/admin | FastAPI → reconciliation.py | app/routes/reconciliation.py | legacy | activo; compatibilidad |
| POST | /api/reconciliation/run | cookie JWT / rol aplicado | frontend/admin | FastAPI → reconciliation.py | app/routes/reconciliation.py | admin | activo |
| GET | /api/reconciliation/runs | cookie JWT / rol aplicado | frontend/admin | FastAPI → reconciliation.py | app/routes/reconciliation.py | admin | activo |
| GET | /api/reconciliation/runs/{run_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → reconciliation.py | app/routes/reconciliation.py | admin | activo |
| GET | /api/reconciliation/{run_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → reconciliation.py | app/routes/reconciliation.py | legacy | activo; compatibilidad |

## Inventario /api/reports

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/reports/overview | cookie JWT / rol aplicado | frontend/admin | FastAPI → reports.py | app/routes/reports.py | admin | activo |

## Inventario /api/seats

Contratos unicos en este grupo: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/seats/event | cookie JWT / rol aplicado | frontend/admin | FastAPI → seats.py | app/routes/seats.py | admin | activo |
| GET | /api/seats/hwm | cookie JWT / rol aplicado | frontend/admin | FastAPI → seats.py | app/routes/seats.py | legacy | activo; compatibilidad |
| GET | /api/seats/hwm/{subscription_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → seats.py | app/routes/seats.py | admin | activo |
| GET | /api/seats/summary | cookie JWT / rol aplicado | frontend/admin | FastAPI → seats.py | app/routes/seats.py | legacy | activo; compatibilidad |
| GET | /api/seats/summary/{subscription_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → seats.py | app/routes/seats.py | admin | activo |
| POST | /api/seats/sync-stripe | cookie JWT / rol aplicado | frontend/admin | FastAPI → seats.py | app/routes/seats.py | admin | activo |

## Inventario /api/settlements

Contratos unicos en este grupo: **4**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/settlements | cookie JWT / rol aplicado | frontend/admin | FastAPI → settlements.py | app/routes/settlements.py | admin | activo |
| POST | /api/settlements/create-period | cookie JWT / rol aplicado | frontend/admin | FastAPI → settlements.py | app/routes/settlements.py | admin | activo |
| GET | /api/settlements/{period_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → settlements.py | app/routes/settlements.py | admin | activo |
| POST | /api/settlements/{period_id}/close | cookie JWT / rol aplicado | frontend/admin | FastAPI → settlements.py | app/routes/settlements.py | admin | activo |

## Inventario /api/stripe-connect

Contratos unicos en este grupo: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/stripe-connect/create-account | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_connect.py | app/routes/stripe_connect.py | admin | activo |
| POST | /api/stripe-connect/transfer | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_connect.py | app/routes/stripe_connect.py | admin | activo |
| GET | /api/stripe-connect/{partner_id}/balance | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_connect.py | app/routes/stripe_connect.py | admin | activo |
| GET | /api/stripe-connect/{partner_id}/dashboard-link | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_connect.py | app/routes/stripe_connect.py | admin | activo |
| GET | /api/stripe-connect/{partner_id}/onboarding-link | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_connect.py | app/routes/stripe_connect.py | admin | activo |
| GET | /api/stripe-connect/{partner_id}/status | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_connect.py | app/routes/stripe_connect.py | admin | activo |

## Inventario /api/stripe-sync

Contratos unicos en este grupo: **5**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/stripe-sync/customers | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_sync.py | app/routes/stripe_sync.py | admin | activo; registro duplicado x2 |
| POST | /api/stripe-sync/full | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_sync.py | app/routes/stripe_sync.py | admin | activo; registro duplicado x2 |
| POST | /api/stripe-sync/invoices | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_sync.py | app/routes/stripe_sync.py | admin | activo; registro duplicado x2 |
| GET | /api/stripe-sync/status | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_sync.py | app/routes/stripe_sync.py | admin | activo; registro duplicado x2 |
| POST | /api/stripe-sync/subscriptions | cookie JWT / rol aplicado | frontend/admin | FastAPI → stripe_sync.py | app/routes/stripe_sync.py | admin | activo; registro duplicado x2 |

## Inventario /api/treasury

Contratos unicos en este grupo: **7**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/treasury/accounts/auto-replenish | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| GET | /api/treasury/accounts/dual-status | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| POST | /api/treasury/accounts/transfer-to-checking | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| GET | /api/treasury/alerts | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| GET | /api/treasury/forecast | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| GET | /api/treasury/summary | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |
| GET | /api/treasury/transactions | admin/ops JWT | frontend/admin | FastAPI → payments.py | app/routes/payments.py | admin | activo; registro duplicado x2 |

## Inventario /api/v1

Contratos unicos en este grupo: **4**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/v1/webhooks/postal-delivery | X-Postal-Signature | Postal | FastAPI → postal_webhooks.py | app/routes/postal_webhooks.py | webhook | activo |
| POST | /api/v1/webhooks/postal/sync | X-API-KEY | operacion/admin | FastAPI → postal_webhooks.py | app/routes/postal_webhooks.py | webhook | activo |
| GET | /api/v1/webhooks/postal/usage-summary | X-API-KEY | operacion/admin | FastAPI → postal_webhooks.py | app/routes/postal_webhooks.py | webhook | activo |
| GET | /api/v1/webhooks/postal/usage/{tenant_subdomain} | X-API-KEY | operacion/admin | FastAPI → postal_webhooks.py | app/routes/postal_webhooks.py | webhook | activo |

## Inventario /api/webhooks

Contratos unicos en este grupo: **2**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/webhooks/odoo | X-API-KEY o HMAC | Odoo jeturing_erp_sync | FastAPI → odoo_webhooks.py | app/routes/odoo_webhooks.py | webhook | activo |
| GET | /api/webhooks/odoo/health | X-API-KEY o HMAC | Odoo jeturing_erp_sync | FastAPI → odoo_webhooks.py | app/routes/odoo_webhooks.py | webhook | activo |

## Inventario /webhook

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /webhook/stripe | firma Stripe | Stripe | FastAPI → onboarding.py | app/routes/onboarding.py | webhook | activo |

## Puntos de quiebre

- `onboarding.py`: si falla el webhook Stripe, el pago existe en Stripe pero no aterriza en `Subscription` ni provisioning.
- `mercury_webhooks.py`: firma inválida o payload inesperado rompe conciliación de cobros directos.
- `postal_webhooks.py`: si el secreto no coincide o cambia el esquema del evento, se pierde metering de email por tenant.
- `payments.py`, `invoices.py`, `seats.py`, `reconciliation.py`, `stripe_sync.py`, `dispersion.py`: cualquier desalineación entre `Customer`, `Subscription`, Stripe, Mercury y ledger interno impacta cobro, payout y métricas.

## Observabilidad

- Webhooks críticos: `/webhook/stripe`, `/api/mercury/webhook`, `/api/v1/webhooks/postal-delivery`.
- Rutas admin de conciliación: `/api/reconciliation/*`, `/api/stripe-sync/*`, `/api/invoices/*`, `/api/seats/*`.
- Evidencia operativa: tabla `StripeEvent`, auditoría general y logs del backend.
- Los warnings de OpenAPI por operaciones duplicadas afectan también a `payments.py`, `dispersion.py` y `stripe_sync.py`.
