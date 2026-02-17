# Dominios Externos — Arquitectura Multi-Tenant Odoo

> **Última actualización**: 2026-02-14  
> **Estado**: Vigente  
> **Infraestructura**: Proxmox → LXC Containers (PCT 105, PCT 160)  
> **IP Pública**: `208.115.125.29`

---

## 📐 Diagrama de Arquitectura

```
                         ┌──────────────────┐
                         │   CLOUDFLARE      │
                         │   (SSL termination)│
      impulse-max.com ──►│   A → 208.115.125.29│
      techeels.io     ──►│   Proxied + Full SSL│
      evolucionamujer  ──►│                    │
                         └────────┬───────────┘
                                  │ HTTPS :443
                                  ▼
                    ┌─────────────────────────────┐
                    │  PCT 160 — NGINX Frontend    │
                    │  IP: 10.10.10.1 / :20        │
                    │  Puerto: 443 (SSL) / 80       │
                    │                               │
                    │  ┌──────────────────────┐    │
                    │  │ DOMINIOS EXTERNOS    │    │
                    │  │ Host: $host (original)│    │
                    │  │ proxy_redirect regex  │    │
                    │  │ Backend: CT105:8080   │    │
                    │  └──────────┬───────────┘    │
                    │             │                  │
                    │  ┌──────────────────────┐    │
                    │  │ ORQUESTADOR *.sajet.us│    │
                    │  │ Host: $proxy_odoo_host│    │
                    │  │ Backend: CT105:8069   │    │
                    │  └──────────┬───────────┘    │
                    └─────────────┼────────────────┘
                                  │ HTTP :8080
                                  ▼
                    ┌─────────────────────────────┐
                    │  CT 105 — NGINX + Odoo       │
                    │  IP: 10.10.10.100             │
                    │  Puerto NGINX: 8080           │
                    │  Puerto Odoo:  8069 / 8072    │
                    │                               │
                    │  ┌──────────────────────┐    │
                    │  │ map $odoo_proxy_host  │    │
                    │  │ impulse-max.com →     │    │
                    │  │   techeels.sajet.us   │    │
                    │  └──────────────────────┘    │
                    │                               │
                    │  Host → $odoo_proxy_host      │
                    │  X-Forwarded-Host →            │
                    │    $odoo_proxy_host            │
                    │  proxy_redirect: reescribe    │
                    │    techeels.sajet.us → $host   │
                    │                               │
                    │  ┌──────────────────────┐    │
                    │  │ ODOO 17 CE            │    │
                    │  │ dbfilter = ^%d$       │    │
                    │  │ proxy_mode = True     │    │
                    │  │ Host: techeels.sajet.us│    │
                    │  │ → BD: techeels        │    │
                    │  └──────────────────────┘    │
                    └─────────────────────────────┘
```

---

## 🔑 Concepto Clave: ¿Por qué la Doble Reescritura?

Odoo usa `dbfilter = ^%d$` con `proxy_mode = True`, lo que significa:

1. **Odoo toma el primer segmento** de `X-Forwarded-Host` para crear un regex de filtro de BD
2. `X-Forwarded-Host: techeels.sajet.us` → dbfilter = `^techeels$` → matchea BD `techeels` ✅
3. `X-Forwarded-Host: impulse-max.com` → dbfilter = `^impulse-max$` → **NO matchea** ❌

**Solución**: CT105 nginx reescribe tanto `Host` como `X-Forwarded-Host` al subdominio `*.sajet.us` correspondiente **antes de enviarlo a Odoo**. Luego, `proxy_redirect` reescribe el Location header de vuelta al dominio original.

---

## 📁 Archivos de Configuración

### PCT 160 (Nginx Frontend)

| Archivo | Propósito |
|---------|-----------|
| `/etc/nginx/sites-available/erp` | Config principal: 4 server blocks |
| `/etc/nginx/conf.d/odoo_http_routes.map` | Mapeo dominio → backend HTTP |
| `/etc/nginx/conf.d/odoo_chat_routes.map` | Mapeo dominio → backend WebSocket |
| `/etc/nginx/ssl/onboarding.crt` | Certificado SSL (self-signed, CN=onboarding.local) |
| `/etc/nginx/ssl/onboarding.key` | Clave privada SSL |

### CT 105 (Nginx + Odoo)

| Archivo | Propósito |
|---------|-----------|
| `/etc/nginx/sites-enabled/odoo` | Proxy multi-tenant con maps de Host rewrite |
| `/etc/odoo/odoo.conf` | Config de Odoo (dbfilter, proxy_mode, workers) |
| `/etc/cloudflared/tcs-sajet-tunnel.yml` | Config del tunnel Cloudflare (para *.sajet.us) |

---

## 📋 Dominios Externos Actuales

| Dominio | Tenant (BD) | Subdominio Interno | Estado |
|---------|-------------|-------------------|--------|
| `impulse-max.com` | techeels | techeels.sajet.us | ✅ Activo |
| `www.impulse-max.com` | techeels | techeels.sajet.us | ✅ Activo |
| `techeels.io` | techeels | techeels.sajet.us | ✅ Activo |
| `www.techeels.io` | techeels | techeels.sajet.us | ✅ Activo |
| `evolucionamujer.com` | techeels | techeels.sajet.us | ✅ Activo |
| `www.evolucionamujer.com` | techeels | techeels.sajet.us | ✅ Activo |

---

## 🌐 Configuración DNS en Cloudflare

Para cada dominio externo, en la **zona DNS del dominio** en Cloudflare:

| Tipo | Nombre | Contenido | Proxy |
|------|--------|-----------|-------|
| A | `@` | `208.115.125.29` | 🟧 Proxied |
| A | `www` | `208.115.125.29` | 🟧 Proxied |

### Configuración SSL/TLS de la zona:
- **Modo SSL**: `Full` (NO Full Strict — el origen usa certificado self-signed)
- **Minimum TLS Version**: 1.2
- **Always Use HTTPS**: ON

> ⚠️ **IMPORTANTE**: No usar CNAME apuntando a `*.sajet.us` ni al tunnel UUID. Esto causa:
> - CNAME → `techeels.sajet.us` (proxied): HTTP **403** (proxy-to-proxy conflict)
> - CNAME → `UUID.cfargotunnel.com`: HTTP **530** (cross-zone tunnel limitation)

---

## 📊 Flujo de una Petición

```
Usuario visita: https://impulse-max.com/web

 1. DNS: impulse-max.com → A 208.115.125.29 (Cloudflare Proxied)
 2. Cloudflare: Termina SSL del cliente, conecta HTTPS:443 → 208.115.125.29
 3. PCT160: Server "DOMINIOS EXTERNOS" captura impulse-max.com
    - location = /web → return 302 /web?db=techeels
 4. Cloudflare reenvía redirect al cliente
 5. Cliente: GET https://impulse-max.com/web?db=techeels
 6. PCT160: location = /web (con $arg_db presente)
    - proxy_pass http://10.10.10.100:8080
    - Host: impulse-max.com (dominio original)
    - X-Forwarded-Host: impulse-max.com
 7. CT105 nginx (:8080):
    - $host = impulse-max.com
    - $odoo_proxy_host = techeels.sajet.us (via map)
    - proxy_set_header Host techeels.sajet.us
    - proxy_set_header X-Forwarded-Host techeels.sajet.us
    - proxy_pass http://127.0.0.1:8069
 8. Odoo:
    - X-Forwarded-Host: techeels.sajet.us (proxy_mode=True)
    - dbfilter: ^techeels$ → BD: techeels ✅
    - Genera: Location: http://techeels.sajet.us/web/login?db=techeels
 9. CT105 nginx (proxy_redirect):
    - Reescribe: techeels.sajet.us → impulse-max.com
    - Location: https://impulse-max.com/web/login?db=techeels
10. PCT160 (proxy_redirect regex):
    - Reescribe cualquier subdominio restante → $host
    - Location: https://impulse-max.com/web/login?db=techeels ✅
11. Cliente: renderiza la página de login de Techeels
```

---

## ⚙️ Server Blocks en PCT 160

| # | Nombre | server_name | Puerto | Función |
|---|--------|-------------|--------|---------|
| 1 | APP CENTRAL | `sajet.us www.sajet.us` | 443 | Landing page + FastAPI (ERP Core) |
| 2 | DOMINIOS EXTERNOS | `techeels.io impulse-max.com evolucionamujer.com ...` | 443, 80 | Proxy a CT105:8080 para tenants Odoo |
| 3 | ORQUESTADOR | `_` (default_server) | 443 | Proxy multi-nodo para `*.sajet.us` → Odoo |
| 4 | HTTP REDIRECT | `_` | 80 | Redirect HTTP → HTTPS |

---

## 🔧 Configuración de Odoo

```ini
# /etc/odoo/odoo.conf (CT105)
dbfilter = ^%d$      # Primer segmento del Host = nombre de BD
proxy_mode = True    # Usa X-Forwarded-Host en vez de Host
list_db = False      # No listar BDs públicamente
db_name = False      # Sin BD predeterminada
workers = 4
```

---

## 🛡️ Seguridad

- `/web/database/manager`, `/web/database/selector`, `/web/database/list`: Restringidos a `127.0.0.1` y `10.10.10.0/24` en ambos nginx
- SSL terminado en Cloudflare con modo "Full"
- Certificado self-signed en PCT160 (aceptado por Cloudflare en modo Full)
- `list_db = False` previene enumeración de bases de datos

---

## 📝 Notas Técnicas

### ¿Por qué no usar Cloudflare Tunnel para dominios externos?
El tunnel `tcs-sajet-tunnel` funciona para `*.sajet.us` porque la zona DNS de `sajet.us` está en la misma cuenta Cloudflare. Para dominios en **otras zonas DNS**, el tunnel requiere registro explícito en el dashboard de Zero Trust (no basta con config.yml local), lo que es más complejo y frágil. La solución de A record es más simple y confiable.

### ¿Por qué `proxy_mode = True` complica las cosas?
Odoo con `proxy_mode = True` ignora el header `Host` y usa `X-Forwarded-Host` para determinar el hostname. Esto significa que **ambos headers** (Host y X-Forwarded-Host) deben ser reescritos a `techeels.sajet.us` antes de llegar a Odoo. Si solo se reescribe `Host` pero no `X-Forwarded-Host`, Odoo verá el dominio externo original y no podrá resolver la BD.

### Diferencia de flujo: *.sajet.us vs dominios externos
- **`techeels.sajet.us`**: PCT160 (orquestador) → CT105:8069 (Odoo directo). El Host ya es correcto para dbfilter.
- **`impulse-max.com`**: PCT160 (dominios externos) → CT105:8080 (nginx) → CT105:8069 (Odoo). El paso extra por nginx (:8080) es necesario para la reescritura de Host/X-Forwarded-Host y proxy_redirect.

---

## Rutas y APIs vigentes (ERP Core)
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
- `docs/CUSTOM_DOMAINS_HOWTO.md`
- `app/routes/domains.py`
