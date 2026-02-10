# Módulo Cloudflare - Gestión de Tunnels

Este directorio contiene scripts y configuración para gestionar Cloudflare Tunnels que exponen tenants Odoo a Internet de forma segura.

## Archivos

### `cf_manager.sh` (Bash Script)
Gestor interactivo de Cloudflare Tunnels via CLI. Permite:
- Crear nuevos tunnels
- Eliminar tunnels
- Listar tunnels activos
- Configurar DNS routing

**Uso:**
```bash
bash cf_manager.sh
```

### `create_tenant.sh` (Original)
Script para crear tenant completo (DB + Odoo + Tunnel).

**Uso:**
```bash
./create_tenant.sh <subdomain> [--with-demo]
```

### `create_tenant_enhanced.sh` (Mejorado)
Versión mejorada que integra con el sistema de provisioning de la API.

**Uso:**
```bash
./create_tenant_enhanced.sh <subdomain> [--with-demo] [--container-ip IP] [--local-port PORT]
```

### `.cf_credentials_example`
Template para configurar credenciales de Cloudflare. 

**Paso 1: Copiar archivo**
```bash
cp .cf_credentials_example ~/.cf_credentials
chmod 600 ~/.cf_credentials
```

**Paso 2: Agregar credenciales**
```bash
# Editar archivo con tus datos de Cloudflare
nano ~/.cf_credentials
```

**Paso 3: Obtener credenciales de Cloudflare**

1. **Token de API:**
   - Ir a https://dash.cloudflare.com/profile/api-tokens
   - Crear nuevo token con permisos: Zone:DNS:Edit + Tunnels:Admin
   - Copiar a `CF_API_TOKEN` en `.cf_credentials`

2. **Account ID & Zone ID:**
   - Ir a https://dash.cloudflare.com/
   - Seleccionar dominio `sajet.us`
   - ID de zona: en la esquina derecha del dashboard

3. **Account Tag:**
   - En API → Overview → Account Tag

### `dominios.json`
Lista de dominios gestionados por Cloudflare.

**Formato:**
```json
[
    {"domain": "sajet.us", "type": "primary"},
    {"domain": "acme.sajet.us", "type": "subdomain", "tenant_id": 1}
]
```

## Integración con Python FastAPI

El sistema principal integra estos scripts a través de:

1. **CloudflareManager** (`app/services/cloudflare_manager.py`)
   - Wrapper Python que ejecuta comandos cloudflared
   - Métodos: create_tunnel, delete_tunnel, get_status, etc.

2. **Tunnel API Endpoints** (`app/routes/tunnels.py`)
   - REST API para gestionar tunnels
   - Endpoints: POST/DELETE /api/tunnels, GET /api/tunnels/status, etc.

3. **Enhanced Provisioner** (`app/services/odoo_provisioner.py`)
   - Provisioning automático de tenants + tunnels
   - Usa create_tenant_enhanced.sh internamente

## Flujo de Creación Automática

```
1. Cliente subscribe (Stripe)
   ↓
2. Webhook → POST /webhook/stripe
   ↓
3. Crear Customer + Subscription
   ↓
4. Llamar provision_tenant()
   ↓
5. Ejecutar: pct exec 105 -- create_tenant_enhanced.sh
   ↓
6. Crear Cloudflare Tunnel via cloudflared CLI
   ↓
7. Configurar DNS routing
   ↓
8. Actualizar BD con tunnel_url, tunnel_id, status=active
   ↓
9. Usuario accede a: https://[subdomain].sajet.us
```

## Troubleshooting

### cloudflared no instalado
```bash
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

dpkg -i cloudflared.deb
```

### Credenciales inválidas
```bash
# Test de credentials
cloudflared tunnel list

# Si falla, re-autenticar
cloudflared tunnel login
```

### Tunnel no responde
```bash
# Ver logs
systemctl status cloudflared-[tunnel-name]-tunnel

# Reiniciar
systemctl restart cloudflared-[tunnel-name]-tunnel
```

### DNS no resuelve
```bash
# Verificar ruta DNS
cloudflared tunnel route dns --list

# Reconfigure
cloudflared tunnel route dns acme acme.sajet.us
```

## Variables de Entorno (en .env)

```bash
# Cloudflare
CF_CREDENTIALS_FILE=/root/.cf_credentials
CF_DOMAINS_FILE=/root/Cloudflare/dominios.json
CLOUDFLARED_PATH=/usr/bin/cloudflared

# LXC
LXC_CONTAINER_ID=105
DOMAIN=sajet.us
CREATE_TENANT_SCRIPT=/root/Cloudflare/create_tenant.sh
```

## Operaciones Comunes

### Crear tunnel via API
```bash
curl -X POST http://localhost:4443/api/tunnels \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_id": "5",
    "container_id": 1,
    "local_port": 8069
  }'
```

### Listar tunnels
```bash
curl http://localhost:4443/api/tunnels \
  -H "Authorization: Bearer <JWT>"
```

### Obtener estado
```bash
curl http://localhost:4443/api/tunnels/acme-tunnel/status \
  -H "Authorization: Bearer <JWT>"
```

### Ver logs
```bash
curl http://localhost:4443/api/tunnels/acme-tunnel/logs \
  -H "Authorization: Bearer <JWT>"
```

### Eliminar tunnel
```bash
curl -X DELETE http://localhost:4443/api/tunnels/acme-tunnel \
  -H "Authorization: Bearer <JWT>"
```

## Monitoreo

### Dashboard Admin
- Acceder: http://localhost:4443/admin/tunnels
- Ver: estado, logs, acciones rápidas

### Métricas
```bash
curl http://localhost:4443/api/dashboard/metrics \
  -H "Authorization: Bearer <JWT>"
```

## Seguridad

1. **Credenciales:**
   - Guardar `.cf_credentials` con permisos 600
   - No commitear a git (incluido en .gitignore)
   - Usar variables de entorno en producción

2. **Tokens JWT:**
   - Requieren auth para acceso a endpoints
   - Rate limiting integrado

3. **Cloudflare WAF:**
   - Protección DDoS automática
   - Rate limiting per domain

## Documentación Completa

Ver [docs/CLOUDFLARE_INTEGRATION.md](../docs/CLOUDFLARE_INTEGRATION.md) para guía completa.

