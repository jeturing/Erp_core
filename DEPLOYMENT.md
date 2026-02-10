# Deployment Guide - Onboarding System

## 🚀 Información del Servidor

- **IP**: 172.16.16.160
- **Hostname**: SRV-ONBOARDING
- **Path**: `/opt/onboarding-system`
- **Servicio**: `onboarding.service`
- **Puerto**: 4443
- **URL**: https://onboarding.sajet.us

## 📦 Último Deployment

**Fecha**: 31 de enero de 2026  
**Versión**: v2.3  
**Estado**: ✅ Exitoso

### Componentes Deployados

1. **Cloudflare Tunnel Management**
   - `app/services/cloudflare_manager.py` - Python wrapper para cloudflared CLI
   - `app/routes/tunnels.py` - REST API para gestión de tunnels
   - `templates/admin_tunnels.html` - UI de administración

2. **Refactored Provisioner**
   - `app/services/odoo_provisioner.py` - Sistema de provisioning con validaciones
   - Eliminación de valores hardcodeados
   - Validación completa de parámetros
   - Configuración basada en variables de entorno

3. **Documentación y Tests**
   - `docs/CLOUDFLARE_*.md` (4 archivos)
   - `docs/PARAMETER_VALIDATION.md`
   - `docs/PROVISIONER_REFACTOR.md`
   - `test_provisioner.py` (30+ test cases)

## 🔧 Proceso de Deployment

### 1. Preparar Paquete en Local

```bash
cd /Users/owner/Desktop/jcore/Erp_core

# Crear paquete tar.gz
tar -czf onboarding-system-v2.X.tar.gz \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='logs/*' \
  --exclude='.env' \
  app/ templates/ static/ Cloudflare/ docs/ \
  requirements.txt \
  .env.example \
  test_provisioner.py \
  README.md
```

### 2. Transferir al Servidor

```bash
scp onboarding-system-v2.X.tar.gz root@172.16.16.160:/tmp/
```

### 3. Backup y Extracción

```bash
ssh root@172.16.16.160

# Crear backup
cd /opt/onboarding-system
tar -czf /root/backups/onboarding-system-backup-$(date +%Y%m%d-%H%M%S).tar.gz app/ templates/

# Extraer nueva versión
tar -xzf /tmp/onboarding-system-v2.X.tar.gz
```

### 4. Actualizar .env (solo primera vez)

```bash
cd /opt/onboarding-system

# Agregar nuevas variables
cat >> .env << 'EOF'

# === Cloudflare Tunnels ===
CF_CREDENTIALS_FILE=/root/.cf_credentials
CLOUDFLARED_PATH=/usr/bin/cloudflared
ENABLE_CLOUDFLARE=true

# === Tenant Provisioning Configuration ===
LXC_CONTAINER_ID=105
DOMAIN=sajet.us
CREATE_TENANT_SCRIPT=/root/Cloudflare/create_tenant_enhanced.sh
DEFAULT_CONTAINER_IP=172.16.16.105
DEFAULT_LOCAL_PORT=8069
EOF
```

### 5. Reiniciar Servicio

```bash
systemctl restart onboarding
sleep 3
systemctl status onboarding
```

### 6. Verificar Deployment

```bash
# Estado del servicio
systemctl is-active onboarding

# Health check
curl -s http://localhost:4443/health | jq

# Test de login
curl -s -X POST http://localhost:4443/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin", "password": "SecurePass2026!", "role": "admin"}' | jq

# Ver logs
journalctl -u onboarding -n 50 --no-pager
```

## 🔐 Configuración de Cloudflare

### Crear archivo de credenciales

```bash
cat > /root/.cf_credentials << 'EOF'
CF_API_TOKEN=tu_cloudflare_api_token
ACCOUNT_ID=tu_cloudflare_account_id
ZONE_ID=tu_cloudflare_zone_id
EOF

chmod 600 /root/.cf_credentials
```

### Verificar cloudflared CLI

```bash
cloudflared --version
cloudflared tunnel list
```

## 📊 Endpoints Disponibles

### Admin Dashboard
- `GET /admin/tunnels` - UI de gestión de tunnels

### Cloudflare Tunnels API
- `GET /api/tunnels` - Listar todos los tunnels
- `POST /api/tunnels` - Crear tunnel para tenant
- `GET /api/tunnels/{id}/status` - Estado del tunnel
- `GET /api/tunnels/{id}/logs` - Logs del tunnel
- `POST /api/tunnels/{id}/restart` - Reiniciar tunnel
- `DELETE /api/tunnels/{id}` - Eliminar tunnel
- `GET /api/tunnels/subscription/{id}/tunnel` - Tunnel por suscripción

### Autenticación
- `POST /api/auth/login` - Login admin/tenant

## 🧪 Testing

### Tests Unitarios

```bash
cd /opt/onboarding-system
source venv/bin/activate
python test_provisioner.py
```

### Test de Provisioning

```bash
# Test con datos válidos
curl -X POST http://localhost:4443/api/tenants/provision \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=<token>" \
  -d '{
    "subdomain": "test-tenant",
    "admin_email": "admin@test.com",
    "company_name": "Test Company",
    "subscription_id": 1
  }'
```

## 🚨 Troubleshooting

### Servicio no inicia

```bash
# Ver logs completos
journalctl -u onboarding -n 100 --no-pager

# Verificar errores de Python
systemctl status onboarding

# Verificar permisos
ls -lh /opt/onboarding-system
chown -R root:root /opt/onboarding-system
```

### Error de importación

```bash
# Verificar estructura
cd /opt/onboarding-system
find app/ -name "*.py" | head -20

# Verificar __pycache__
find . -type d -name __pycache__ -exec rm -rf {} +
```

### Error en base de datos

```bash
# Verificar conexión a PostgreSQL
psql -h localhost -U jeturing -d onboarding_db -c "SELECT version();"

# Verificar variable DATABASE_URL
grep DATABASE_URL /opt/onboarding-system/.env
```

## 📋 Rollback

### Restaurar versión anterior

```bash
cd /opt/onboarding-system

# Detener servicio
systemctl stop onboarding

# Restaurar backup
tar -xzf /root/backups/onboarding-system-backup-YYYYMMDD-HHMMSS.tar.gz

# Reiniciar
systemctl start onboarding
systemctl status onboarding
```

## 🔄 Updates Comunes

### Actualizar un solo archivo

```bash
# En local
tar -czf update.tar.gz app/routes/tunnels.py
scp update.tar.gz root@172.16.16.160:/tmp/

# En servidor
cd /opt/onboarding-system
tar -xzf /tmp/update.tar.gz
systemctl restart onboarding
```

### Actualizar dependencias

```bash
ssh root@172.16.16.160
cd /opt/onboarding-system
source venv/bin/activate
pip install -r requirements.txt
systemctl restart onboarding
```

## 📝 Notas

- **Backup automático**: Los backups se crean en `/root/backups/` antes de cada deployment
- **Logs**: Los logs del sistema están en `journalctl -u onboarding`
- **Configuración**: El archivo `.env` contiene toda la configuración sensible
- **Permisos**: El servicio corre como root para acceder a LXC containers
- **Puerto**: 4443 (configurado en systemd service)

## ✅ Checklist de Deployment

- [ ] Crear paquete tar.gz en local
- [ ] Transferir a servidor
- [ ] Crear backup de código actual
- [ ] Extraer nueva versión
- [ ] Actualizar .env si hay nuevas variables
- [ ] Reiniciar servicio
- [ ] Verificar estado del servicio
- [ ] Test de health check
- [ ] Test de login
- [ ] Verificar logs sin errores
- [ ] Test de endpoints críticos

## 🔗 Referencias

- [CLOUDFLARE_INTEGRATION.md](docs/CLOUDFLARE_INTEGRATION.md)
- [PARAMETER_VALIDATION.md](docs/PARAMETER_VALIDATION.md)
- [PROVISIONER_REFACTOR.md](docs/PROVISIONER_REFACTOR.md)
- [JWT_QUICKSTART.md](docs/JWT_QUICKSTART.md)
