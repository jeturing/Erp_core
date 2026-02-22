# QUICK START - Despliegue de Nodo Odoo Multi-Tenant

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


Guía rápida para desplegar `/nodo/` en un servidor nuevo.

## ⚡ 5 Minutos - Instalación Mínima

```bash
# 1. Como root, ejecutar instalador
sudo bash /opt/Erp_core/nodo/install.sh

# 2. Editar configuración
sudo nano /opt/nodo/config/.env

# Actualizar:
# CLOUDFLARE_API_TOKEN=tu_token_real
# CF_TUNNEL_ID=tu_tunnel_id_real

# 3. Iniciar servicios
sudo systemctl start odoo-local-api
sudo systemctl start odoo-db-watcher

# 4. Verificar
curl http://localhost:8070/health
```

## 📊 Checklist de Instalación

- [ ] Verificar requisitos previos (Ubuntu + Odoo + PostgreSQL)
- [ ] Ejecutar `install.sh`
- [ ] Editar `/opt/nodo/config/.env`
- [ ] Actualizar Cloudflare API Token
- [ ] Copiar `/opt/nodo/cloudflare/domains.json` a `/opt/odoo/config/`
- [ ] Iniciar servicios
- [ ] Verificar logs: `journalctl -u odoo-local-api -f`
- [ ] Probar crear tenant: `curl -X POST http://localhost:8070/api/tenant ...`

## 🔗 Integración con APP Server

Para conectar PCT 160 con este nodo:

**En PCT 160, actualizar `/opt/Erp_core/app/routes/provisioning.py`:**

```python
ODOO_SERVERS = {
    "primary": {
        "name": "SRV-Odoo-server",
        "ip": "10.10.10.100",      # IP del nodo nuevo
        "api_port": 8070,
        "domain": "sajet.us",
        "tunnel_id": "da2bc763-a93b-41f5-9a22-1731403127e3"
    }
}
```

## 📁 Archivos Importantes

| Archivo | Propósito |
|---------|-----------|
| `/opt/nodo/install.sh` | Script maestro de instalación |
| `/opt/nodo/config/.env` | Variables de entorno (editar) |
| `/opt/nodo/cloudflare/domains.json` | Configuración de dominios |
| `/opt/odoo/scripts/odoo_local_api.py` | API REST (systemd service) |
| `/opt/odoo/scripts/odoo_db_watcher.py` | Monitor de BDs (systemd service) |

## ✅ Validación

```bash
# Verificar API está corriendo
systemctl status odoo-local-api

# Probar endpoint
curl -H "X-API-KEY: prov-key-2026-secure" \
     http://localhost:8070/api/tenants

# Verificar DB Watcher
systemctl status odoo-db-watcher
journalctl -u odoo-db-watcher -n 10

# Crear un tenant de prueba
/opt/odoo/scripts/create_tenant.sh test_nodo secreto123
```

## 🎯 Flujo de Provisioning

```
PCT 160 (APP)           PCT 105 (NODO)
─────────────────────────────────────
  │                           │
  │  POST /api/tenant         │
  │──────────────────────────>│
  │  {"subdomain":"nuevo"...} │
  │                    odoo-local-api
  │                      ├─ CREATE BD
  │                      ├─ CONFIG
  │                      └─ DNS
  │  Response               │
  │<──────────────────────────┤
  │  {"success":true...}    │
  │                           │
```

## 🚨 Troubleshooting Rápido

**API no responde:**
```bash
systemctl restart odoo-local-api
journalctl -u odoo-local-api -n 30
```

**Cloudflare no crea DNS:**
```bash
# Verificar token
cat /opt/nodo/config/.env | grep CLOUDFLARE

# Probar conectividad
curl -I https://api.cloudflare.com/client/v4/zones
```

**PostgreSQL no accesible:**
```bash
sudo -u postgres psql -l | head
```

## 📞 Soporte

Ver documentación completa:
- `/opt/nodo/docs/README.md` - Guía completa
- `/opt/nodo/docs/API.md` - Documentación API
- `/opt/nodo/docs/TROUBLESHOOTING.md` - Solución de problemas

---

**Para siguiente servidor:** Repetir pasos 1-3 con distinto IP
