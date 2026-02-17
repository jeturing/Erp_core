#!/bin/bash
#
# 🚀 Bulk Migration Script - Odoo 17 → 19
# Migra TODOS los módulos automáticamente y genera reporte de validación
#
# Uso: ./scripts/bulk_migrate_all.sh
#

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorios
SOURCE_DIR="extra-addons/V17"
TARGET_DIR="extra-addons/V19"
PYTHON_TOOL="scripts/odoo_migration_tool.py"
REPORTS_DIR="migration_reports"

# Crear directorio de reportes
mkdir -p "$REPORTS_DIR"

# Timestamps
START_TIME=$(date +%s)
START_DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 BULK MIGRATION - Odoo 17 → 19${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Inicio: $START_DATE"
echo "Origen: $SOURCE_DIR"
echo "Destino: $TARGET_DIR"
echo ""

# Validar directorios
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ ERROR: Directorio origen no existe: $SOURCE_DIR${NC}"
    exit 1
fi

if [ ! -f "$PYTHON_TOOL" ]; then
    echo -e "${RED}❌ ERROR: Herramienta no encontrada: $PYTHON_TOOL${NC}"
    exit 1
fi

# Contar módulos
MODULES=$(find "$SOURCE_DIR" -maxdepth 1 -type d -exec test -f "{}/__manifest__.py" \; -print | wc -l)
echo -e "${YELLOW}📊 Módulos encontrados: $MODULES${NC}"
echo ""

if [ $MODULES -eq 0 ]; then
    echo -e "${RED}⚠️  No se encontraron módulos en $SOURCE_DIR${NC}"
    echo "Asegúrate de que existen directorios con __manifest__.py"
    exit 1
fi

# Crear directorio destino
mkdir -p "$TARGET_DIR"

# Array para tracking
TOTAL_SUCCESS=0
TOTAL_FAILED=0
TOTAL_FIXED=0
FAILED_MODULES=()

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔄 FASE 1: MIGRACIÓN AUTOMÁTICA${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Iterar sobre cada módulo
MODULE_COUNT=0
for module_dir in "$SOURCE_DIR"/*; do
    if [ -d "$module_dir" ]; then
        module_name=$(basename "$module_dir")

        # Verificar que tiene __manifest__.py
        if [ ! -f "$module_dir/__manifest__.py" ]; then
            continue
        fi

        MODULE_COUNT=$((MODULE_COUNT + 1))
        PERCENT=$((MODULE_COUNT * 100 / MODULES))

        echo -e "${YELLOW}[$MODULE_COUNT/$MODULES - ${PERCENT}%]${NC} Migrando: ${BLUE}$module_name${NC}"

        # Ejecutar migración
        if python "$PYTHON_TOOL" \
            --source "$SOURCE_DIR" \
            --target "$TARGET_DIR" \
            --module "$module_name" \
            --output "$REPORTS_DIR/${module_name}_migration.json" > /dev/null 2>&1; then

            echo -e "  ${GREEN}✅ Migración exitosa${NC}"
            TOTAL_SUCCESS=$((TOTAL_SUCCESS + 1))

            # Contar fixes aplicados
            if [ -f "$REPORTS_DIR/${module_name}_migration.json" ]; then
                FIXES=$(python -c "import json; data=json.load(open('$REPORTS_DIR/${module_name}_migration.json')); print(sum(1 for m in data.get('modules', []) if m.get('status')=='completed' and any(s['name']=='fix' for s in m.get('steps', []))))" 2>/dev/null || echo "0")
                if [ "$FIXES" != "0" ]; then
                    echo -e "  📝 Fixes aplicados: $FIXES"
                    TOTAL_FIXED=$((TOTAL_FIXED + FIXES))
                fi
            fi
        else
            echo -e "  ${RED}❌ Error en migración${NC}"
            TOTAL_FAILED=$((TOTAL_FAILED + 1))
            FAILED_MODULES+=("$module_name")
        fi

        echo ""
    fi
done

# ============================================
# FASE 2: VALIDACIÓN
# ============================================

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}✅ FASE 2: VALIDACIÓN DE MÓDULOS MIGRADOS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

VALIDATION_PASSED=0
VALIDATION_FAILED=0

for module_dir in "$TARGET_DIR"/*; do
    if [ -d "$module_dir" ]; then
        module_name=$(basename "$module_dir")
        echo -n "Validando: $module_name ... "

        # Validación 1: Existe __manifest__.py
        if [ ! -f "$module_dir/__manifest__.py" ]; then
            echo -e "${RED}❌ Falta __manifest__.py${NC}"
            VALIDATION_FAILED=$((VALIDATION_FAILED + 1))
            continue
        fi

        # Validación 2: Versión actualizada a v19
        VERSION=$(grep -oP "(?<='version':\s')[^']*" "$module_dir/__manifest__.py" || echo "")
        if [[ "$VERSION" == *"19.0"* ]]; then
            echo -n " ${GREEN}✅ versión:$VERSION${NC} "
        else
            echo -n " ${YELLOW}⚠️ versión:$VERSION${NC} "
        fi

        # Validación 3: No tiene @api.multi o @api.one
        MULTI_COUNT=$(grep -r "@api.multi" "$module_dir" 2>/dev/null | wc -l)
        ONE_COUNT=$(grep -r "@api.one" "$module_dir" 2>/dev/null | wc -l)

        if [ $MULTI_COUNT -eq 0 ] && [ $ONE_COUNT -eq 0 ]; then
            echo -e " ${GREEN}✅ No deprecados${NC}"
            VALIDATION_PASSED=$((VALIDATION_PASSED + 1))
        else
            echo -e " ${RED}❌ Encontrados: @api.multi=$MULTI_COUNT @api.one=$ONE_COUNT${NC}"
            VALIDATION_FAILED=$((VALIDATION_FAILED + 1))
        fi
    fi
done

# ============================================
# FASE 3: REPORTE CONSOLIDADO
# ============================================

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📊 FASE 3: REPORTE CONSOLIDADO${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Generar reporte master
REPORT_FILE="$REPORTS_DIR/MASTER_MIGRATION_REPORT.md"

cat > "$REPORT_FILE" << EOF
# 🚀 Master Migration Report - Odoo 17 → 19

**Fecha**: $(date '+%Y-%m-%d %H:%M:%S')
**Origen**: $SOURCE_DIR
**Destino**: $TARGET_DIR

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Módulos encontrados | $MODULES |
| Migraciones exitosas | $TOTAL_SUCCESS |
| Migraciones fallidas | $TOTAL_FAILED |
| Tasa de éxito | $((TOTAL_SUCCESS * 100 / MODULES))% |
| Validaciones pasadas | $VALIDATION_PASSED |
| Validaciones fallidas | $VALIDATION_FAILED |
| Total de fixes aplicados | $TOTAL_FIXED |

---

## ✅ Módulos Migrados Exitosamente

$(ls "$TARGET_DIR" 2>/dev/null | sed 's/^/- /' || echo "Ninguno")

---

## ❌ Módulos con Errores

$(if [ ${#FAILED_MODULES[@]} -gt 0 ]; then
    for mod in "${FAILED_MODULES[@]}"; do
        echo "- $mod"
    done
else
    echo "Ninguno ✅"
fi)

---

## 📋 Próximos Pasos

1. **Revisión manual**: Revisar módulos fallidos
2. **Testing**: Instalar módulos en Odoo 19 test
3. **Validación**: Verificar flujos principales
4. **Merge**: Hacer PR a main

---

## 📁 Reportes Detallados

Los reportes individuales están en: $REPORTS_DIR/

EOF

echo -e "${GREEN}✅ Reporte guardado: $REPORT_FILE${NC}"
cat "$REPORT_FILE"
echo ""

# ============================================
# RESUMEN FINAL
# ============================================

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🏁 RESUMEN FINAL${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Tiempo total: ${YELLOW}${MINUTES}m ${SECONDS}s${NC}"
echo -e "Módulos procesados: ${YELLOW}$TOTAL_SUCCESS${NC} exitosos, ${RED}$TOTAL_FAILED${NC} fallidos"
echo -e "Validación: ${YELLOW}$VALIDATION_PASSED${NC} pasadas, ${RED}$VALIDATION_FAILED${NC} fallidas"
echo -e "Fixes aplicados: ${YELLOW}$TOTAL_FIXED${NC}"
echo ""

if [ $TOTAL_FAILED -eq 0 ] && [ $VALIDATION_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ MIGRACIÓN COMPLETADA EXITOSAMENTE${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️ MIGRACIÓN COMPLETADA CON ADVERTENCIAS${NC}"
    echo -e "   Revisar: $REPORT_FILE"
    exit 1
fi
