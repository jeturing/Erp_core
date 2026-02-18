# ROLES PERMISOS MATRIZ

Estado: deprecado
Validado: 2026-02-14
Entorno objetivo: `/opt/Erp_core` (PCT160)
Dominio: Auth/Security

## Objetivo
Documento de referencia para auth/security.

## Estado actual
Este documento se conserva por trazabilidad historica y no representa el flujo operativo actual.
Para la operacion vigente usar `README.md` y `docs/INDICE.md`.

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
