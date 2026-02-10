#!/bin/bash
# =============================================================================
# SCRIPT PARA LISTAR TENANTS ODOO
# =============================================================================

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DOMAIN="sajet.us"
ODOO_URL="http://localhost:8069"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   TENANTS ODOO                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Obtener lista de BDs
DBS=$(python3 << 'PYEOF'
import xmlrpc.client
import os

url = os.environ.get('ODOO_URL', 'http://localhost:8069')

try:
    db = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/db")
    dbs = db.list()
    for d in sorted(dbs):
        print(d)
except:
    pass
PYEOF
)

if [[ -z "$DBS" ]]; then
    # Fallback a PostgreSQL
    DBS=$(sudo -u postgres psql -t -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres') ORDER BY datname;" 2>/dev/null | tr -d ' ')
fi

if [[ -z "$DBS" ]]; then
    echo -e "${YELLOW}No se encontraron bases de datos${NC}"
    exit 0
fi

printf "${GREEN}%-25s %-40s${NC}\n" "BASE DE DATOS" "URL"
printf "%-25s %-40s\n" "-------------------------" "----------------------------------------"

while IFS= read -r db; do
    [[ -z "$db" ]] && continue
    printf "%-25s https://%s.%s\n" "$db" "$db" "$DOMAIN"
done <<< "$DBS"

echo ""
TOTAL=$(echo "$DBS" | grep -c . || echo 0)
echo -e "${BLUE}Total: $TOTAL tenant(s)${NC}"
echo ""
