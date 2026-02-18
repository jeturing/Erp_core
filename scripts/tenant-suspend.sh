#!/usr/bin/env bash
#═══════════════════════════════════════════════════════════════════
#  tenant-suspend.sh — Gestión de suspensión/reactivación de tenants
#  
#  Uso:
#    ./tenant-suspend.sh suspend <subdomain> [reason] [owner_email]
#    ./tenant-suspend.sh reactivate <subdomain>
#    ./tenant-suspend.sh list
#    ./tenant-suspend.sh check <subdomain>
#    ./tenant-suspend.sh full-suspend <subdomain> [reason] [owner_email]
#    ./tenant-suspend.sh full-reactivate <subdomain>
#
#  full-suspend: Suspende a nivel Nginx + desactiva usuarios en Odoo
#  full-reactivate: Reactiva Nginx + reactiva usuarios en Odoo
#═══════════════════════════════════════════════════════════════════
set -euo pipefail

API_BASE="${API_BASE:-https://sajet.us}"
API_KEY="${PROVISIONING_API_KEY:-prov-key-2026-secure}"
ODOO_HOST="${ODOO_HOST:-10.10.10.100}"
ODOO_DB_USER="${ODOO_DB_USER:-Jeturing}"
ODOO_DB_PASS="${ODOO_DB_PASS:-123Abcd.}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    echo -e "${CYAN}━━━ Tenant Suspension Manager ━━━${NC}"
    echo ""
    echo "Uso:"
    echo "  $0 suspend <subdomain> [reason] [owner_email]"
    echo "  $0 reactivate <subdomain>"
    echo "  $0 list"
    echo "  $0 check <subdomain>"
    echo "  $0 full-suspend <subdomain> [reason] [owner_email]"
    echo "  $0 full-reactivate <subdomain>"
    echo ""
    echo "Razones válidas:"
    echo "  payment_failed  - Cobro rechazado"
    echo "  past_due        - Pagos vencidos"
    echo "  cancelled       - Suscripción cancelada"
    echo "  expired         - Período de prueba expirado"
    echo "  manual          - Suspendido manualmente"
    echo ""
    echo "Ejemplos:"
    echo "  $0 suspend acme payment_failed admin@acme.com"
    echo "  $0 full-suspend demo expired demo@correo.com"
    echo "  $0 reactivate acme"
    exit 1
}

# ── Suspend: Solo Nginx redirect ──
cmd_suspend() {
    local subdomain="$1"
    local reason="${2:-payment_failed}"
    local owner_email="${3:-}"
    
    echo -e "${YELLOW}🔴 Suspendiendo tenant: ${subdomain}${NC}"
    echo "   Razón: ${reason}"
    echo "   Owner: ${owner_email:-N/A}"
    
    local response
    response=$(curl -s -X POST \
        "${API_BASE}/api/tenant-suspension/${subdomain}?reason=${reason}&owner_email=${owner_email}&x_api_key=${API_KEY}")
    
    local success
    success=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success',''))" 2>/dev/null || echo "")
    
    if [ "$success" = "True" ]; then
        echo -e "${GREEN}✅ Tenant ${subdomain} suspendido exitosamente${NC}"
        echo "   → Visitantes verán: 'Estaremos de regreso pronto'"
        echo "   → Propietario verá: Página de reactivación de pago"
    else
        echo -e "${RED}❌ Error suspendiendo tenant${NC}"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    fi
}

# ── Reactivate: Solo Nginx redirect ──
cmd_reactivate() {
    local subdomain="$1"
    
    echo -e "${GREEN}🟢 Reactivando tenant: ${subdomain}${NC}"
    
    local response
    response=$(curl -s -X DELETE \
        "${API_BASE}/api/tenant-suspension/${subdomain}?x_api_key=${API_KEY}")
    
    local success
    success=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success',''))" 2>/dev/null || echo "")
    
    if [ "$success" = "True" ]; then
        echo -e "${GREEN}✅ Tenant ${subdomain} reactivado${NC}"
    else
        echo -e "${RED}❌ Error reactivando${NC}"
        echo "$response"
    fi
}

# ── Full Suspend: Nginx + Odoo users ──
cmd_full_suspend() {
    local subdomain="$1"
    local reason="${2:-payment_failed}"
    local owner_email="${3:-}"
    
    echo -e "${YELLOW}🔴 Suspensión COMPLETA de ${subdomain}${NC}"
    echo ""
    
    # 1. Suspender a nivel Nginx (redirección)
    echo "  [1/2] Activando redirección Nginx..."
    cmd_suspend "$subdomain" "$reason" "$owner_email"
    echo ""
    
    # 2. Desactivar usuarios en Odoo via provisioning API
    echo "  [2/2] Desactivando usuarios Odoo..."
    local response
    response=$(curl -s -X PUT \
        "${API_BASE}/api/provisioning/tenant/suspend" \
        -H "Content-Type: application/json" \
        -H "X-API-KEY: ${API_KEY}" \
        -d "{\"subdomain\":\"${subdomain}\",\"suspend\":true,\"reason\":\"${reason}\"}")
    
    local status
    status=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
    
    if [ "$status" = "suspended" ]; then
        echo -e "${GREEN}  ✅ Usuarios Odoo desactivados${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Respuesta Odoo: ${response}${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}━━━ Suspensión completa de ${subdomain} finalizada ━━━${NC}"
}

# ── Full Reactivate: Nginx + Odoo users ──
cmd_full_reactivate() {
    local subdomain="$1"
    
    echo -e "${GREEN}🟢 Reactivación COMPLETA de ${subdomain}${NC}"
    echo ""
    
    # 1. Reactivar usuarios en Odoo
    echo "  [1/2] Reactivando usuarios Odoo..."
    local response
    response=$(curl -s -X PUT \
        "${API_BASE}/api/provisioning/tenant/suspend" \
        -H "Content-Type: application/json" \
        -H "X-API-KEY: ${API_KEY}" \
        -d "{\"subdomain\":\"${subdomain}\",\"suspend\":false}")
    
    local status
    status=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
    
    if [ "$status" = "active" ]; then
        echo -e "${GREEN}  ✅ Usuarios Odoo reactivados${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Respuesta Odoo: ${response}${NC}"
    fi
    echo ""
    
    # 2. Quitar redirección Nginx
    echo "  [2/2] Quitando redirección Nginx..."
    cmd_reactivate "$subdomain"
    
    echo ""
    echo -e "${GREEN}━━━ Reactivación completa de ${subdomain} finalizada ━━━${NC}"
}

# ── List ──
cmd_list() {
    echo -e "${CYAN}━━━ Tenants Suspendidos ━━━${NC}"
    echo ""
    
    local response
    response=$(curl -s "${API_BASE}/api/tenant-suspensions?x_api_key=${API_KEY}")
    
    local total
    total=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total',0))" 2>/dev/null || echo "0")
    
    if [ "$total" = "0" ]; then
        echo -e "${GREEN}  ✅ No hay tenants suspendidos${NC}"
        return
    fi
    
    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tenants = data.get('tenants', {})
print(f'Total: {len(tenants)}')
print()
print(f'{\"Subdominio\":<20} {\"Razón\":<20} {\"Owner\":<30} {\"Fecha\"}')
print('─' * 90)
for name, info in tenants.items():
    print(f'{name:<20} {info.get(\"reason\",\"?\"):<20} {info.get(\"owner_email\",\"?\"):<30} {info.get(\"suspended_at\",\"?\")}')
"
}

# ── Check ──
cmd_check() {
    local subdomain="$1"
    
    local response
    response=$(curl -s "${API_BASE}/api/tenant-status/${subdomain}")
    
    local status
    status=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
    
    if [ "$status" = "suspended" ]; then
        echo -e "${RED}🔴 ${subdomain}: SUSPENDIDO${NC}"
        echo "$response" | python3 -m json.tool 2>/dev/null
    elif [ "$status" = "active" ]; then
        echo -e "${GREEN}🟢 ${subdomain}: ACTIVO${NC}"
    else
        echo -e "${YELLOW}⚠️  ${subdomain}: ${status}${NC}"
    fi
}

# ── Main ──
[ $# -lt 1 ] && usage

case "$1" in
    suspend)
        [ $# -lt 2 ] && usage
        cmd_suspend "${2}" "${3:-payment_failed}" "${4:-}"
        ;;
    reactivate)
        [ $# -lt 2 ] && usage
        cmd_reactivate "${2}"
        ;;
    full-suspend)
        [ $# -lt 2 ] && usage
        cmd_full_suspend "${2}" "${3:-payment_failed}" "${4:-}"
        ;;
    full-reactivate)
        [ $# -lt 2 ] && usage
        cmd_full_reactivate "${2}"
        ;;
    list)
        cmd_list
        ;;
    check)
        [ $# -lt 2 ] && usage
        cmd_check "${2}"
        ;;
    *)
        usage
        ;;
esac
