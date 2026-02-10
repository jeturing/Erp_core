# NODO ODOO MULTI-TENANT

Paquete de instalación para convertir un servidor Odoo en un nodo multi-tenant con provisioning automático de tenants via API.

## 📋 Requisitos Previos

- Ubuntu/Debian Linux
- Odoo instalado y funcionando
- PostgreSQL 12+
- Python 3.8+
- Acceso root o sudo
- Token de Cloudflare (para auto-provisioning de DNS)

## 🚀 Instalación Rápida

```bash
# Como root o con sudo
sudo bash /path/to/nodo/install.sh
```

El instalador:
1. Crea la estructura `/opt/nodo`
2. Instala dependencias Python (FastAPI, Uvicorn, Pydantic, Requests)
3. Copia scripts y configuraciones
4. Instala servicios systemd
5. Genera archivo `.env` editable

## ⚙️ Configuración

Editar `/opt/nodo/config/.env`:

```bash
# Dominio del nodo
ODOO_DOMAIN=sajet.us

# Token de Cloudflare para auto-provisioning de DNS
CLOUDFLARE_API_TOKEN=tu_token_aqui

# ID del túnel Cloudflare
CF_TUNNEL_ID=tu_tunnel_id_aqui

# API Key para comunicación entre nodos
PROVISIONING_API_KEY=prov-key-2026-secure
```

Editar `/opt/nodo/cloudflare/domains.json` para configurar zonas:

```json
{
  "zones": {
    "sajet.us": "zone_id_1",
    "otro.dominio": "zone_id_2"
  },
  "tunnel_id": "tu_tunnel_id"
}
```

## 🔧 Servicios

### odoo-local-api.service
API REST para provisioning local de tenants.

**Puerto:** 8070

**Endpoints:**
- `GET /health` - Healthcheck
- `GET /api/tenants` - Listar tenants
- `POST /api/tenant` - Crear tenant
- `DELETE /api/tenant` - Eliminar tenant
- `GET /api/domains` - Listar dominios

**Autenticación:** Header `X-API-KEY: <PROVISIONING_API_KEY>`

Ejemplo:
```bash
curl -H "X-API-KEY: prov-key-2026-secure" \
     http://localhost:8070/api/tenants
```

### odoo-db-watcher.service
Monitorea PostgreSQL y crea automáticamente registros DNS en Cloudflare cuando se detectan nuevas bases de datos.

**Características:**
- Monitoreo automático cada 10 segundos
- Detección de nuevas BDs
- Creación automática de registros CNAME en Cloudflare
- Logging detallado

**Configuración:**
- `DB_WATCHER_INTERVAL=10` - Segundos entre chequeos

**Logs:**
```bash
journalctl -u odoo-db-watcher -f
```

## 📝 Uso

### Crear un tenant manualmente

```bash
/opt/odoo/scripts/create_tenant.sh nombre_tenant contraseña sajet.us tcs
```

Parámetros:
- `nombre_tenant` - Nombre del tenant (ej: cliente_nuevo)
- `contraseña` - Contraseña para usuario admin
- `dominio` - Dominio (default: sajet.us)
- `plantilla` - BD plantilla (default: tcs)

### Listar tenants

```bash
/opt/odoo/scripts/list_tenants.sh sajet.us
```

### Eliminar un tenant

```bash
/opt/odoo/scripts/delete_tenant.sh nombre_tenant
```

### Ver estado de servicios

```bash
systemctl status odoo-local-api
systemctl status odoo-db-watcher
```

### Ver logs

```bash
# API local
journalctl -u odoo-local-api -f

# DB Watcher
journalctl -u odoo-db-watcher -f
```

## 🔗 Integración con APP Server

El APP Server (PCT 160) conecta con este nodo via HTTP:

```python
# PCT 160 calls PCT 105 local API
POST http://10.10.10.100:8070/api/tenant
{
  "subdomain": "nuevo_cliente",
  "admin_password": "secreto123",
  "domain": "sajet.us",
  "template_db": "tcs"
}
```

Headers requeridos:
- `X-API-KEY: prov-key-2026-secure`

## 📂 Estructura de Archivos

```
/opt/nodo/
├── install.sh                 # Script de instalación
├── config/
│   ├── nodo.env              # Variables de entorno
│   └── .env                  # Archivo real (editado)
├── scripts/
│   ├── odoo_local_api.py     # API REST de provisioning
│   ├── odoo_db_watcher.py    # Monitor de BDs
│   ├── create_tenant.sh      # Crear tenant manualmente
│   ├── list_tenants.sh       # Listar tenants
│   └── delete_tenant.sh      # Eliminar tenant
├── systemd/
│   ├── odoo-local-api.service
│   └── odoo-db-watcher.service
├── cloudflare/
│   └── domains.json          # Configuración de zonas
├── logs/
│   └── *.log                 # Logs de servicios
└── docs/
    ├── README.md             # Este archivo
    ├── API.md
    ├── DB_WATCHER.md
    └── TROUBLESHOOTING.md
```

## 🐛 Troubleshooting

### API no responde
```bash
# Verificar si el servicio está corriendo
systemctl status odoo-local-api

# Ver logs detallados
journalctl -u odoo-local-api -n 50

# Verificar acceso al puerto 8070
netstat -tlnp | grep 8070
```

### DB Watcher no crea DNS
```bash
# Verificar token de Cloudflare
echo $CLOUDFLARE_API_TOKEN

# Ver logs
journalctl -u odoo-db-watcher -f

# Probar conectividad a Cloudflare
curl -I https://api.cloudflare.com/client/v4/zones
```

### Error "API key inválida"
- Verificar que `X-API-KEY` header sea `prov-key-2026-secure`
- O actualizar en `/opt/nodo/config/.env`

## 🔄 Despliegue en Múltiples Nodos

Para desplegar en varios servidores:

1. **Nodo Principal (PCT 105):**
   ```bash
   sudo bash /opt/Erp_core/nodo/install.sh
   # Configurar Cloudflare y variables
   sudo systemctl start odoo-local-api
   sudo systemctl start odoo-db-watcher
   ```

2. **Nodos Secundarios (PCT 200, 300, etc):**
   ```bash
   # Repetir instalación en cada servidor
   # Cada uno escucha en puerto 8070
   ```

3. **APP Server (PCT 160):**
   ```python
   # Actualizar provisioning.py para incluir nuevos nodos
   ODOO_SERVERS = {
       "nodo1": {"ip": "10.10.10.100", "api_port": 8070},
       "nodo2": {"ip": "10.10.10.200", "api_port": 8070},
       "nodo3": {"ip": "10.10.10.300", "api_port": 8070}
   }
   ```

## 📞 Soporte

Para problemas o preguntas:
1. Revisar logs: `journalctl -u odoo-local-api -f`
2. Verificar configuración: `cat /opt/nodo/config/.env`
3. Ver documentación: `/opt/nodo/docs/`

---

**Versión:** 1.0  
**Última actualización:** Febrero 2026
