# TENANT MANAGEMENT README

Estado: vigente
Validado: 2026-02-14
Entorno objetivo: `/opt/Erp_core` (PCT160)
Dominio: Tenants/Provisioning

## Objetivo
Documento de referencia para tenants/provisioning.

## Estado actual
Contenido reescrito para alinear rutas, APIs y procesos con la implementacion activa.
No incluye contratos inventados ni paths obsoletos fuera de `/opt/Erp_core`.

## Rutas y APIs vigentes
- GET /api/tenants
- POST /api/tenants
- PUT /api/provisioning/tenant/password
- PUT /api/provisioning/tenant/suspend
- DELETE /api/tenants/{subdomain}?confirm=true

## Operacion
- ./scripts/create_tenant.sh
- ./scripts/delete_tenant.sh
- ./scripts/list_tenants.sh

## Referencias
- `README.md`
- `docs/INDICE.md`
- `app/routes/tenants.py`
