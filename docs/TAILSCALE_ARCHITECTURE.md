# TAILSCALE ARCHITECTURE

Estado: vigente
Validado: 2026-02-14
Entorno objetivo: `/opt/Erp_core` (PCT160)
Dominio: Infraestructura

## Objetivo
Documento de referencia para infraestructura.

## Estado actual
Contenido reescrito para alinear rutas, APIs y procesos con la implementacion activa.
No incluye contratos inventados ni paths obsoletos fuera de `/opt/Erp_core`.

## Rutas y APIs vigentes
- GET /api/nodes
- GET /api/nodes/status
- GET /api/nodes/metrics/summary
- GET /api/nodes/containers/all

## Operacion
- Monitoreo via app/services/resource_monitor.py
- Operaciones de nodos via app/routes/nodes.py

## Referencias
- `README.md`
- `docs/INDICE.md`
