#!/bin/bash
# =============================================================================
# SCRIPT PARA ELIMINAR TENANTS ODOO
# Elimina: Base de datos + Subdominio en Cloudflare
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Cargar credenciales de Cloudflare
CF_CRED_FILE="/opt/odoo/scripts/.cf_credentials"
if [[ -f "$CF_CRED_FILE" ]]; then
    source "$CF_CRED_FILE"
fi
CF_API_TOKEN="${cloudflare_api_token:-$CF_API_TOKEN}"
CF_ZONE_ID="${CF_ZONE_ID:-4a83b88793ac3688486ace69b6ae80f9}"

DOMAIN="sajet.us"
ODOO_MASTER_PASSWORD="${ODOO_MASTER_PASSWORD:-admin}"
ODOO_URL="http://localhost:8069"

usage() {
    echo "Uso: $0 <nombre_tenant> [--force]"
    echo ""
    echo "Elimina una base de datos Odoo y su subdominio en Cloudflare"
    echo ""
    echo "Opciones:"
    echo "  --force    No pedir confirmación"
    exit 1
}

TENANT_NAME=""
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force) FORCE=true; shift ;;
        --help|-h) usage ;;
        -*) echo -e "${RED}Opción desconocida: $1${NC}"; usage ;;
        *) TENANT_NAME="$1"; shift ;;
    esac
done

if [[ -z "$TENANT_NAME" ]]; then
    echo -e "${RED}Error: Debe especificar nombre del tenant${NC}"
    usage
fi

# Normalizar
TENANT_NAME=$(echo "$TENANT_NAME" | tr '[:upper:]' '[:lower:]')

echo ""
echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║              ⚠ ELIMINAR TENANT ODOO                       ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${YELLOW}Tenant:${NC}     $TENANT_NAME"
echo -e "  ${YELLOW}Subdominio:${NC} ${TENANT_NAME}.${DOMAIN}"
echo ""

if [[ "$FORCE" != "true" ]]; then
    echo -e "${RED}⚠ ADVERTENCIA: Esta acción es IRREVERSIBLE${NC}"
    echo -e "${RED}  Se eliminarán TODOS los datos del tenant${NC}"
    echo ""
    read -p "¿Está seguro? Escriba '$TENANT_NAME' para confirmar: " CONFIRM
    
    if [[ "$CONFIRM" != "$TENANT_NAME" ]]; then
        echo -e "${YELLOW}Operación cancelada${NC}"
        exit 0
    fi
fi

# =============================================================================
# PASO 1: Verificar que la BD existe
# =============================================================================
echo -e "${YELLOW}[1/3] Verificando base de datos...${NC}"

if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$TENANT_NAME"; then
    echo -e "${YELLOW}  ⚠ La base de datos '$TENANT_NAME' no existe${NC}"
else
    echo -e "${GREEN}  ✓ BD encontrada${NC}"
fi

# =============================================================================
# PASO 2: Eliminar Base de Datos
# =============================================================================
echo -e "${YELLOW}[2/3] Eliminando base de datos...${NC}"

DELETE_SCRIPT=$(cat << 'PYEOF'
import xmlrpc.client
import sys
import os

url = os.environ.get('ODOO_URL')
master_pwd = os.environ.get('ODOO_MASTER_PASSWORD')
db_name = os.environ.get('TENANT_NAME')

try:
    db = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/db")
    
    # Verificar si existe
    dbs = db.list()
    if db_name not in dbs:
        print(f"  ⚠ BD '{db_name}' no encontrada en Odoo")
        sys.exit(0)
    
    # Eliminar
    db.drop(master_pwd, db_name)
    print(f"  ✓ BD '{db_name}' eliminada")
    
except Exception as e:
    print(f"  ✗ Error: {e}", file=sys.stderr)
    # Intentar con psql directamente
    sys.exit(1)
PYEOF
)

export ODOO_URL ODOO_MASTER_PASSWORD TENANT_NAME

if ! echo "$DELETE_SCRIPT" | python3; then
    echo -e "${YELLOW}  Intentando eliminación directa con PostgreSQL...${NC}"
    
    # Terminar conexiones activas
    sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$TENANT_NAME';" 2>/dev/null || true
    
    # Eliminar BD
    if sudo -u postgres dropdb "$TENANT_NAME" 2>/dev/null; then
        echo -e "${GREEN}  ✓ BD eliminada con PostgreSQL${NC}"
    else
        echo -e "${RED}  ✗ No se pudo eliminar la BD${NC}"
    fi
fi

# =============================================================================
# PASO 3: Eliminar DNS en Cloudflare
# =============================================================================
echo -e "${YELLOW}[3/3] Eliminando DNS de Cloudflare...${NC}"

if [[ -z "$CF_API_TOKEN" ]] || [[ -z "$CF_ZONE_ID" ]]; then
    echo -e "${YELLOW}  ⚠ Variables CF no configuradas, eliminar DNS manualmente${NC}"
else
    # Buscar el registro
    RECORD_RESPONSE=$(curl -s -X GET \
        "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records?type=CNAME&name=${TENANT_NAME}.${DOMAIN}" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json")
    
    RECORD_ID=$(echo "$RECORD_RESPONSE" | python3 -c "import sys,json; r=json.load(sys.stdin).get('result',[]); print(r[0]['id'] if r else '')" 2>/dev/null || echo "")
    
    if [[ -z "$RECORD_ID" ]]; then
        echo -e "${YELLOW}  ⚠ Registro DNS no encontrado${NC}"
    else
        # Eliminar
        DELETE_RESPONSE=$(curl -s -X DELETE \
            "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records/${RECORD_ID}" \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/json")
        
        SUCCESS=$(echo "$DELETE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null || echo "False")
        
        if [[ "$SUCCESS" == "True" ]]; then
            echo -e "${GREEN}  ✓ Registro DNS eliminado${NC}"
        else
            echo -e "${RED}  ✗ Error eliminando DNS${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✓ TENANT ELIMINADO                           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
