#!/bin/bash
# =============================================================================
# SCRIPT DE PROVISIONING AUTOMÁTICO DE TENANTS ODOO
# Crea: Base de datos + Subdominio en Cloudflare
# Uso: ./create_tenant.sh <nombre_tenant> [opciones]
# =============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración Cloudflare
CF_API_TOKEN="${CF_API_TOKEN:-}"
CF_ZONE_ID="${CF_ZONE_ID:-}"
CF_TUNNEL_ID="da2bc763-a93b-41f5-9a22-1731403127e3"
DOMAIN="sajet.us"

# Configuración Odoo
ODOO_MASTER_PASSWORD="${ODOO_MASTER_PASSWORD:-admin}"
ODOO_URL="http://localhost:8069"

# Uso
usage() {
    echo "Uso: $0 <nombre_tenant> [opciones]"
    echo ""
    echo "Crea automáticamente una base de datos Odoo y su subdominio en Cloudflare"
    echo ""
    echo "Argumentos:"
    echo "  nombre_tenant      Nombre del tenant (será el subdominio y nombre de BD)"
    echo ""
    echo "Opciones:"
    echo "  --admin-password   Password del admin de Odoo (default: admin)"
    echo "  --lang             Idioma (default: es_DO)"
    echo "  --country          País código ISO (default: DO)"
    echo "  --demo             Instalar datos de demostración"
    echo "  --modules          Módulos a instalar separados por coma"
    echo "  --help, -h         Mostrar esta ayuda"
    echo ""
    echo "Variables de entorno:"
    echo "  CF_API_TOKEN           Token de API de Cloudflare (requerido para DNS)"
    echo "  CF_ZONE_ID             Zone ID de Cloudflare para sajet.us"
    echo "  ODOO_MASTER_PASSWORD   Master password de Odoo (default: admin)"
    echo ""
    echo "Ejemplos:"
    echo "  $0 empresa1"
    echo "  $0 micliente --admin-password secreto123 --lang es_MX"
    echo "  $0 demo_company --demo --modules sale,purchase,stock"
    exit 1
}

# Parsear argumentos
TENANT_NAME=""
ADMIN_PASS="admin"
LANG="es_DO"
COUNTRY="DO"
DEMO="False"
MODULES=""
DEFAULT_MODULES="spiffy_theme_backend,hide_powered_by_odoo,rest_api_odoo"

while [[ $# -gt 0 ]]; do
    case $1 in
        --admin-password) ADMIN_PASS="$2"; shift 2 ;;
        --lang) LANG="$2"; shift 2 ;;
        --country) COUNTRY="$2"; shift 2 ;;
        --demo) DEMO="True"; shift ;;
        --modules) MODULES="$2"; shift 2 ;;
        --help|-h) usage ;;
        -*) echo -e "${RED}Opción desconocida: $1${NC}"; usage ;;
        *) TENANT_NAME="$1"; shift ;;
    esac
done

# Validaciones
if [[ -z "$TENANT_NAME" ]]; then
    echo -e "${RED}Error: Debe especificar nombre del tenant${NC}"
    usage
fi

# Normalizar nombre (minúsculas, sin espacios, solo alfanumérico y guión bajo)
TENANT_NAME=$(echo "$TENANT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr '-' '_' | sed 's/[^a-z0-9_]//g')

# Validar longitud
if [[ ${#TENANT_NAME} -lt 3 ]]; then
    echo -e "${RED}Error: El nombre del tenant debe tener al menos 3 caracteres${NC}"
    exit 1
fi

if [[ ${#TENANT_NAME} -gt 30 ]]; then
    echo -e "${RED}Error: El nombre del tenant no puede exceder 30 caracteres${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       PROVISIONING AUTOMÁTICO DE TENANT ODOO              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}Tenant:${NC}     $TENANT_NAME"
echo -e "  ${GREEN}Subdominio:${NC} https://${TENANT_NAME}.${DOMAIN}"
echo -e "  ${GREEN}Idioma:${NC}     $LANG"
echo -e "  ${GREEN}País:${NC}       $COUNTRY"
echo -e "  ${GREEN}Demo:${NC}       $DEMO"

ALL_MODULES="$DEFAULT_MODULES"
if [[ -n "$MODULES" ]]; then
    ALL_MODULES="$DEFAULT_MODULES,$MODULES"
fi

# Deduplicar y normalizar
ALL_MODULES=$(echo "$ALL_MODULES" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sed '/^$/d' | awk '!seen[$0]++' | paste -sd ',' -)
[[ -n "$ALL_MODULES" ]] && echo -e "  ${GREEN}Módulos:${NC}    $ALL_MODULES"
echo ""

# =============================================================================
# PASO 1: Verificar que la BD no existe
# =============================================================================
echo -e "${YELLOW}[1/5] Verificando disponibilidad...${NC}"

if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$TENANT_NAME"; then
    echo -e "${RED}  ✗ Error: La base de datos '$TENANT_NAME' ya existe${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Nombre de BD disponible${NC}"

# =============================================================================
# PASO 2: Crear Base de Datos en Odoo
# =============================================================================
echo -e "${YELLOW}[2/5] Creando base de datos en Odoo...${NC}"

echo "  Creando BD '$TENANT_NAME'..."

# Detectar usuario de PostgreSQL para Odoo
PG_USER=$(sudo -u postgres psql -t -c "SELECT usename FROM pg_user WHERE usename NOT IN ('postgres') LIMIT 1;" | tr -d ' ')
if [[ -z "$PG_USER" ]]; then
    PG_USER="odoo"
fi
echo "  Usuario PostgreSQL: $PG_USER"

# Método: Duplicar una BD existente como plantilla (más rápido y confiable)
# Usamos 'tcs' como plantilla base

TEMPLATE_DB="tcs"

# Verificar que existe la plantilla
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$TEMPLATE_DB"; then
    echo -e "${YELLOW}  ⚠ BD plantilla '$TEMPLATE_DB' no existe, creando BD desde cero...${NC}"
    
    # Crear BD vacía
    sudo -u postgres createdb -O "$PG_USER" "$TENANT_NAME"
    
    # Inicializar con odoo-bin (puede tardar)
    echo "  Inicializando Odoo (esto puede tardar varios minutos)..."
    
    # Parar Odoo temporalmente para liberar puerto
    systemctl stop odoo
    sleep 2
    
    if [[ "$DEMO" == "True" ]]; then
        sudo -u odoo /usr/bin/odoo -c /etc/odoo/odoo.conf -d "$TENANT_NAME" -i base --stop-after-init --load-language="$LANG" 2>&1 | tail -5
    else
        sudo -u odoo /usr/bin/odoo -c /etc/odoo/odoo.conf -d "$TENANT_NAME" -i base --stop-after-init --without-demo=all --load-language="$LANG" 2>&1 | tail -5
    fi
    
    # Reiniciar Odoo
    systemctl start odoo
    sleep 3
else
    # Duplicar plantilla (mucho más rápido)
    echo "  Duplicando desde plantilla '$TEMPLATE_DB'..."
    
    # Terminar conexiones a la plantilla
    sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$TEMPLATE_DB' AND pid <> pg_backend_pid();" >/dev/null 2>&1 || true
    
    # Duplicar BD
    sudo -u postgres createdb -O "$PG_USER" -T "$TEMPLATE_DB" "$TENANT_NAME"
    
    echo -e "${GREEN}  ✓ BD duplicada desde plantilla${NC}"
fi

# Verificar que se creó
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$TENANT_NAME"; then
    echo -e "${RED}  ✗ Error: No se pudo crear la base de datos${NC}"
    exit 1
fi

# Actualizar datos únicos del nuevo tenant
echo "  Configurando datos del nuevo tenant..."
sudo -u postgres psql -d "$TENANT_NAME" << SQLEOF
-- Resetear password admin
UPDATE res_users SET password = '$ADMIN_PASS' WHERE login = 'admin';

-- Limpiar sessions
DELETE FROM ir_sessions;

-- Actualizar nombre de compañía
UPDATE res_company SET name = '${TENANT_NAME}' WHERE id = 1;
UPDATE res_partner SET name = '${TENANT_NAME}' WHERE id = 1;

-- Limpiar attachments de filestore (opcional, mantener estructura)
-- DELETE FROM ir_attachment WHERE store_fname IS NOT NULL;

-- Regenerar UUID para evitar conflictos
UPDATE ir_config_parameter SET value = gen_random_uuid()::text WHERE key = 'database.uuid';
SQLEOF

echo -e "${GREEN}  ✓ Base de datos creada${NC}"

# =============================================================================
# PASO 3: Crear Subdominio en Cloudflare (DNS CNAME)
# =============================================================================
echo -e "${YELLOW}[3/5] Configurando DNS en Cloudflare...${NC}"

if [[ -z "$CF_API_TOKEN" ]] || [[ -z "$CF_ZONE_ID" ]]; then
    echo -e "${YELLOW}  ⚠ Variables CF_API_TOKEN o CF_ZONE_ID no configuradas${NC}"
    echo -e "${YELLOW}  → El subdominio debe crearse manualmente en Cloudflare${NC}"
    echo -e "${YELLOW}  → CNAME: ${TENANT_NAME} → ${CF_TUNNEL_ID}.cfargotunnel.com${NC}"
else
    # Verificar si ya existe
    EXISTING_RESPONSE=$(curl -s -X GET \
        "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records?type=CNAME&name=${TENANT_NAME}.${DOMAIN}" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json")
    
    EXISTING_COUNT=$(echo "$EXISTING_RESPONSE" | python3 -c "import sys,json; r=json.load(sys.stdin); print(len(r.get('result',[])))" 2>/dev/null || echo "0")
    
    if [[ "$EXISTING_COUNT" -gt 0 ]]; then
        echo -e "${YELLOW}  ⚠ Registro DNS ya existe para ${TENANT_NAME}.${DOMAIN}${NC}"
    else
        # Crear CNAME apuntando al tunnel
        CREATE_RESPONSE=$(curl -s -X POST \
            "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records" \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/json" \
            --data "{
                \"type\": \"CNAME\",
                \"name\": \"${TENANT_NAME}\",
                \"content\": \"${CF_TUNNEL_ID}.cfargotunnel.com\",
                \"ttl\": 1,
                \"proxied\": true,
                \"comment\": \"Auto-created for Odoo tenant ${TENANT_NAME}\"
            }")
        
        SUCCESS=$(echo "$CREATE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null || echo "False")
        
        if [[ "$SUCCESS" == "True" ]]; then
            echo -e "${GREEN}  ✓ Registro DNS creado: ${TENANT_NAME}.${DOMAIN}${NC}"
        else
            ERROR_MSG=$(echo "$CREATE_RESPONSE" | python3 -c "import sys,json; errs=json.load(sys.stdin).get('errors',[]); print(errs[0].get('message','Unknown') if errs else 'Unknown')" 2>/dev/null || echo "Unknown error")
            echo -e "${RED}  ✗ Error creando DNS: $ERROR_MSG${NC}"
            echo -e "${YELLOW}  → Crear manualmente CNAME: ${TENANT_NAME} → ${CF_TUNNEL_ID}.cfargotunnel.com${NC}"
        fi
    fi
fi

# =============================================================================
# PASO 4: Configurar parámetros del sistema en Odoo
# =============================================================================
echo -e "${YELLOW}[4/5] Configurando parámetros del tenant...${NC}"

CONFIG_SCRIPT=$(cat << 'PYEOF'
import xmlrpc.client
import sys
import os

url = os.environ.get('ODOO_URL')
db = os.environ.get('TENANT_NAME')
domain = os.environ.get('DOMAIN')
password = os.environ.get('ADMIN_PASS')

try:
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, 'admin', password, {})
    
    if not uid:
        print("  ⚠ No se pudo autenticar", file=sys.stderr)
        sys.exit(0)
    
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    
    base_url = f"https://{db}.{domain}"
    
    # Configurar parámetros
    models.execute_kw(db, uid, password, 'ir.config_parameter', 'set_param', ['web.base.url', base_url])
    models.execute_kw(db, uid, password, 'ir.config_parameter', 'set_param', ['web.base.url.freeze', 'True'])
    models.execute_kw(db, uid, password, 'ir.config_parameter', 'set_param', ['mail.catchall.domain', f'{db}.{domain}'])
    
    print(f"  ✓ web.base.url = {base_url}")
    
except Exception as e:
    print(f"  ⚠ Error: {e}", file=sys.stderr)
PYEOF
)

export DOMAIN
echo "$CONFIG_SCRIPT" | python3

# =============================================================================
# PASO 5: Instalar módulos adicionales (si se especificaron)
# =============================================================================
if [[ -n "$ALL_MODULES" ]]; then
    echo -e "${YELLOW}[5/5] Instalando módulos: $ALL_MODULES${NC}"
    
    INSTALL_SCRIPT=$(cat << 'PYEOF'
import xmlrpc.client
import sys
import os

url = os.environ.get('ODOO_URL')
db = os.environ.get('TENANT_NAME')
password = os.environ.get('ADMIN_PASS')
modules = os.environ.get('MODULES', '').split(',')

try:
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, 'admin', password, {})
    
    if not uid:
        print("  ⚠ No se pudo autenticar", file=sys.stderr)
        sys.exit(1)
    
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    
    for module in modules:
        module = module.strip()
        if not module:
            continue
            
        # Buscar el módulo
        mod_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search', 
            [[['name', '=', module]]])
        
        if not mod_ids:
            print(f"  ⚠ Módulo '{module}' no encontrado")
            continue
        
        # Revisar estado antes de instalar
        states = models.execute_kw(
            db, uid, password,
            'ir.module.module', 'read',
            [mod_ids, ['state']]
        )
        current_state = states[0].get('state') if states else None

        if current_state == 'installed':
            print(f"  ✓ Módulo '{module}' ya está instalado")
            continue

        # Instalar
        models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_install', [mod_ids])
        print(f"  ✓ Módulo '{module}' instalado")
        
except Exception as e:
    print(f"  ⚠ Error instalando módulos: {e}", file=sys.stderr)
PYEOF
    )
    
    export MODULES="$ALL_MODULES"
    echo "$INSTALL_SCRIPT" | python3
else
    echo -e "${YELLOW}[5/5] Sin módulos adicionales${NC}"
fi

# =============================================================================
# RESUMEN FINAL
# =============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✓ TENANT CREADO EXITOSAMENTE                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}URL:${NC}        https://${TENANT_NAME}.${DOMAIN}"
echo -e "  ${BLUE}Usuario:${NC}    admin"
echo -e "  ${BLUE}Password:${NC}   ${ADMIN_PASS}"
echo -e "  ${BLUE}Base datos:${NC} ${TENANT_NAME}"
echo ""
echo -e "  ${YELLOW}Nota: El DNS puede tardar unos minutos en propagarse${NC}"
echo ""
