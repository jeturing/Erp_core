# Odoo 17 to 19 Automated Migration Tool

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


Herramienta Python para **automatizar completamente la migración de módulos Odoo** de v17 a v19.

## Características

✅ Análisis automático de compatibilidad v17→v19
✅ Auto-fix automático de decoradores deprecados (@api.multi, @api.one)
✅ Actualización de manifests a v19
✅ Validación de dependencias en Odoo 19
✅ Generación de reportes detallados en JSON
✅ Migración de módulos individuales o en lote
✅ Logging completo de todas las operaciones

## Instalación

### Requisitos
- Python 3.8+
- No requiere dependencias externas

### Setup
```bash
cd /path/to/Erp_core
chmod +x scripts/odoo_migration_tool.py
```

## Uso

### Migrar un módulo específico
```bash
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --target extra-addons/V19 \
    --module account_custom
```

### Migrar todos los módulos
```bash
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --target extra-addons/V19 \
    --all
```

### Solo analizar (sin cambios)
```bash
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --module account_custom \
    --analyze-only
```

### Generar reporte de compatibilidad
```bash
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --report \
    --output compatibility_report.json
```

## Qué Detecta y Corrige

| Issue | Auto-Fix |
|-------|----------|
| @api.multi | ✅ Removido |
| @api.one | ✅ Removido |
| Versión v17 | ✅ Actualizado |
| License faltante | ✅ Agregado |
| Dependencias inválidas | ⚠️ Warning |

## Reportes

La herramienta genera:
- `migration_report.json` - Detalles de la migración
- `compatibility_report.json` - Estado de compatibilidad
- `odoo_migration.log` - Log completo de ejecución

## Workflow Recomendado

```bash
# 1. Generar reporte inicial
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --report \
    --output compatibility_baseline.json

# 2. Migrar módulos (por prioridad)
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --target extra-addons/V19 \
    --module account_custom

# 3. Generar reporte final
python scripts/odoo_migration_tool.py \
    --source extra-addons/V19 \
    --report \
    --output migration_final_report.json

# 4. Validar en servidor Odoo 19
```

## Troubleshooting

### Script no ejecutable
```bash
chmod +x scripts/odoo_migration_tool.py
```

### Ver errores detallados
```bash
tail -f odoo_migration.log
```

### Revisar compatibilidad
```bash
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --analyze-only \
    --module [nombre]
```

## Documentación Relacionada

- `docs/ODOO_MIGRATION_V17_TO_V19.md` - Plan estratégico completo
- `extra-addons/ODOO_MIGRATION_TRACKER.md` - Tracking de módulos
- `extra-addons/MODULE_MIGRATION_TEMPLATE.md` - Template por módulo

## Licencia

LGPL-3

---

Versión: 1.0
Última actualización: 2026-02-16
