# Integración de Cloudflare Tunnels - Guía Completa

## Overview

El sistema de onboarding integra Cloudflare Tunnels para exponer automáticamente contenedores LXC (tenants Odoo) a Internet de forma segura, sin necesidad de configurar puertos públicos.

### Arquitectura de Tunnels

```
┌─────────────────────────────────────────┐
│   Cliente (Browser)                     │
│   https://acme.sajet.us                 │
└──────────────┬──────────────────────────┘
               │ HTTPS (Cloudflare)
               ▼
┌──────────────────────────────────────────┐
│   Cloudflare Edge (Global)               │
│   (Web Application Firewall)             │
└──────────────┬───────────────────────────┘
               │ TLS 1.2+
               ▼
┌──────────────────────────────────────────┐
│   cloudflared Tunnel (LXC 105)           │
│   Proceso daemon local                   │
└──────────────┬───────────────────────────┘
               │ HTTP (localhost)
               ▼
┌──────────────────────────────────────────┐
│   Odoo Service                           │
│   http://172.16.16.105:8069              │
│   (Inside LXC)                           │
└──────────────────────────────────────────┘
```

## Componentes del Sistema

### 1. CloudflareManager (`app/services/cloudflare_manager.py`)

Servicio Python que gestiona Cloudflare Tunnels mediante CLI `cloudflared`.

**Funcionalidades:**
- Crear tunnels: `create_tunnel(subdomain, container_id, local_port, domain)`
- Eliminar tunnels: `delete_tunnel(tunnel_name)`
- Listar tunnels: `list_tunnels()`
- Obtener estado: `get_tunnel_status(tunnel_name)`
- Reiniciar tunnels: `restart_tunnel(tunnel_name)`
- Obtener logs: `get_tunnel_logs(tunnel_name, lines)`

**Archivo de configuración:**
```bash
# ~/.cf_credentials
ACCOUNT_ID=...
ZONE_ID=...
CF_API_TOKEN=sk_...
CF_ACCOUNT_TAG=...
```

### 2. Endpoints API (`app/routes/tunnels.py`)

```
GET    /api/tunnels                          # Listar todos
POST   /api/tunnels                          # Crear nuevo
GET    /api/tunnels/{tunnel_id}/status       # Estado
GET    /api/tunnels/{tunnel_id}/logs         # Logs
DELETE /api/tunnels/{tunnel_id}              # Eliminar
POST   /api/tunnels/{tunnel_id}/restart      # Reiniciar
GET    /api/tunnels/subscription/{sub_id}/tunnel  # Por suscripción
```

### 3. Base de Datos - TenantDeployment

Tabla que enlaza suscripciones con deployments:

```sql
CREATE TABLE tenant_deployments (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER NOT NULL,
    container_id INTEGER NOT NULL,
    subdomain VARCHAR(100),
    tunnel_url VARCHAR(255),           -- ej: "acme.sajet.us"
    tunnel_id VARCHAR(100),            -- ID del tunnel en Cloudflare
    tunnel_active BOOLEAN DEFAULT FALSE,
    direct_url VARCHAR(255),           -- ej: "172.16.16.105:8069"
    plan_type VARCHAR(20),
    ...
);
```

### 4. Provisioning integrado (`app/services/odoo_provisioner.py`)

El provisioning ahora:
1. Crea DB PostgreSQL
2. Inicializa Odoo
3. **Crea automáticamente Cloudflare Tunnel**
4. Configura DNS routing
5. Actualiza estado en BD

## Flujo de Creación de Tenant

### 1. Cliente suscribe (Stripe webhook)

```json
POST /webhook/stripe
{
    "type": "checkout.session.completed",
    "data": {
        "object": {
            "client_reference_id": "123",  // Customer ID
            "customer_email": "admin@acme.com"
        }
    }
}
```

### 2. Crear Deployment + Tunnel

```bash
POST /api/tenants
{
    "subscription_id": 5,
    "subdomain": "acme",
    "plan_type": "pro",
    "container_id": 1,
    "local_port": 8069
}
```

Response:
```json
{
    "success": true,
    "tenant": {
        "id": 10,
        "subdomain": "acme",
        "database": "acme",
        "url": "https://acme.sajet.us",
        "tunnel": {
            "tunnel_id": "abc123",
            "tunnel_name": "acme-tunnel",
            "status": "active"
        }
    }
}
```

### 3. Verificar Tunnel

```bash
curl -H "Authorization: Bearer <JWT>" \
     http://localhost:4443/api/tunnels/acme-tunnel/status

{
    "tunnel_name": "acme-tunnel",
    "service": "cloudflared-acme-tunnel",
    "active": true,
    "status": "running"
}
```

## Configuración de Cloudflare

### Prerrequisitos

1. **Dominio en Cloudflare**: `sajet.us`
2. **API Token**: Con permisos de DNS + Tunnels
3. **Nameservers**: Apuntados a Cloudflare

### Instalación de cloudflared

```bash
# En el host Proxmox o LXC
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

dpkg -i cloudflared.deb

# Verificar instalación
cloudflared --version
```

### Autenticación

```bash
# Primera vez - login interactivo
cloudflared tunnel login

# Genera ~/.cloudflared/cert.pem + token
# Se guardará la credential
```

### Crear Tunnel Manual (referencia)

```bash
# Crear tunnel
cloudflared tunnel create acme

# Configurar routing DNS
cloudflared tunnel route dns acme acme.sajet.us

# Ejecutar tunnel
cloudflared tunnel run acme

# En otra terminal - crear archivo config
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: acme
credentials-file: /root/.cloudflared/abc123.json

ingress:
  - hostname: acme.sajet.us
    service: http://172.16.16.105:8069
  - service: http_status:404
EOF

# Listar tunnels
cloudflared tunnel list

# Eliminar tunnel
cloudflared tunnel delete acme
```

## Variables de Entorno

Agregar a `.env`:

```bash
# Cloudflare
CF_CREDENTIALS_FILE=/root/.cf_credentials
CF_DOMAINS_FILE=/root/Cloudflare/dominios.json
CLOUDFLARED_PATH=/usr/bin/cloudflared

# Tenant Provisioning
LXC_CONTAINER_ID=105
DOMAIN=sajet.us
CREATE_TENANT_SCRIPT=/root/Cloudflare/create_tenant.sh
```

## Operaciones Comunes

### Listar todos los Tunnels

```bash
curl -H "Authorization: Bearer <JWT>" \
     http://localhost:4443/api/tunnels
```

```json
{
    "success": true,
    "total": 5,
    "tunnels": [
        {
            "id": "abc123",
            "name": "acme-tunnel",
            "status": "active",
            "deployment": {
                "subdomain": "acme",
                "url": "https://acme.sajet.us",
                "plan": "pro",
                "subscription_id": 5
            }
        }
    ]
}
```

### Obtener Logs de un Tunnel

```bash
curl -H "Authorization: Bearer <JWT>" \
     "http://localhost:4443/api/tunnels/acme-tunnel/logs?lines=100"
```

### Reiniciar Tunnel

```bash
curl -X POST \
     -H "Authorization: Bearer <JWT>" \
     http://localhost:4443/api/tunnels/acme-tunnel/restart
```

### Eliminar Tenant + Tunnel

```bash
curl -X DELETE \
     -H "Authorization: Bearer <JWT>" \
     http://localhost:4443/api/tenants/5
```

Esto:
1. Borra base de datos PostgreSQL
2. Detiene servicio systemd de tunnel
3. Elimina tunnel de Cloudflare
4. Marca como inactivo en BD

## Troubleshooting

### Tunnel no responde

```bash
# Ver estado del servicio
systemctl status cloudflared-acme-tunnel

# Ver logs
journalctl -u cloudflared-acme-tunnel -f

# Reiniciar
systemctl restart cloudflared-acme-tunnel
```

### Error "tunnel already exists"

```bash
# Listar y eliminar tunels duplicados
cloudflared tunnel list
cloudflared tunnel delete acme  # Si está duplicado

# Desde API
curl -X DELETE \
     -H "Authorization: Bearer <JWT>" \
     http://localhost:4443/api/tunnels/acme-tunnel
```

### DNS no resuelve

```bash
# Verificar en Cloudflare Dashboard
# o via DNS lookup
nslookup acme.sajet.us

# Verificar ruta DNS en tunnel
cloudflared tunnel route dns --list

# Reconfigure si es necesario
cloudflared tunnel route dns acme acme.sajet.us
```

### Servicio no inicia automáticamente

```bash
# Habilitar en systemd
systemctl enable cloudflared-acme-tunnel
systemctl start cloudflared-acme-tunnel

# Verificar
systemctl is-active cloudflared-acme-tunnel
```

## Monitoreo

### Dashboard Admin

La ruta `/admin` ahora muestra:
- Estado de todos los tunnels
- Salud de conexiones
- Logs en tiempo real
- Acciones rápidas (restart, delete)

### Métricas

```bash
GET /api/dashboard/metrics

{
    "tunnel_health": {
        "total": 5,
        "active": 5,
        "error": 0,
        "avg_latency_ms": 45
    }
}
```

## Seguridad

### Recomendaciones

1. **Rate Limiting**: Cloudflare WAF protege contra DDoS
2. **Autenticación**: JWT en backend + Cloudflare auth (opcional)
3. **Encriptación**: TLS 1.2+ entre cliente y Cloudflare
4. **Tokens**: Guardar `CF_API_TOKEN` en secretos (no en .env)
5. **Auditoría**: Todos los cambios de tunnel se registran

### Rotate Credentials

```bash
# Generar nuevo token Cloudflare
# En Dashboard → API Token → Create Token

# Actualizar .env
CF_API_TOKEN=sk_new_...

# Reiniciar servicio
systemctl restart onboarding
```

## Integración con Terraform (Futuro)

Para automatizar creación de dominios en Cloudflare:

```hcl
resource "cloudflare_zone" "sajet" {
  zone = "sajet.us"
}

resource "cloudflare_record" "tenant" {
  zone_id = cloudflare_zone.sajet.id
  name    = var.subdomain
  type    = "CNAME"
  value   = "tunnel-alias.sajet.us"
}
```

## Referencias

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [cloudflared CLI Reference](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/)
- [API de Cloudflare](https://developers.cloudflare.com/api/)

