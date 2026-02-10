# /nodo/ - Paquete de Instalación para Nodo Odoo Multi-Tenant

## 📦 Contenido

Este directorio contiene todo lo necesario para convertir un servidor Odoo en un nodo multi-tenant con provisioning automático.

### 🎯 Propósito

Crear una estructura modular y reutilizable que permita:
1. Desplegar nodos Odoo multi-tenant en múltiples servidores
2. Autodetectar nuevas bases de datos y crear DNS automáticamente
3. Provisionar tenants remotamente via API HTTP
4. Escalar horizontalmente sin cambiar el código

### 📂 Estructura

```
nodo/
├── install.sh                      # ⭐ PUNTO DE ENTRADA - Ejecutar como: sudo bash install.sh
├── QUICKSTART.md                   # Guía rápida (5 minutos)
├── 
├── scripts/
│   ├── odoo_local_api.py          # 🚀 API REST en puerto 8070
│   ├── odoo_db_watcher.py         # 👀 Monitor de BDs para auto-DNS
│   ├── create_tenant.sh           # 📝 Crear tenant manualmente
│   ├── list_tenants.sh            # 📋 Listar tenants
│   └── delete_tenant.sh           # 🗑️ Eliminar tenant
│
├── systemd/
│   ├── odoo-local-api.service     # Servicio para API
│   └── odoo-db-watcher.service    # Servicio para monitor
│
├── config/
│   ├── nodo.env                   # Template de variables
│   └── .env                       # ⚙️ Archivo real (editado durante instalación)
│
├── cloudflare/
│   └── domains.json               # Zonas y tunnel ID de Cloudflare
│
├── docs/
│   ├── README.md                  # 📖 Documentación completa
│   ├── API.md                     # 🔌 Referencia de API
│   └── TROUBLESHOOTING.md         # 🐛 Solución de problemas
│
└── logs/
    └── *.log                      # 📊 Archivos de log
```

## 🚀 Instalación (Paso a Paso)

### Paso 1: Preparativos
```bash
# Verificar requisitos
sudo su -
apt update && apt install -y python3 python3-pip postgresql

# Instalar Odoo (si no está instalado)
# ... instrucciones de Odoo ...
```

### Paso 2: Ejecutar Instalador
```bash
sudo bash /path/to/nodo/install.sh
```

El instalador hará:
- Crear directorios (`/opt/nodo/`, `/opt/odoo/scripts/`)
- Instalar dependencias Python
- Copiar archivos de configuración
- Instalar servicios systemd
- Solicitar datos de Cloudflare

### Paso 3: Configurar
```bash
# Editar variables de entorno
sudo nano /opt/nodo/config/.env

# Variables clave:
# ODOO_DOMAIN=sajet.us
# CLOUDFLARE_API_TOKEN=tu_token_aqui
# CF_TUNNEL_ID=tu_tunnel_id_aqui
```

### Paso 4: Iniciar
```bash
sudo systemctl start odoo-local-api
sudo systemctl start odoo-db-watcher
sudo systemctl enable odoo-local-api
sudo systemctl enable odoo-db-watcher
```

### Paso 5: Verificar
```bash
# Healthcheck
curl http://localhost:8070/health

# Ver logs
journalctl -u odoo-local-api -f
journalctl -u odoo-db-watcher -f
```

## 🎮 Uso

### Via API HTTP (Desde APP Server)
```bash
curl -X POST \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{"subdomain": "cliente_nuevo", "admin_password": "secreto"}' \
  http://10.10.10.100:8070/api/tenant
```

### Via Scripts CLI (Directo en nodo)
```bash
# Crear
/opt/odoo/scripts/create_tenant.sh nombre_cliente contraseña123

# Listar
/opt/odoo/scripts/list_tenants.sh

# Eliminar
/opt/odoo/scripts/delete_tenant.sh nombre_cliente
```

## 🔄 Flujo de Provisioning

```
┌─────────────────────────────────────────────────────────┐
│          FRONTEND / USUARIO                             │
│        www.sajet.us/admin                               │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  APP SERVER (PCT 160)       │
        │  FastAPI :4443              │
        │  /api/provisioning/tenant   │
        │  X-API-KEY: prov-key-...    │
        └──────────────┬──────────────┘
                       │ HTTP :8070
        ┌──────────────▼──────────────┐
        │  NODO ODOO (PCT 105)        │
        │  odoo-local-api :8070       │
        │  /api/tenant (POST)         │
        └──────────────┬──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                              │
    ┌───▼────┐          ┌────────────▼──┐
    │ CREATE │          │  CREATE DNS   │
    │   BD   │          │  Cloudflare   │
    └────────┘          └───────────────┘
        │
        ▼ PostgreSQL
    ┌─────────────────┐
    │  nuevo_cliente  │ ◄─── https://nuevo_cliente.sajet.us
    │     (Odoo)      │
    └─────────────────┘
```

## 🌍 Despliegue Multi-Nodo

Para escalar a múltiples servidores:

1. **Instalar en cada servidor:**
   - PCT 105: ip 10.10.10.100 → `sudo bash /opt/Erp_core/nodo/install.sh`
   - PCT 200: ip 10.10.10.200 → `sudo bash /opt/Erp_core/nodo/install.sh`
   - PCT 300: ip 10.10.10.300 → `sudo bash /opt/Erp_core/nodo/install.sh`

2. **Actualizar APP Server (PCT 160):**
   ```python
   # provisioning.py
   ODOO_SERVERS = {
       "nodo1": {"ip": "10.10.10.100", "api_port": 8070},
       "nodo2": {"ip": "10.10.10.200", "api_port": 8070},
       "nodo3": {"ip": "10.10.10.300", "api_port": 8070}
   }
   ```

3. **Usar balanceador (Nginx, HAProxy, etc):**
   - Distribuir tenants entre nodos
   - Health checks automáticos

## 📊 Monitoreo

### Logs
```bash
# API
journalctl -u odoo-local-api -f

# DB Watcher
journalctl -u odoo-db-watcher -f

# Sistema
journalctl -n 100 -p err
```

### Métricas
```bash
# Ver tenants
/opt/odoo/scripts/list_tenants.sh

# Ver estado de servicios
systemctl status odoo-local-api
systemctl status odoo-db-watcher
```

### Alertas
- Monitorear `/var/lib/odoo/db_watcher_state.json` para cambios
- Revisar logs de Cloudflare en Dashboard

## 🔐 Seguridad

1. **Cambiar API Key:**
   ```bash
   # En /opt/nodo/config/.env
   PROVISIONING_API_KEY=nuevo_key_secreto_aleatorio
   ```

2. **IP Whitelisting (Firewall):**
   ```bash
   # Solo permitir conexiones desde APP Server
   ufw allow from 10.10.10.110 to any port 8070
   ```

3. **HTTPS (Opcional):**
   - Nginx reverse proxy con SSL
   - Certificado Let's Encrypt

4. **Auditoría:**
   - Revisar logs de creación/eliminación de tenants
   - Mantener backups automáticos

## 📚 Documentación Detallada

- **[QUICKSTART.md](./QUICKSTART.md)** - Instalación rápida (5 min)
- **[docs/README.md](./docs/README.md)** - Guía completa
- **[docs/API.md](./docs/API.md)** - Referencia de endpoints
- **[docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)** - Solución de problemas (crear si falta)

## ❓ Preguntas Frecuentes

**P: ¿Puedo instalar en Windows/Mac?**  
R: No, requiere Linux. Usa WSL en Windows.

**P: ¿Necesito Cloudflare?**  
R: No es obligatorio, pero se recomienda para DNS automático. Puedes crear registros manualmente.

**P: ¿Cuántos tenants soporta un nodo?**  
R: Depende de recursos (CPU, RAM, disco). Recomendado: 50-100 tenants por nodo de 4 cores + 16GB RAM.

**P: ¿Cómo migro tenants entre nodos?**  
R: Usar pg_dump / pg_restore o Odoo backup.

**P: ¿Se puede usar sin provisioning automático?**  
R: Sí, crear BDs manualmente con los scripts CLI.

## 🎯 Roadmap Futuro

- [ ] Dashboard web para gestión de tenants
- [ ] Balanceo automático de tenants entre nodos
- [ ] Respaldos automáticos
- [ ] Migración de tenants sin downtime
- [ ] Monitoreo centralizado
- [ ] Webhooks para eventos

## 📝 Versionado

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | Feb 2026 | Release inicial |

---

## 🚀 ¡Comienza ahora!

```bash
sudo bash /opt/Erp_core/nodo/install.sh
```

Para preguntas o issues, revisar documentación en `/nodo/docs/`

**Hecho con ❤️ para ERP Core**
