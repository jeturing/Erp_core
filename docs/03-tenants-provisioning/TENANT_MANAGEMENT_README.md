# TENANT MANAGEMENT README

Estado: vigente
Validado: 2026-02-22
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
- Frontend publico de alta:
  - `#/signup` abre una portada de decision con tres rutas: empresa, firma contable y partner
  - `#/signup?mode=tenant` entra directo al alta de empresa/cliente
  - `#/signup?mode=accountant` entra directo al alta de firma contable
  - `POST /api/checkout` sigue siendo la API de provisionamiento inicial para empresa y firma contable

## Operacion
- ./scripts/create_tenant.sh
- ./scripts/delete_tenant.sh
- ./scripts/list_tenants.sh

## Notas operativas 2026-03-28
- La navegacion publica ahora expone de forma visible la entrada de clientes desde el menu principal (`Clientes`) y deja `Crear empresa` como CTA primaria.
- Los CTAs de pricing ya envian a `#/signup?mode=tenant` para no perder el contexto del plan elegido.
- El flujo contable quedo alineado a `mode=accountant` y reutiliza `POST /api/checkout` con `is_accountant=true` en el payload.

## Referencias
- `README.md`
- `docs/INDICE.md`
- `app/routes/tenants.py`
