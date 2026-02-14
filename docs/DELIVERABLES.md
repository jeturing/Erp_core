# DELIVERABLES

Estado: vigente
Validado: 2026-02-14
Entorno objetivo: `/opt/Erp_core` (PCT160)
Dominio: Deploy/Operacion

## Objetivo
Matriz de entregables de frontend, backend y operacion.

## Estado actual
Contenido reescrito para alinear rutas, APIs y procesos con la implementacion activa.
No incluye contratos inventados ni paths obsoletos fuera de `/opt/Erp_core`.

## Rutas y APIs vigentes
- GET /health
- GET /admin
- GET /tenant/portal
- POST /api/auth/login

## Operacion
- ./scripts/deploy_to_server.sh --profile pct160
- APP_SERVICE para restart remoto

## Referencias
- `README.md`
- `docs/INDICE.md`
- `scripts/deploy_to_server.sh`
