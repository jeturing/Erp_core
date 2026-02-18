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
| 0 | Setup: Rama + Alembic + Tracker | ✅ completado | 2026-02-18 | alembic/, .env.test |
| 1 | Billing Mode + Tenant Origin Rules | ✅ completado | 2026-02-18 | models/database.py (28 tables, 22 enums) |
| 2 | Blueprints / Module Packages | ✅ completado | 2026-02-18 | routes/blueprints.py (7 endpoints) |
| 3 | Seats Direct (HWM + Stripe qty) | ✅ completado | 2026-02-18 | routes/seats.py (4 endpoints) |
| 4 | Seats Partner (metered + grace 8h) | ✅ completado | 2026-02-18 | routes/seats.py (integrated) |
| 5 | Invoices (TENANT_READY + intercompany) | ✅ completado | 2026-02-18 | routes/invoices.py (4 endpoints) |
| 6 | Settlement 50/50 + offsets | ✅ completado | 2026-02-18 | routes/settlements.py (4 endpoints) |
| 7 | Stripe Reconciliation + Assets | ✅ completado | 2026-02-18 | routes/reconciliation.py, services/stripe_reconciliation.py |
| 8 | Domains temprano + no bloqueante | ⬜ pendiente | — | routes/domains.py (update) |
| 9 | Work Orders + gating | ✅ completado | 2026-02-18 | routes/work_orders.py (4 endpoints) |
| 10 | Auditoría persistente + White-label | ✅ completado | 2026-02-18 | routes/audit.py, routes/branding.py (8 endpoints) |
| T | Tests Unitarios | ⬜ pendiente | — | tests/ |
| D | Merge + Deploy | ⬜ pendiente | — | — |

---

## Commits
<!-- Se actualiza con cada commit -->
| Hash | Mensaje | Archivos |
|------|---------|----------|
| 7059d92 | epic-0: Alembic setup + tracker + .env.test | 8 files |
| bcc8b12 | feat: Blueprints, Invoices, Seats, Settlements routes + migration + models | 7 files, 2453 insertions |
| e738a4f | feat(epic1): Reconciliation, Work Orders, Branding, Audit + register routers | 6 files, 816 insertions |

## Resumen de Endpoints Nuevos (34 total)
- `/api/blueprints/*` — 7 endpoints (Catálogo módulos + paquetes CRUD)
- `/api/seats/*` — 4 endpoints (Events, HWM, Stripe sync, Summary)
- `/api/invoices/*` — 4 endpoints (Generate, List, Detail, Mark-paid)
- `/api/settlements/*` — 4 endpoints (Create, List, Detail, Close)
- `/api/reconciliation/*` — 3 endpoints (Run, History, Detail)
- `/api/work-orders/*` — 4 endpoints (CRUD + gating status)
- `/api/branding/*` — 5 endpoints (Profiles CRUD + domain resolve)
- `/api/audit/*` — 3 endpoints (Log, List, Detail)
