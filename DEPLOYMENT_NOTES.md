# Notas de Despliegue - Servidor 10.10.10.20

## ✅ Estado Actual (2026-02-18)

### Configuración
- **Servidor**: 10.10.10.20 (SRV-Sajet)
- **Ruta de instalación**: `/var/www/html`
- **Usuario del servicio**: `www-data`
- **Base de datos**: SQLite (fallback) en `/var/www/html/app_data/erp_core.db`

### Servicios Activos
1. **FastAPI Backend** (puerto 4443)
   - Servicio systemd: `erp-core.service`
   - Estado: ✅ **Activo**
   - Workers: 2
   - Timeout inicio: 60s
   - Reinicio automático: habilitado

2. **Nginx** (puerto 80)
   - Sitio: `/etc/nginx/sites-available/erp-core`
   - Estado: ✅ **Activo**
   - Función: Reverse proxy + servidor SPA

### Componentes Desplegados

```
/var/www/html/
├── app/                    # Backend FastAPI
├── frontend/dist/          # Frontend Svelte compilado
├── static/                 # Assets estáticos
├── app_data/              # Datos SQLite
├── logs/                  # Logs de aplicación
├── requirements.txt       # Dependencias Python
├── venv/                  # Entorno virtual Python
└── .env.production        # Variables de entorno
```

## 🔧 Configuración del Sistema

### Variables de Entorno (`.env.production`)
```
ENVIRONMENT=production
FORCE_HTTPS=false
ENABLE_WAF=false
ENABLE_SQLITE_FALLBACK=true
SQLALCHEMY_DATABASE_URL=sqlite:////var/www/html/app_data/erp_core.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=SecurePass2026!
```

### Rutas del Nginx
- `/` → Frontend SPA (index.html con fallback para routing)
- `/api/*` → Proxy a FastAPI en localhost:4443
- `/static/*` → Assets estáticos desde `/var/www/html/static/`

## 📊 Flujo de Acceso

```
Usuario (http://10.10.10.20)
    ↓
Nginx:80 (reverse proxy)
    ├→ /api/* → FastAPI:4443
    └→ /* → SPA static files
```

## ⚠️ Problemas Resueltos

### 1. Error 500 Internal Server Error (SOLUCIONADO)
**Causa**: Permisos incorrectos en directorio `logs/`
**Solución**: Cambiar owner a `www-data` y permisos 755

### 2. Servicio timeout (SOLUCIONADO)
**Causa**: Conexión a PostgreSQL remoto fallando
**Solución**: Usar SQLite como fallback con `ENABLE_SQLITE_FALLBACK=true`

### 3. 404 Not Found en Nginx (SOLUCIONADO)
**Causa**: Múltiples sitios configurados (conflicto con sitio `erp`)
**Solución**: Desactivar sitio conflictivo, mantener solo `erp-core`

### 4. Host header no enviado por curl (DETECTADO)
**Solución**: Sempre usar header `-H "Host: 10.10.10.20"` en pruebas locales

## 🚀 Acceso a la Aplicación

### Desde el cliente
```bash
# Abrir en navegador
http://10.10.10.20

# Login
- Usuario: admin
- Contraseña: SecurePass2026!
```

### Verificación de servicios
```bash
# SSH al servidor
ssh root@10.10.10.20

# Backend
systemctl status erp-core.service
journalctl -u erp-core.service -f

# Nginx
systemctl status nginx
tail -f /var/log/nginx/erp-core-error.log

# Base de datos
sqlite3 /var/www/html/app_data/erp_core.db ".tables"
```

## 📦 Actualización del código

### Desde MacBook local
```bash
cd /Users/owner/Desktop/jcore/Erp_core

# 1. Compilar frontend si hubo cambios
npm run build

# 2. Commit y push
git add -A
git commit -m "feat: descripción de cambios"
git push origin main

# 3. Transferir al servidor
scp -r frontend/dist root@10.10.10.20:/var/www/html/frontend/
scp -r app root@10.10.10.20:/var/www/html/

# 4. Reiniciar backend
ssh root@10.10.10.20 "systemctl restart erp-core.service"
```

## 🔍 Logs y Monitoreo

### Backend FastAPI
```bash
ssh root@10.10.10.20 "journalctl -u erp-core.service -f"
```

### Nginx
```bash
ssh root@10.10.10.20 "tail -f /var/log/nginx/erp-core-error.log"
ssh root@10.10.10.20 "tail -f /var/log/nginx/erp-core-access.log"
```

### Auditoría
```bash
ssh root@10.10.10.20 "tail -f /var/www/html/logs/audit.log"
```

## 🛠️ Mantenimiento

### Limpiar datos de prueba SQLite
```bash
ssh root@10.10.10.20 "rm /var/www/html/app_data/erp_core.db && systemctl restart erp-core.service"
```

### Cambiar a PostgreSQL producción
Modificar `.env.production`:
```
DATABASE_URL=postgresql://jeturing:PASSWORD@HOST:5432/erp_core_db
ENABLE_SQLITE_FALLBACK=false
```

Luego reiniciar:
```bash
ssh root@10.10.10.20 "systemctl restart erp-core.service"
```

### Habilitar HTTPS (Nginx + Certbot)
```bash
ssh root@10.10.10.20 "certbot certonly --nginx -d 10.10.10.20"
# Actualizar .env.production: FORCE_HTTPS=true
# Reiniciar: systemctl restart erp-core.service nginx
```

## 📝 Historial

| Fecha | Cambio | Estado |
|-------|--------|--------|
| 2026-02-18 | Despliegue inicial | ✅ |
| 2026-02-18 | Configuración SQLite fallback | ✅ |
| 2026-02-18 | Resolver conflictos Nginx | ✅ |

---

**Última actualización**: 2026-02-18 06:52 UTC  
**Responsable**: Jeturing ERP Core Team
