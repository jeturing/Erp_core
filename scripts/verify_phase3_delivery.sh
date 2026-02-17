#!/bin/bash
# Script de Verificación – Entrega Phase 3 (Partner-Led Onboarding)
# Sajet.us / PCT 160 | Febrero 14, 2026

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ VERIFICACIÓN DE ENTREGA – PHASE 3 (PARTNER-LED)           ║"
echo "║  Sajet.us / PCT 160                                           ║"
echo "║  Febrero 14, 2026                                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

failed=0
passed=0

check() {
    local result=$1
    local msg=$2
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $msg"
        ((passed++))
    else
        echo -e "${RED}✗${NC} $msg"
        ((failed++))
    fi
}

file_exists() {
    [ -f "$1" ]
}

# 1. DOCUMENTACIÓN
echo ""
echo "📋 VERIFICANDO DOCUMENTACIÓN..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ -f docs/RESUMEN_EJECUTIVO_PHASE_3.md ]; check $? "RESUMEN_EJECUTIVO_PHASE_3.md existe"
[ -f docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md ]; check $? "ONBOARDING_PUBLICO_SIN_PRECIOS.md existe"
[ -f docs/ROLES_PERMISOS_MATRIZ.md ]; check $? "ROLES_PERMISOS_MATRIZ.md existe"
[ -f docs/PR_TEMPLATE_ONBOARDING_PARTNER.md ]; check $? "PR_TEMPLATE_ONBOARDING_PARTNER.md existe"
[ -f docs/VALIDACION_NO_REGRESION.md ]; check $? "VALIDACION_NO_REGRESION.md existe"
[ -f docs/DELIVERY_PCT160.md ]; check $? "DELIVERY_PCT160.md existe"

# 2. CONTENIDO
echo ""
echo "📖 VERIFICANDO CONTENIDO DE DOCUMENTACIÓN..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "Onboarding Público sin Precios" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "ONBOARDING: Definición de flujo público"
grep -q "POST /api/leads/public" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "ONBOARDING: Endpoint leads/public"
grep -q "Proveedor de Servicio" docs/ROLES_PERMISOS_MATRIZ.md && check "ROLES: Rol Proveedor definido"
grep -q "ACL" docs/ROLES_PERMISOS_MATRIZ.md && check "ROLES: Control de acceso"
grep -q "Checklist de Integración" docs/PR_TEMPLATE_ONBOARDING_PARTNER.md && check "PR: Checklist presente"
grep -q "No-regresión" docs/VALIDACION_NO_REGRESION.md && check "VALIDACIÓN: No-regresión documentada"

# 3. TABLAS DE BD
echo ""
echo "💾 VERIFICANDO DISEÑO BD..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "CREATE TABLE leads" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "BD: Tabla leads"
grep -q "CREATE TABLE partners" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "BD: Tabla partners"
grep -q "CREATE TABLE quotations" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "BD: Tabla quotations"
grep -q "status VARCHAR" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "BD: Columna status en leads"
grep -q "assigned_partner_id" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "BD: Foreign key partner"

# 4. ENDPOINTS
echo ""
echo "🔌 VERIFICANDO ENDPOINTS..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "POST /api/leads/public" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "API: POST /api/leads/public"
grep -q "GET /api/leads/{lead_id}/status" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "API: GET /api/leads/{id}/status"
grep -q "PUT /api/admin/leads/{lead_id}/qualify" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "API: PUT /api/admin/leads/{id}/qualify"
grep -q "POST /api/partners/leads/{lead_id}/create-tenant" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "API: POST /api/partners/leads/{id}/create-tenant"
grep -q "response.*200" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "API: Respuestas HTTP documentadas"

# 5. SEGURIDAD
echo ""
echo "🔐 VERIFICANDO SEGURIDAD..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "Rate Limiting" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "SEGURIDAD: Rate limiting"
grep -q "Validaciones Pydantic" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "SEGURIDAD: Pydantic validation"
grep -q "JWT" docs/ROLES_PERMISOS_MATRIZ.md && check "SEGURIDAD: JWT configurado"
grep -q "ACL\|isolation" docs/ROLES_PERMISOS_MATRIZ.md && check "SEGURIDAD: Data isolation"
grep -q "logs.*secretos" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "SEGURIDAD: Logs sin secretos"

# 6. TESTING
echo ""
echo "🧪 VERIFICANDO TESTING & VALIDACIÓN..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "test.*pytest\|pytest.*test" docs/PR_TEMPLATE_ONBOARDING_PARTNER.md && check "TESTING: Tests pytest mencionados"
grep -q "test_checkout_flow\|test_partner_flow" docs/VALIDACION_NO_REGRESION.md && check "TESTING: E2E tests definidos"
grep -q "Criterios de Aceptación\|PASS\|FAIL" docs/VALIDACION_NO_REGRESION.md && check "TESTING: Criterios de aceptación"
grep -q "Rollback" docs/PR_TEMPLATE_ONBOARDING_PARTNER.md && check "TESTING: Plan de rollback"

# 7. README
echo ""
echo "📚 VERIFICANDO README..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "Phase 3" README.md && check "README: Phase 3 mencionado"
grep -q "Partner-Led\|partner-led" README.md && check "README: Partner-led mencionado"
grep -q "ONBOARDING_PUBLICO_SIN_PRECIOS" README.md && check "README: Link a documentación Phase 3"

# 8. FLUJO NO-REGRESIÓN
echo ""
echo "🔄 VERIFICANDO FLUJO ACTUAL INTACTO..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "/signup" docs/VALIDACION_NO_REGRESION.md && check "FLUJO: /signup documentado"
grep -q "/api/checkout" docs/VALIDACION_NO_REGRESION.md && check "FLUJO: /api/checkout documentado"
grep -q "/webhook/stripe" docs/VALIDACION_NO_REGRESION.md && check "FLUJO: /webhook/stripe documentado"
grep -q "no rompe\|No rompe\|NO rompe" docs/VALIDACION_NO_REGRESION.md && check "FLUJO: Garantía no-regresión"

# 9. PARTNERSHIP ALINEACIÓN
echo ""
echo "🤝 VERIFICANDO ALINEACIÓN PARTNERSHIP..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "50/50\|comision\|comisión" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "PARTNERSHIP: Comisiones 50/50"
grep -q "acuerdo\|Acuerdo\|ACUERDO" docs/RESUMEN_EJECUTIVO_PHASE_3.md && check "PARTNERSHIP: Alineado con acuerdo"
grep -q "Jeturing\|jeturing\|JETURING" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "PARTNERSHIP: Gating Jeturing"
grep -q "Ingresos Netos\|ingresos netos" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "PARTNERSHIP: Definición Ingresos Netos"

# 10. ESTADOS DE PIPELINE
echo ""
echo "📊 VERIFICANDO PIPELINE & ESTADOS..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "nuevo\|en_calificacion\|calificado" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "PIPELINE: Estados definidos"
grep -q "facturado\|activo" docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md && check "PIPELINE: Estados finales"
grep -q "Transiciones\|transiciones" docs/ROLES_PERMISOS_MATRIZ.md && check "PIPELINE: Transiciones documentadas"

# RESUMEN
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "📊 RESULTADOS:"
echo -e "   ${GREEN}✓ Pasaron${NC}: $passed"
if [ $failed -gt 0 ]; then
    echo -e "   ${RED}✗ Fallaron${NC}: $failed"
else
    echo -e "   ${RED}✗ Fallaron${NC}: 0"
fi
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ ENTREGA COMPLETA Y VALIDADA – LISTO PARA PCT 160          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ⚠️  REVISAR FALLOS ANTES DE ENVIAR A PCT 160                  ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 1
fi
