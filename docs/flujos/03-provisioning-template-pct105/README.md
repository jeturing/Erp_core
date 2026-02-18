# 03 - Provisioning con template en PCT105

## Objetivo
Crear un tenant nuevo clonando `template_tenant` en PostgreSQL/Odoo del servidor 105.

## Disparador
- `POST /api/tenants` con `use_fast_method=true`

## Secuencia ASCII

```text
[SPA #/tenants]
   |
   | POST /api/tenants
   v
[tenants.py:create_tenant]
   |
   | use_fast_method=true
   v
[odoo_database_manager.py:create_tenant_from_template]
   |
   +--> validar subdomain
   +--> check BD destino no exista
   +--> check template_tenant exista
   +--> terminar conexiones al template
   +--> CREATE DATABASE <new> WITH TEMPLATE <template_tenant>
   +--> SQL post-config (company, web.base.url, uuid)
   v
[PCT105 PostgreSQL]
   |
   v
[Registro local en customers/subscriptions]
   |
   v
[success -> frontend reload]
```

## Dependencias de infraestructura
- PCT160 (`10.10.10.20`) con acceso a PostgreSQL en PCT105 (`10.10.10.100:5432`)
- `pg_hba.conf` debe permitir subnet `10.10.10.0/24` (md5)
- Variable `ODOO_TEMPLATE_DB=template_tenant`

## Errores típicos
- `Template 'template_tenant' no existe`
- `BD '<subdomain>' ya existe`
- `no pg_hba.conf entry ...` (bloqueo de red/ACL)

## Validación
- `GET /api/tenants` muestra nuevo subdomain
- `url` generado: `https://<subdomain>.sajet.us`
