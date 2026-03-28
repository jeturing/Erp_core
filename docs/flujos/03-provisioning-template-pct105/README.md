# 03 - Provisioning con template en PCT105

Estado: vigente  
Validado: 2026-03-28  
Entorno objetivo: `/opt/Erp_core`


## Objetivo
Crear un tenant nuevo clonando `template_tenant` en PostgreSQL/Odoo del servidor PCT105,
con DNS automático en Cloudflare, módulos Odoo instalados, y opcionalmente dominio custom.

## Runtime config
- En `app/routes/provisioning.py`, las claves críticas ya se leen en runtime desde `system_config` con fallback a `.env`.
- Incluye: `PROVISIONING_API_KEY`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONES`, `CLOUDFLARE_TUNNEL_ID`, `ODOO_EXTRA_NODES_JSON`, `ODOO_PRIMARY_*`, `ODOO_DB_*`.
- Cambios en esas claves aplican sin reinicio para las rutas ya migradas.

## Servicios Involucrados (PCT105)

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `odoo.service` | 8069 | Odoo 17 Multi-Tenant |
| `odoo-local-api.service` | 8070 | API REST de provisioning local |
| `odoo-db-watcher.service` | — | Monitor de BDs → auto-DNS Cloudflare |
| `cloudflared-tcs-sajet-tunnel` | — | Tunnel `*.sajet.us` → localhost:8443 |
| `nginx` | 8443/8080 | Reverse proxy SSL con routing multi-tenant |

## Flujo Principal: Via API (PCT160 → PCT105)

```text
                          ┌─────────────────────────────┐
                          │  SPA  https://sajet.us/#/    │
                          │  POST /api/tenants           │
                          └──────────┬──────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │ PCT160 (10.10.10.20:4443)       │
                    │ tenants.py:create_tenant         │
                    │  ├─ use_fast_method=true         │
                    │  └─ calls odoo_database_manager  │
                    └────────────────┬────────────────┘
                                     │ pct exec 105
                    ┌────────────────▼────────────────┐
                    │ PCT105 PostgreSQL (10.10.10.100) │
                    │                                  │
                    │ 1. Validar subdomain único       │
                    │ 2. Verificar template_tenant     │
                    │ 3. pg_terminate_backend(template) │
                    │ 4. CREATE DATABASE "new"          │
                    │    WITH TEMPLATE "template_tenant"│
                    │ 5. UPDATE res_company SET name    │
                    │ 6. UPDATE web.base.url            │
                    │ 7. gen_random_uuid() → db.uuid    │
                    └────────────────┬────────────────┘
                                     │
              ┌──────────────────────▼───────────────────────┐
              │ DB Watcher detecta nueva BD cada 10 seg.     │
              │                                              │
              │  → Cloudflare API: crear CNAME               │
              │    <subdomain>.sajet.us →                     │
              │    da2bc763...cfargotunnel.com                │
              │                                              │
              │ El wildcard *.sajet.us en el tunnel           │
              │ ya enruta cualquier subdominio nuevo          │
              │ al Nginx en localhost:8443                    │
              └──────────────────────┬───────────────────────┘
                                     │
              ┌──────────────────────▼───────────────────────┐
              │ Nginx (PCT105) resuelve BD por hostname:     │
              │  map: ~^([a-z0-9-]+)\.sajet\.us$ → $1        │
              │  proxy_pass → http://127.0.0.1:8069          │
              │  Odoo dbfilter=^%d$ selecciona la BD         │
              └──────────────────────────────────────────────┘
```

## Flujo Alternativo: Via API Local directa (PCT105:8070)

```bash
curl -X POST http://10.10.10.100:8070/api/tenant \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "mi_tenant",
    "admin_password": "321Abcd.",
    "domain": "sajet.us",
    "template_db": "template_tenant"
  }'
```

## Instalación de Módulos Post-Provisioning

```bash
pct exec 105 -- su -s /bin/bash odoo -c \
  "/opt/odoo/odoo-bin -c /etc/odoo/odoo.conf \
   -d <subdomain> -i <modulo> \
   --without-demo all --no-http --stop-after-init"
```

## Caso Real: Cliente joficreditosrd (Feb 2026)

| Campo | Valor |
|-------|-------|
| **Subdomain** | joficreditosrd |
| **Empresa** | Jofi Creditos RD |
| **URL sajet** | https://joficreditosrd.sajet.us |
| **URL custom** | https://joficreditosrd.com (pendiente DNS cliente) |
| **Admin 1** | admin@sajet.us / 321Abcd. |
| **Admin 2** | Admin@joficreditosrd.com / 321Abcd. |
| **Módulo** | jeturing_finance_core (Loan Management) |
| **Template** | template_tenant (sin datos demo) |

### Pasos ejecutados
1. POST /api/tenant → duplicó template_tenant → BD joficreditosrd
2. DNS CNAME joficreditosrd.sajet.us creado automáticamente
3. SQL: empresa, web.base.url, database.uuid, mail.catchall.domain
4. Usuario Admin@joficreditosrd.com con permisos admin (22 grupos)
5. Módulo jeturing_finance_core copiado e instalado sin demo
6. Dominio joficreditosrd.com en tunnel config + Nginx maps

## Dominio Custom

### 1. Tunnel (`/etc/cloudflared/tcs-sajet-tunnel.yml`)
```yaml
  - hostname: "joficreditosrd.com"
    service: https://localhost:8443
    originRequest:
      noTLSVerify: true
```

### 2. Nginx maps
```nginx
map $host $tenant_db {
    joficreditosrd.com joficreditosrd;
}
map $host $odoo_proxy_host {
    joficreditosrd.com joficreditosrd.sajet.us;
}
```

### 3. DNS del cliente
```
joficreditosrd.com A → 208.115.125.29
```

## Regla vigente para dominios custom

- Dominio externo del cliente: termina en PCT 160 (`208.115.125.29`).
- Dominio interno SAJET del tenant: sigue usando `*.sajet.us` y túnel Cloudflare donde aplique.
- No recomendar `CNAME` externo a `tenant.sajet.us`.
- No recomendar `CNAME` externo a `*.cfargotunnel.com`.

## DB Watcher

```text
┌────────────────────────────┐
│ odoo-db-watcher.py (loop)  │
│  while True:               │
│    current = pg_database   │
│    new = current - known   │
│    for db in new:          │
│      → CF API: CNAME       │
│    save_state()            │
│    sleep(10)               │
└────────────────────────────┘
```

## Errores Típicos
| Error | Causa | Solución |
|-------|-------|----------|
| Template no existe | BD eliminada | Recrear desde backup |
| BD ya existe | Duplicado | Usar otro nombre |
| no pg_hba.conf entry | Firewall PG | Agregar subnet |
| DNS already exists | CNAME previo | Se reutiliza, no es error |
| Cloudflare no configurado | Token vacío | `/opt/odoo/config/domains.json` |
| Dominio externo 404 en apex | Se publicó CNAME a tunnel/tenant interno | Corregir a `A -> 208.115.125.29` |

## Validación
```bash
# BD existe
pct exec 105 -- sudo -u postgres psql -lqt | grep <subdomain>
# Módulo instalado
pct exec 105 -- bash -c 'PGPASSWORD="123Abcd." psql -h 127.0.0.1 -U Jeturing -d <subdomain> -t -c "SELECT name,state FROM ir_module_module WHERE name LIKE '\''jeturing%'\''"'
# URL accesible
curl -sk -o /dev/null -w "%{http_code}" https://<subdomain>.sajet.us/web/login
# Watcher activo
pct exec 105 -- systemctl status odoo-db-watcher
```
