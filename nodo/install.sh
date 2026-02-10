#!/bin/bash
#
# INSTALADOR DE NODO ODOO MULTI-TENANT
# 
# Este script instala todo lo necesario para convertir un servidor Odoo
# en un nodo multi-tenant con provisioning automático
#
# Uso: sudo bash install.sh
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
NODO_HOME="/opt/nodo"
ODOO_HOME="/opt/odoo"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}[*] $1${NC}"
}

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    print_error "Este script debe ejecutarse como root (sudo)"
    exit 1
fi

print_header "INSTALACIÓN DE NODO ODOO MULTI-TENANT"

# 1. Validar dependencias
print_header "1. Validando dependencias"

for cmd in python3 pip3 sudo postgresql psql; do
    if command -v "$cmd" &> /dev/null; then
        print_success "$cmd instalado"
    else
        print_error "$cmd no encontrado. Instálalo primero."
        exit 1
    fi
done

# 2. Crear estructura de directorios
print_header "2. Creando estructura de directorios"

mkdir -p "$NODO_HOME"/{scripts,config,systemd,cloudflare,docs,logs}
mkdir -p /var/lib/odoo
print_success "Directorios creados"

# 3. Copiar archivos desde instalador
print_header "3. Instalando archivos"

# Scripts
if [ -d "$SCRIPT_DIR/scripts" ]; then
    cp "$SCRIPT_DIR/scripts"/*.py "$ODOO_HOME/scripts/" 2>/dev/null || true
    cp "$SCRIPT_DIR/scripts"/*.sh "$ODOO_HOME/scripts/" 2>/dev/null || true
    chmod +x "$ODOO_HOME/scripts"/*.sh
    print_success "Scripts instalados en $ODOO_HOME/scripts"
fi

# Configuración
if [ -d "$SCRIPT_DIR/config" ]; then
    cp "$SCRIPT_DIR/config"/* "$NODO_HOME/config/" 2>/dev/null || true
    print_success "Archivos de configuración instalados"
fi

# Cloudflare
if [ -d "$SCRIPT_DIR/cloudflare" ]; then
    cp "$SCRIPT_DIR/cloudflare"/* "$NODO_HOME/cloudflare/" 2>/dev/null || true
    chmod 600 "$NODO_HOME/cloudflare"/*.json 2>/dev/null || true
    print_success "Configuración Cloudflare instalada"
fi

# 4. Configurar Cloudflare
print_header "4. Configuración de Cloudflare"

DOMAINS_CONFIG="$NODO_HOME/cloudflare/domains.json"
if [ -f "$DOMAINS_CONFIG" ]; then
    print_info "Dominios configurados:"
    python3 -c "import json; c=json.load(open('$DOMAINS_CONFIG')); [print(f'  - {k}') for k in c.get('zones', {}).keys()]" || true
fi

read -p "¿Deseas actualizar el token de Cloudflare? (s/n): " update_cf
if [ "$update_cf" = "s" ]; then
    read -p "Ingresa tu API Token de Cloudflare: " cf_token
    python3 << PYTHON
import json
with open('$DOMAINS_CONFIG', 'r') as f:
    config = json.load(f)
# Guardar token en variable de entorno (no en JSON)
print(f"Actualizar en .env: CLOUDFLARE_API_TOKEN={cf_token}")
PYTHON
fi

# 5. Instalar dependencias Python
print_header "5. Instalando dependencias Python"

pip3 install --upgrade pip >/dev/null 2>&1
pip3 install fastapi uvicorn pydantic requests >/dev/null 2>&1
print_success "Dependencias Python instaladas"

# 6. Crear archivo .env
print_header "6. Configurando variables de entorno"

ENV_FILE="$NODO_HOME/config/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$NODO_HOME/config/nodo.env" "$ENV_FILE"
    print_success "Archivo .env creado en $ENV_FILE"
else
    print_info "Archivo .env ya existe"
fi

read -p "¿Deseas editar el archivo .env ahora? (s/n): " edit_env
if [ "$edit_env" = "s" ]; then
    nano "$ENV_FILE"
fi

# 7. Instalar servicios systemd
print_header "7. Instalando servicios systemd"

if [ -f "$SCRIPT_DIR/systemd/odoo-local-api.service" ]; then
    cp "$SCRIPT_DIR/systemd/odoo-local-api.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable odoo-local-api
    print_success "Servicio odoo-local-api instalado"
fi

if [ -f "$SCRIPT_DIR/systemd/odoo-db-watcher.service" ]; then
    cp "$SCRIPT_DIR/systemd/odoo-db-watcher.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable odoo-db-watcher
    print_success "Servicio odoo-db-watcher instalado"
fi

# 8. Crear directorios de logs y estado
print_header "8. Finalizando instalación"

mkdir -p "$NODO_HOME/logs"
mkdir -p /var/lib/odoo
touch "$NODO_HOME/logs/odoo-local-api.log"
touch "$NODO_HOME/logs/odoo-db-watcher.log"

chmod 755 "$NODO_HOME/scripts"/*.sh 2>/dev/null || true
print_success "Directorios de logs creados"

# 9. Mostrar siguientes pasos
print_header "INSTALACIÓN COMPLETADA"

echo -e "\n${GREEN}✓ Nodo Odoo Multi-Tenant instalado exitosamente${NC}\n"

echo "Siguientes pasos:"
echo "1. Editar configuración: nano $ENV_FILE"
echo "2. Actualizar dominio y credenciales Cloudflare"
echo "3. Iniciar servicios:"
echo "   sudo systemctl start odoo-local-api"
echo "   sudo systemctl start odoo-db-watcher"
echo ""
echo "Comandos útiles:"
echo "  - Ver estado: systemctl status odoo-local-api"
echo "  - Ver logs: journalctl -u odoo-local-api -f"
echo "  - Crear tenant: $ODOO_HOME/scripts/create_tenant.sh nombre_tenant contraseña"
echo "  - Listar tenants: $ODOO_HOME/scripts/list_tenants.sh"
echo ""
echo "Documentación: $SCRIPT_DIR/docs/"
echo ""
