---
name: erp-core-saas
description: Skill específica para el sistema Erp_core - SaaS multitenant para Odoo con FastAPI, Cloudflare Tunnels, y Stripe. Usa esta skill cuando trabajes en provisioning de tenants, gestión de túneles, o integración con Odoo.
license: Internal - Jeturing
---

# Erp_core SaaS Multitenant System

Esta skill guía el desarrollo del sistema de onboarding SaaS que automatiza:
- Registro de clientes y pagos con Stripe
- Provisioning de instancias Odoo multitenant en contenedores LXC
- Gestión de túneles Cloudflare para acceso público
- Dashboard administrativo con métricas y logs

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE (FastAPI)                         │
│                     https://sajet.us                                │
│                     LXC 160 - SRV-Sajet                             │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │     ODOO SERVER       │
              │     LXC 105           │
              │   SRV-Odoo-server     │
              │   Odoo 17 + PostgreSQL│
              │   Nginx + dbfilter    │
              └───────────────────────┘
```

## Stack Tecnológico

### Backend (FastAPI)
- **Framework:** FastAPI con Pydantic
- **Base de datos:** PostgreSQL (SQLAlchemy)
- **Autenticación:** JWT con cookies httpOnly
- **Seguridad:** WAF middleware, TOTP 2FA opcional
- **Templates:** Jinja2 con TailwindCSS

### Infraestructura
- **Contenedores:** Proxmox LXC
- **Túneles:** Cloudflare Argo Tunnels
- **Odoo:** Versión 17 Community
- **Dominio base:** sajet.us

## Patrones de Código

### Autenticación con Cookies
```python
from fastapi import Cookie, Header

async def endpoint(
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif access_token:
        token = access_token
    # Validar token...
```

### JavaScript Frontend (usar cookies, NO localStorage)
```javascript
// CORRECTO - usa cookies automáticamente
const response = await fetch('/api/endpoint', {
    credentials: 'same-origin'
});

// INCORRECTO - no usar localStorage para tokens
// const token = localStorage.getItem('admin_token');
```

### Provisioning de Tenants
```python
# Crear tenant via XML-RPC
models.execute_kw(db, uid, password, 
    'ir.module.module', 'button_immediate_install', [module_ids])
```

## Estructura de Directorios

```
app/
├── main.py              # FastAPI app principal
├── models/
│   └── database.py      # SQLAlchemy models
├── routes/
│   ├── auth.py          # Autenticación JWT
│   ├── provisioning.py  # Crear tenants (X-API-KEY)
│   ├── settings.py      # Configuración sistema
│   ├── tenants.py       # CRUD de tenants
│   └── tunnels.py       # Gestión Cloudflare
├── security/
│   └── middleware.py    # WAF, HTTPS, headers
└── services/
    ├── odoo_provisioner.py
    └── odoo_database_manager.py
```

## Convenciones

### Rutas API
- `/api/auth/*` - Autenticación (login, logout, refresh)
- `/api/tenants/*` - Gestión de tenants
- `/api/provisioning/*` - Provisioning (requiere X-API-KEY)
- `/api/settings/*` - Configuración del sistema
- `/api/cloudflare/*` - Túneles Cloudflare

### Headers de Seguridad
- `X-API-KEY: prov-key-2026-secure` - Para provisioning
- Cookie `access_token` - JWT para sesión de usuario
- Cookie `refresh_token` - Para renovar access_token

### Credenciales por Defecto
- **Admin Panel:** admin / SecurePass2026!
- **Odoo Tenants:** admin@sajet.us / 321Abcd.
- **PostgreSQL Odoo:** Jeturing / 123Abcd.
- **Master Password:** admin

## Comandos de Despliegue

### Sincronizar código al servidor
```bash
# Desde host Proxmox
pct push 160 /opt/Erp_core/file.py /opt/Erp_core/file.py
```

### Instalar módulos en Odoo
```python
# Via XML-RPC (cuando Odoo está corriendo)
common = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/object')
models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_install', [module_ids])
```

### Comandos LXC
```bash
# Ver contenedores
pct list

# Ejecutar comando en LXC
pct exec 160 -- comando

# Transferir archivo
pct push 160 /origen /destino

# Estado de servicio
pct exec 105 -- systemctl status odoo
```

## Módulos Preinstalados en Template

La base de datos `template_tenant` incluye:
- `spiffy_theme_backend` - Tema visual del backend
- `website` - Sitio web
- `website_mail` - Integración email

## Configuración Nginx (LXC 105)

```nginx
map $host $db_name {
    ~^(?<subdomain>[^.]+)\.sajet\.us$ $subdomain;
    default "";
}

server {
    listen 8080;
    server_name *.sajet.us;
    
    location / {
        proxy_pass http://127.0.0.1:8069;
        proxy_set_header X-Odoo-dbfilter $db_name;
        proxy_set_header Host $host;
    }
}
```

## Testing

### Probar endpoint con cookie
```bash
curl -c /tmp/cookies.txt -X POST "https://sajet.us/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin","password":"SecurePass2026!","role":"admin"}'

curl -b /tmp/cookies.txt "https://sajet.us/api/settings/odoo/current"
```

### Probar provisioning
```bash
curl -X POST "https://sajet.us/api/provisioning/tenant" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: prov-key-2026-secure" \
  -d '{"tenant_name": "Test", "subdomain": "test"}'
```

## Errores Comunes

1. **"Token requerido"** - El frontend debe usar `credentials: 'same-origin'` en fetch
2. **"API key inválida"** - Provisioning requiere header `X-API-KEY`
3. **CSP bloqueado** - Agregar dominios a `middleware.py` CSP headers
4. **WAF bloquea request** - JWT en cookies puede disparar falsos positivos, excluir Cookie header
