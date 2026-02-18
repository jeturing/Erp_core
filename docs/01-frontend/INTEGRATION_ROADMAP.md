# INTEGRATION ROADMAP

Estado: vigente
Validado: 2026-02-14
Entorno objetivo: `/opt/Erp_core` (PCT160)
Dominio: Frontend SPA

## Objetivo
Documento de referencia para frontend spa.

## Estado actual
Contenido reescrito para alinear rutas, APIs y procesos con la implementacion activa.
No incluye contratos inventados ni paths obsoletos fuera de `/opt/Erp_core`.

## Rutas y APIs vigentes
- GET /admin
- GET /tenant/portal
- GET /api/dashboard/metrics
- GET /api/tenants
- GET /api/domains
- GET /api/nodes
- GET /api/billing/metrics
- GET /api/settings

## Operacion
- ./scripts/build_static.sh
- ./scripts/smoke_pct160.sh

## Referencias
- `README.md`
- `docs/INDICE.md`
- `frontend/src/App.svelte`
