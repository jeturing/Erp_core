# 🚀 Guía de Migración en Lote - Odoo 17 → 19

Automatiza la migración de **TODOS** los módulos Odoo de v17 a v19 con validación completa.

## 📋 Requisitos Previos

1. **Módulos V17 listos**: Deben estar en `extra-addons/V17/`
2. **Python 3.8+** instalado
3. **Estructura correcta**: Cada módulo debe tener `__manifest__.py`

```
extra-addons/
├── V17/
│   ├── account_custom/
│   │   ├── __manifest__.py      ← Obligatorio
│   │   ├── __init__.py
│   │   ├── models/
│   │   └── views/
│   ├── sale_custom/
│   └── [otros módulos...]
└── V19/          ← Se crea automáticamente
```

## ⚡ Ejecución Rápida (3 pasos)

### Paso 1: Generar Reporte de Compatibilidad Base

```bash
python scripts/odoo_migration_tool.py --source extra-addons/V17 --report --output baseline.json

# Ver resultados
cat baseline.json | jq '.modules | length'
# Resultado: número de módulos encontrados
```

### Paso 2: Migrar Todos los Módulos Automáticamente

```bash
# Opción A: Script bash (recomendado)
./scripts/bulk_migrate_all.sh

# Opción B: Manual (módulo por módulo)
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --target extra-addons/V19 \
    --all
```

### Paso 3: Validar Todos los Módulos

```bash
# Validar y generar reporte
python scripts/validate_migration.py \
    --target extra-addons/V19 \
    --report validation_report.json

# Ver resultados
cat validation_report.json | jq '.summary'
```

## 📊 Output y Reportes

### Después de migración:
```
migration_reports/
├── MASTER_MIGRATION_REPORT.md      ← Resumen de migración
├── [modulo1]_migration.json
├── [modulo2]_migration.json
└── ...
```

### Después de validación:
```
validation_report.json              ← Reporte de validación
```

## 🔍 Validaciones Automáticas

### Manifest Checks
- ✅ `__manifest__.py` existe
- ✅ Versión es 19.0.x.x.x
- ✅ License especificada
- ✅ Dependencias definidas
- ✅ Sintaxis Python válida

### Python Checks
- ✅ Sin `@api.multi` (removido en v18)
- ✅ Sin `@api.one` (removido en v17)
- ✅ Sintaxis válida en todos los archivos

### XML Checks
- ✅ XML bien formado
- ✅ Sin errores de parseo

### Structure Checks
- ✅ `__init__.py` existe en raíz
- ✅ Estructura de carpetas válida

## 📈 Ejemplo Completo

```bash
# 1. Preparación
mkdir -p extra-addons/{V17,V19}
# Copiar módulos V17 aquí

# 2. Generar baseline
python scripts/odoo_migration_tool.py --source extra-addons/V17 --report --output baseline.json

# 3. Migrar
./scripts/bulk_migrate_all.sh

# 4. Validar
python scripts/validate_migration.py --target extra-addons/V19 --report validation.json

# 5. Revisar reportes
cat migration_reports/MASTER_MIGRATION_REPORT.md
cat validation.json | jq '.'

# 6. Commit y Push
git add extra-addons/V19 migration_reports/ validation.json
git commit -m "feat: Migrate all modules to Odoo 19"
git push
```

## 🛠️ Comandos Avanzados

### Migrar solo un módulo
```bash
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --target extra-addons/V19 \
    --module [nombre_modulo]
```

### Validar con modo strict
```bash
python scripts/validate_migration.py \
    --target extra-addons/V19 \
    --strict
# Falla si hay algún warning o issue
```

### Validar un módulo específico
```bash
python scripts/validate_migration.py \
    --target extra-addons/V19 \
    --module [nombre_modulo]
```

### Solo analizar sin cambios
```bash
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --module [nombre_modulo] \
    --analyze-only
```

## 📊 Interpretar Reportes

### MASTER_MIGRATION_REPORT.md
```markdown
| Métrica | Valor |
|---------|-------|
| Módulos encontrados | 30 |
| Migraciones exitosas | 28 |
| Migraciones fallidas | 2 |
| Tasa de éxito | 93% |
| Total de fixes | 45 |
```

### validation_report.json
```json
{
  "modules": [
    {
      "module": "account_custom",
      "is_valid": true,
      "score": 100.0,
      "validation_results": {
        "manifest": { "passed": 5, "failed": 0 },
        "python": { "passed": 3, "failed": 0 },
        "xml": { "passed": 1, "failed": 0 },
        "structure": { "passed": 2, "failed": 0 }
      },
      "issues": [],
      "warnings": []
    }
  ],
  "summary": {
    "valid_modules": 28,
    "invalid_modules": 2,
    "average_score": 96.5
  }
}
```

## 🚨 Troubleshooting

### Error: "Módulo no encontrado"
```bash
# Verificar que los módulos existen
ls extra-addons/V17/
ls extra-addons/V17/[nombre]/__manifest__.py

# Verificar sintaxis de manifest
python -m py_compile extra-addons/V17/[nombre]/__manifest__.py
```

### Error: "Script no ejecutable"
```bash
chmod +x scripts/bulk_migrate_all.sh
chmod +x scripts/validate_migration.py
```

### Error: "@api.multi aún presente"
```bash
# Ver dónde está
grep -r "@api.multi" extra-addons/V19/[modulo]/

# La herramienta debería haberlo removido
# Si no, revisar manualmente
```

### Módulo falla en validación
```bash
# Ver detalles
python scripts/validate_migration.py \
    --target extra-addons/V19 \
    --module [problema] \
    --report detailed.json

cat detailed.json | jq '.modules[0]'
```

## 📋 Flujo Recomendado

```
1. PREPARACIÓN (1 hora)
   ├─ Copiar módulos V17
   └─ Generar baseline report

2. MIGRACIÓN (30 minutos - 2 horas)
   ├─ Ejecutar bulk migration
   ├─ Revisar MASTER_MIGRATION_REPORT.md
   └─ Investigar módulos fallidos

3. VALIDACIÓN (30 minutos)
   ├─ Ejecutar validación
   ├─ Revisar validation_report.json
   └─ Revisar warnings

4. AJUSTES MANUALES (1-3 horas, si aplica)
   ├─ Corregir módulos fallidos
   ├─ Re-validar
   └─ Repetir hasta score 100%

5. TESTING (1-2 horas)
   ├─ Instalar en Odoo 19 test
   ├─ Verificar sin errores
   └─ Probar flujos principales

6. FINALIZACIÓN (30 minutos)
   ├─ Commit
   ├─ Push
   └─ Crear PR
```

## 📞 Soporte

### Ver logs detallados
```bash
tail -f odoo_migration.log
```

### Ver todos los reportes generados
```bash
ls -la migration_reports/
```

### Verificar integridad
```bash
# Contar módulos migrados
ls extra-addons/V19/ | wc -l

# Contar módulos originales
ls extra-addons/V17/ | wc -l

# Deben ser iguales
```

## ✅ Checklist Final

- [ ] Todos los módulos V17 copiados
- [ ] Herramienta ejecutable: `./scripts/bulk_migrate_all.sh`
- [ ] Validación ejecutable: `python scripts/validate_migration.py`
- [ ] Migración completada sin errores
- [ ] Validación con score > 90%
- [ ] Reportes revisados
- [ ] Módulos fallidos investigados
- [ ] Testing en Odoo 19 completado
- [ ] Commit y push realizados

---

**Versión**: 1.0
**Última actualización**: 2026-02-16
**Tiempo estimado**: 4-6 horas para 30-40 módulos
