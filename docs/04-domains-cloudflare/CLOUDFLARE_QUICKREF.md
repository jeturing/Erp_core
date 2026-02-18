# CLOUDFLARE QUICKREF

Estado: vigente
Validado: 2026-02-14
Entorno objetivo: `/opt/Erp_core` (PCT160)
Dominio: Domains/Cloudflare

## Objetivo
Documento de referencia para domains/cloudflare.

## Estado actual
Contenido reescrito para alinear rutas, APIs y procesos con la implementacion activa.
No incluye contratos inventados ni paths obsoletos fuera de `/opt/Erp_core`.

## Rutas y APIs vigentes
- GET /api/domains
- POST /api/domains
- POST /api/domains/{id}/verify
- POST /api/domains/{id}/activate
- POST /api/domains/{id}/deactivate
- POST /api/domains/{id}/configure-cloudflare
- GET /api/domains/my-domains

## Operacion
- ./scripts/domain_sync.sh
- ./scripts/migrate_custom_domains.py

## Referencias
- `README.md`
- `docs/INDICE.md`
- `app/routes/domains.py`
