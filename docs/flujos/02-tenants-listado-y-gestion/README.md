# 02 - Tenants: listado y gestión

## Objetivo
Mostrar tenants en la SPA y ejecutar operaciones de creación, suspensión, cambio de password y borrado.

## Disparador
- Frontend: `#/tenants`
- API principal: `GET /api/tenants`

## Secuencia ASCII (listado)

```text
[SPA Tenants.svelte onMount]
      |
      | GET /api/tenants
      v
[tenants.py:list_tenants]
      |
      +--> get_all_tenants_from_servers()
      |      +--> Odoo /web/database/list
      |      +--> fallback PostgreSQL directo (PCT105)
      |
      +--> merge/fallback local (customers/subscriptions)
      v
[items[], total]
      |
      v
[Tabla Tenants en SPA]
```

## Secuencia ASCII (acciones)

```text
Crear tenant:
SPA -> POST /api/tenants -> create_tenant() -> service -> respuesta -> reload list

Suspender/reactivar:
SPA -> PUT /api/provisioning/tenant/suspend -> estado -> reload list

Cambiar password:
SPA -> PUT /api/provisioning/tenant/password -> resultado

Eliminar:
SPA -> DELETE /api/tenants/{subdomain}?confirm=true -> cleanup -> reload
```

## Endpoints
- `GET /api/tenants`
- `POST /api/tenants`
- `GET /api/tenants/{subdomain}`
- `DELETE /api/tenants/{subdomain}`
- `PUT /api/provisioning/tenant/password`
- `PUT /api/provisioning/tenant/suspend`

## Errores típicos
- Lista vacía por fallo de Odoo list -> mitigado con fallback.
- `BD ya existe` al crear tenant.
- `400 confirm=true requerido` al eliminar.
