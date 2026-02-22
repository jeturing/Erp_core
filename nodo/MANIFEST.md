# MANIFEST - Contenido de /nodo/

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


## 📋 Checklist de Archivos

### Scripts (scripts/)
- [x] odoo_local_api.py (198 líneas) - API REST FastAPI para provisioning
- [x] odoo_db_watcher.py (220 líneas) - Monitor de PostgreSQL con auto-DNS
- [x] create_tenant.sh - Crear tenants manualmente
- [x] list_tenants.sh - Listar tenants
- [x] delete_tenant.sh - Eliminar tenants

### Configuración (config/)
- [x] nodo.env - Template de variables de entorno
- [x] .env - Archivo .env real (generado por instalador)

### Systemd (systemd/)
- [x] odoo-local-api.service - Servicio para API
- [x] odoo-db-watcher.service - Servicio para DB Watcher

### Cloudflare (cloudflare/)
- [x] domains.json - Configuración de zonas Cloudflare

### Documentación (docs/)
- [x] README.md - Guía completa
- [x] API.md - Referencia de API

### Raíz
- [x] install.sh - Script maestro de instalación
- [x] QUICKSTART.md - Guía rápida
- [x] INDEX.md - Visión general del paquete
- [x] MANIFEST.md - Este archivo

---

## 🎯 Qué se Instala

### En /opt/nodo/
```
config/
├── nodo.env (template)
└── .env (archivo real)

cloudflare/
└── domains.json

scripts/
├── odoo_local_api.py
├── odoo_db_watcher.py
├── create_tenant.sh
├── list_tenants.sh
└── delete_tenant.sh

systemd/
├── odoo-local-api.service
└── odoo-db-watcher.service

docs/
├── README.md
└── API.md

logs/
└── (archivos creados en tiempo de ejecución)
```

### En /opt/odoo/scripts/
```
odoo_local_api.py
odoo_db_watcher.py
create_tenant.sh
list_tenants.sh
delete_tenant.sh
```

### En /etc/systemd/system/
```
odoo-local-api.service
odoo-db-watcher.service
```

---

## 🔧 Configuración

### Valores Predeterminados
- Puerto API: 8070
- Dominio: sajet.us
- API Key: prov-key-2026-secure
- DB Watcher intervalo: 10 segundos
- Template BD: tcs

### Variables de Entorno Clave
```
ODOO_DOMAIN=sajet.us
CLOUDFLARE_API_TOKEN=<editar>
CF_TUNNEL_ID=<editar>
PROVISIONING_API_KEY=prov-key-2026-secure
DB_WATCHER_INTERVAL=10
```

---

## ✅ Validación Post-Instalación

```bash
# 1. Verificar directorios
ls -la /opt/nodo/
ls -la /opt/odoo/scripts/

# 2. Verificar servicios
systemctl status odoo-local-api
systemctl status odoo-db-watcher

# 3. Healthcheck
curl http://localhost:8070/health

# 4. Logs
journalctl -u odoo-local-api -n 10
journalctl -u odoo-db-watcher -n 10
```

---

## 📊 Estadísticas del Paquete

| Elemento | Cantidad |
|----------|----------|
| Scripts Python | 2 |
| Scripts Bash | 3 |
| Servicios systemd | 2 |
| Archivos de config | 2 |
| Documentación | 4 |
| Líneas de código | ~1000 |
| Tamaño total | ~100 KB |

---

## 🚀 Ciclo de Vida

### Instalación
1. Ejecutar `install.sh`
2. Ingresar datos de Cloudflare
3. Iniciar servicios

### Operación
1. API escucha en :8070
2. DB Watcher monitorea cada 10s
3. Servicios auto-reinician si caen

### Mantenimiento
1. Revisar logs regularmente
2. Actualizar API Key si es necesario
3. Respaldar `/opt/nodo/config/.env`

---

## 🔄 Actualización

Para actualizar a versión nueva:
```bash
# Respaldar config actual
cp /opt/nodo/config/.env /opt/nodo/config/.env.backup

# Copiar nuevos scripts
cp /nueva/version/nodo/scripts/* /opt/odoo/scripts/

# Reiniciar
systemctl restart odoo-local-api
systemctl restart odoo-db-watcher
```

---

**Total de archivos:** 13  
**Completado:** 100%  
**Fecha:** Febrero 2026
