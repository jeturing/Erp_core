# 🚀 PR Tracker — Onboarding SaaS Sajet.us
# Auto-generado y actualizado por cada épica completada
# Rama: onboarding | Base: main

## Estado General
- **Inicio**: 2026-02-18
- **Rama**: `onboarding`
- **Stripe Mode**: TEST (sk_test_51G0K5CB1h7Ho...)
- **DB**: PostgreSQL erp_core_db (10.10.10.137 / 10.10.10.20)

---

## Épicas

| # | Épica | Estado | Fecha | Archivos Clave |
|---|-------|--------|-------|----------------|
| 0 | Setup: Rama + Alembic + Tracker | ⬜ pendiente | — | alembic/, .env.test |
| 1 | Billing Mode + Tenant Origin Rules | ⬜ pendiente | — | models/database.py, routes/onboarding.py |
| 2 | Blueprints / Module Packages | ⬜ pendiente | — | routes/blueprints.py, scripts/seed_module_catalog.py |
| 3 | Seats Direct (HWM + Stripe qty) | ⬜ pendiente | — | routes/seats.py |
| 4 | Seats Partner (metered + grace 8h) | ⬜ pendiente | — | routes/seats.py |
| 5 | Invoices (TENANT_READY + intercompany) | ⬜ pendiente | — | routes/invoices.py |
| 6 | Settlement 50/50 + offsets | ⬜ pendiente | — | routes/settlements.py |
| 7 | Stripe Reconciliation + Assets | ⬜ pendiente | — | routes/reconciliation.py, services/stripe_reconciliation.py |
| 8 | Domains temprano + no bloqueante | ⬜ pendiente | — | routes/domains.py |
| 9 | Work Orders + gating | ⬜ pendiente | — | routes/work_orders.py |
| 10 | Auditoría persistente + White-label | ⬜ pendiente | — | security/audit.py, routes/branding.py |
| T | Tests Unitarios | ⬜ pendiente | — | tests/ |
| D | Merge + Deploy | ⬜ pendiente | — | — |

---

## Commits
<!-- Se actualiza con cada commit -->
