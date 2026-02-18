# JWT IMPLEMENTATION SUMMARY

Estado: vigente
Validado: 2026-02-14
Entorno objetivo: `/opt/Erp_core` (PCT160)
Dominio: Auth/Security

## Objetivo
Documento de referencia para auth/security.

## Estado actual
Contenido reescrito para alinear rutas, APIs y procesos con la implementacion activa.
No incluye contratos inventados ni paths obsoletos fuera de `/opt/Erp_core`.

## Rutas y APIs vigentes
- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/refresh
- POST /api/auth/logout
- GET /login/admin
- GET /login/tenant

## Operacion
- Variables ADMIN_USERNAME/ADMIN_PASSWORD en .env
- Cookies access_token/refresh_token

## Referencias
- `README.md`
- `docs/INDICE.md`
- `app/routes/secure_auth.py`
