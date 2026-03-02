# PR Tracker - ERP Core

Estado: vigente  
Validado: 2026-02-22  
Base branch recomendada: `main`

## Objetivo

Registro operativo de epicas y entregables consolidados en el backend SaaS de ERP Core.

## Estado general

- Epicas funcionales principales: completadas
- Endpoints SaaS Billing/Partner: activos en `app/main.py`
- Deuda operativa abierta: mantenimiento de documentacion, pruebas E2E y hardening continuo

## Epicas clave (resumen)

| Epica | Estado | Artefactos principales |
|---|---|---|
| Blueprints / catalogo de modulos | Completada | `app/routes/blueprints.py` |
| Seats y sync de cantidades | Completada | `app/routes/seats.py` |
| Invoices / settlements / reconciliation | Completada | `app/routes/invoices.py`, `app/routes/settlements.py`, `app/routes/reconciliation.py` |
| Work orders y gating | Completada | `app/routes/work_orders.py` |
| Branding + auditoria | Completada | `app/routes/branding.py`, `app/routes/audit.py` |
| Customer onboarding configurable | Completada | `app/routes/customer_onboarding.py`, `app/routes/onboarding_config.py` |

## Pendientes operativos

- Ejecutar regression suite completa antes de cada release mayor
- Mantener sincronia entre docs funcionales y rutas activas
- Revisar estado de scripts legacy antes de automatizarlos en CI

## Referencias

- `README.md`
- `docs/INDICE.md`
- `app/main.py`
