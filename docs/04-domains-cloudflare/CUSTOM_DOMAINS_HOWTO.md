# Guía: Agregar un Nuevo Dominio Externo a un Tenant Odoo

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


> **Última actualización**: 2026-02-14  
> **Pre-requisito**: Leer `CUSTOM_DOMAINS_ARCHITECTURE.md` para entender la arquitectura

---

## 🤖 Método Automatizado (Recomendado)

Desde la versión actual, la app FastAPI en PCT160 configura nginx **automáticamente**
al activar un dominio via API.

### Flujo automático:

1. **Crear dominio** en la app:
   ```
   POST /api/domains
   { "external_domain": "midominio.com", "customer_id": 1, "tenant_deployment_id": 5 }
   ```

2. **Configurar Cloudflare** (DNS del dominio externo):
   ```
   POST /api/domains/{id}/configure-cloudflare
   ```

3. **Activar dominio** — nginx se configura automáticamente:
   ```
   POST /api/domains/{id}/activate
   ```
   Esto edita nginx en PCT160 (local) y CT105 (via SSH) automáticamente.

4. **Verificar estado nginx**:
   ```
   GET /api/domains/{id}/nginx-status
   ```

### Endpoints adicionales:

| Endpoint | Descripción |
|----------|-------------|
| `POST /api/domains/{id}/configure-nginx` | Re-aplicar configuración nginx manualmente |
| `POST /api/domains/{id}/deactivate` | Desactiva dominio + elimina config nginx |
| `POST /api/domains/bulk/sync-nginx` | Configura nginx para todos los dominios activos sin config |
| `GET /api/domains/{id}/nginx-status` | Verifica si nginx está configurado en ambos servidores |

### Fallback automático:

El script `/opt/Erp_core/scripts/nginx_sync.py` (cron cada 5 min) detecta dominios
activos sin `nginx_configured` y los configura automáticamente.

```bash
# Agregar a cron de PCT160:
*/5 * * * * /opt/Erp_core/venv/bin/python3 /opt/Erp_core/scripts/nginx_sync.py >> /var/log/nginx_sync.log 2>&1
```

### Requisitos:
- SSH sin contraseña desde PCT160 → CT105 (`ssh root@10.10.10.100`)
- nginx instalado y corriendo en ambos servidores

---

## 📋 Método Manual (Referencia)

Para que `midominio.com` apunte al tenant `mi_tenant` en Odoo:

1. **Cloudflare**: Crear A record en la zona del dominio
2. **PCT 160**: Actualizar nginx (maps + server_name + route maps)
3. **CT 105**: Actualizar nginx (maps)
4. **Verificar**: Probar con curl --resolve

---

## Paso 1: DNS en Cloudflare

En el dashboard de Cloudflare, ir a la **zona DNS de `midominio.com`**:

| Tipo | Nombre | Contenido | Proxy |
|------|--------|-----------|-------|
| A | `@` | `208.115.125.29` | 🟧 Proxied |
| A | `www` | `208.115.125.29` | 🟧 Proxied |

En **SSL/TLS** → Overview:
- Modo: **Full** (NO Full Strict)

---

## Paso 2: Actualizar PCT 160

### 2.1 — `/etc/nginx/sites-available/erp`

Editar 4 secciones:

#### A) Map `$external_tenant_db` — agregar:
```nginx
    midominio.com        mi_tenant;
    www.midominio.com    mi_tenant;
```

#### B) Map `$external_odoo_host` — agregar:
```nginx
    midominio.com        mi_tenant.sajet.us;
    www.midominio.com    mi_tenant.sajet.us;
```

#### C) Map `$proxy_odoo_host` (maps globales) — agregar:
```nginx
    midominio.com        mi_tenant.sajet.us;
    www.midominio.com    mi_tenant.sajet.us;
```

#### D) Server block `DOMINIOS EXTERNOS` → `server_name` — agregar:
```nginx
    server_name
        techeels.io www.techeels.io
        evolucionamujer.com www.evolucionamujer.com
        impulse-max.com www.impulse-max.com
        midominio.com www.midominio.com;    # ← NUEVO
```

### 2.2 — `/etc/nginx/conf.d/odoo_http_routes.map`

Agregar:
```
midominio.com 10.10.10.100:8080;
www.midominio.com 10.10.10.100:8080;
```

### 2.3 — `/etc/nginx/conf.d/odoo_chat_routes.map`

Agregar:
```
midominio.com 10.10.10.100:8080;
www.midominio.com 10.10.10.100:8080;
```

### 2.4 — Recargar nginx:
```bash
nginx -t && systemctl reload nginx
```

---

## Paso 3: Actualizar CT 105

### 3.1 — `/etc/nginx/sites-enabled/odoo`

Editar 4 secciones:

#### A) Map `$tenant_db` — agregar:
```nginx
    midominio.com mi_tenant;
    www.midominio.com mi_tenant;
```

#### B) Map `$web_redirect_target` — agregar:
```nginx
    midominio.com: /web?db=mi_tenant;
    www.midominio.com: /web?db=mi_tenant;
```

#### C) Map `$odoo_proxy_host` — agregar:
```nginx
    midominio.com mi_tenant.sajet.us;
    www.midominio.com mi_tenant.sajet.us;
```

#### D) `server_name` — agregar:
```nginx
    server_name *.sajet.us sajet.us ... midominio.com www.midominio.com;
```

#### E) `proxy_redirect` — agregar (si es un tenant diferente a techeels):
```nginx
    proxy_redirect https://mi_tenant.sajet.us/ https://$host/;
    proxy_redirect http://mi_tenant.sajet.us/ https://$host/;
```

### 3.2 — Recargar nginx:
```bash
nginx -t && systemctl reload nginx
```

---

## Paso 4: (Opcional) Cloudflare Tunnel

Si el dominio está en la misma cuenta Cloudflare que `sajet.us`, opcionalmente agregar al tunnel:

### `/etc/cloudflared/tcs-sajet-tunnel.yml` — agregar antes de `catch-all`:
```yaml
  - hostname: midominio.com
    service: http://localhost:8080
  - hostname: www.midominio.com
    service: http://localhost:8080
```

Luego reiniciar:
```bash
systemctl restart cloudflared-tcs-sajet-tunnel
```

> ⚠️ Esto solo funciona si la zona DNS del dominio está en la misma cuenta Cloudflare. Para dominios en otras cuentas, usar solo el A record.

---

## Paso 5: Verificar

```bash
# Verificar redirect inicial
curl -sk --resolve midominio.com:443:208.115.125.29 \
  -D- -o/dev/null "https://midominio.com/web" 2>&1 | grep location
# Esperado: location: https://midominio.com/web?db=mi_tenant

# Verificar login
curl -sk --resolve midominio.com:443:208.115.125.29 \
  -D- -o/dev/null "https://midominio.com/web?db=mi_tenant" 2>&1 | grep location
# Esperado: location: https://midominio.com/web/login?db=mi_tenant

# Verificar que la página carga
curl -sk --resolve midominio.com:443:208.115.125.29 \
  "https://midominio.com/web/login?db=mi_tenant" | grep '<title>'
# Esperado: <title>Login | Mi Tenant</title>

# Verificar *.sajet.us sigue funcionando
curl -sk --resolve mi_tenant.sajet.us:443:208.115.125.29 \
  -D- -o/dev/null "https://mi_tenant.sajet.us/web" 2>&1 | grep location
# Esperado: location: https://mi_tenant.sajet.us/web?db=mi_tenant
```

---

## 🔥 Troubleshooting

| Síntoma | Causa | Solución |
|---------|-------|----------|
| HTTP 403 | CNAME proxied → dominio proxied | Usar A record, no CNAME |
| HTTP 530 | Tunnel cross-zone sin dashboard config | Usar A record en vez de tunnel |
| HTTP 404 | Dominio no está en server_name ni en maps | Verificar paso 2 y 3 |
| Redirect a `/web/database/selector` | Odoo no resuelve la BD | Verificar X-Forwarded-Host → `$odoo_proxy_host` |
| Redirect a `techeels.sajet.us` en vez de dominio | proxy_redirect no está aplicando | Verificar que las locations no tienen `proxy_redirect off` |
| Login page pero título incorrecto | BD incorrecta seleccionada | Verificar map $tenant_db |

### Logs útiles:
```bash
# Nginx CT105
tail -f /var/log/nginx/odoo-access.log
tail -f /var/log/nginx/odoo-error.log

# Odoo
tail -f /var/log/odoo/odoo.log | grep werkzeug

# Nginx PCT160
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Debug temporal (CT105 nginx):
Agregar en `/etc/nginx/nginx.conf` (dentro de `http {}`):
```nginx
log_format debug_host '$remote_addr - $host [$odoo_proxy_host] "$request" $status';
```
Luego en el server block de `/etc/nginx/sites-enabled/odoo`:
```nginx
access_log /var/log/nginx/odoo-debug.log debug_host;
```
Recargar y verificar:
```bash
nginx -t && systemctl reload nginx
tail -f /var/log/nginx/odoo-debug.log
```

---

## 📎 Referencia Rápida: Archivos a Editar

| Servidor | Archivo | Qué agregar |
|----------|---------|-------------|
| PCT 160 | `/etc/nginx/sites-available/erp` | 3 maps + server_name |
| PCT 160 | `/etc/nginx/conf.d/odoo_http_routes.map` | dominio → 10.10.10.100:8080 |
| PCT 160 | `/etc/nginx/conf.d/odoo_chat_routes.map` | dominio → 10.10.10.100:8080 |
| CT 105 | `/etc/nginx/sites-enabled/odoo` | 3 maps + server_name + proxy_redirect |
| CT 105 | `/etc/cloudflared/tcs-sajet-tunnel.yml` | hostname (opcional) |
| Cloudflare | Zona DNS del dominio | A record → 208.115.125.29 (Proxied) |
