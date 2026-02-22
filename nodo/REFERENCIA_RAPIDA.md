# 🚀 REFERENCIA RÁPIDA - /nodo/

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


## 📍 Ubicación
```
/opt/Erp_core/nodo/
```

## ⚡ Instalación en 3 Pasos

```bash
# 1. Copiar
scp -r /opt/Erp_core/nodo/ user@servidor:/tmp/

# 2. Instalar (como root)
sudo bash /tmp/nodo/install.sh

# 3. Configurar
sudo nano /opt/nodo/config/.env
# Editar CLOUDFLARE_API_TOKEN y CF_TUNNEL_ID
```

## 🔧 Comandos Principales

```bash
# Iniciar servicios
sudo systemctl start odoo-local-api odoo-db-watcher

# Ver estado
sudo systemctl status odoo-local-api
sudo systemctl status odoo-db-watcher

# Ver logs
journalctl -u odoo-local-api -f
journalctl -u odoo-db-watcher -f

# Healthcheck
curl http://localhost:8070/health

# Crear tenant
/opt/odoo/scripts/create_tenant.sh mi_cliente secreto123

# Listar tenants
/opt/odoo/scripts/list_tenants.sh sajet.us

# Eliminar tenant
/opt/odoo/scripts/delete_tenant.sh mi_cliente
```

## 📚 Documentación

| Archivo | Propósito |
|---------|-----------|
| INDEX.md | Visión general |
| QUICKSTART.md | Instalación rápida |
| MANIFEST.md | Checklist de archivos |
| RESUMEN_EJECUTIVO.md | Resumen ejecutivo |
| docs/README.md | Guía completa |
| docs/API.md | Referencia API |

## 🔌 API Endpoints

```bash
# Listar tenants
curl -H "X-API-KEY: prov-key-2026-secure" \
     http://localhost:8070/api/tenants

# Crear tenant
curl -X POST \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{"subdomain":"nuevo","admin_password":"pass"}' \
  http://localhost:8070/api/tenant

# Eliminar tenant
curl -X DELETE \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{"subdomain":"nuevo"}' \
  http://localhost:8070/api/tenant

# Health check
curl http://localhost:8070/health

# Listar dominios
curl http://localhost:8070/api/domains
```

## 🐛 Troubleshooting

```bash
# API no responde
systemctl restart odoo-local-api
journalctl -u odoo-local-api -n 50

# Verificar PostgreSQL
sudo -u postgres psql -l

# Verificar puerto 8070
netstat -tlnp | grep 8070

# Reinstalar dependencias
pip3 install fastapi uvicorn pydantic requests

# Ver configuración
cat /opt/nodo/config/.env
```

## 📁 Estructura

```
nodo/
├── install.sh              ← Ejecutar primero
├── QUICKSTART.md           ← Guía rápida
├── docs/
│   ├── README.md           ← Guía completa
│   └── API.md              ← Endpoints
├── scripts/
│   ├── odoo_local_api.py
│   ├── odoo_db_watcher.py
│   ├── create_tenant.sh
│   ├── list_tenants.sh
│   └── delete_tenant.sh
├── systemd/
│   ├── odoo-local-api.service
│   └── odoo-db-watcher.service
├── config/
│   └── nodo.env
└── cloudflare/
    └── domains.json
```

## ✅ Validación Post-Instalación

```bash
# 1. Servicios corriendo
systemctl status odoo-local-api
systemctl status odoo-db-watcher

# 2. API respondiendo
curl http://localhost:8070/health
# → {"status":"ok","service":"odoo-provisioning"}

# 3. Listando tenants
curl -H "X-API-KEY: prov-key-2026-secure" \
     http://localhost:8070/api/tenants
# → {"tenants":[...],"total":N}

# 4. Logs limpios
journalctl -u odoo-local-api -n 5
# Sin errores
```

## 🎯 Variables de Entorno Clave

```
ODOO_DOMAIN=sajet.us
CLOUDFLARE_API_TOKEN=<editar>
CF_TUNNEL_ID=<editar>
PROVISIONING_API_KEY=prov-key-2026-secure
DB_WATCHER_INTERVAL=10
```

## 🔗 Integración con APP Server

```python
# En provisioning.py de PCT 160

ODOO_SERVERS = {
    "nodo1": {"ip": "10.10.10.100", "api_port": 8070},
    "nodo2": {"ip": "10.10.10.200", "api_port": 8070},
}
```

## 📞 Soporte

- Documentación: `/opt/nodo/docs/`
- Logs: `journalctl -u odoo-local-api -f`
- Config: `/opt/nodo/config/.env`

---

**Versión:** 1.0  
**Última actualización:** Febrero 2026
