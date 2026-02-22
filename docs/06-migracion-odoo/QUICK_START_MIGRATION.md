# Quick Start: Odoo 17→19 Migration

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


## En 5 Minutos

```bash
# 1. Generar reporte de compatibilidad (5 min)
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --report \
    --output baseline.json

# 2. Ver cuales módulos tienen issues
cat baseline.json | jq '.modules[] | select(.issues_found > 0) | {name, issues: .issues_found}'

# 3. Migrar un módulo
python scripts/odoo_migration_tool.py \
    --source extra-addons/V17 \
    --target extra-addons/V19 \
    --module account_custom

# ✅ Done! Revisar migration_report.json
cat migration_report.json | jq '.summary'
```

---

## Flujo Típico (1-2 horas por módulo)

```
1. Migración automática
   └─ python scripts/odoo_migration_tool.py --module X
      ├─ Copia módulo V17 → V19
      ├─ Analiza compatibility
      └─ Auto-fix problemas comunes
      
2. Validar en Odoo 19 test
   └─ Instalar módulo
      ├─ Verificar sin errores
      ├─ Abrir menús/vistas
      └─ Probar flujo principal

3. Revisar cambios
   └─ git diff extra-addons/V19/X/
      └─ Code review

4. Documentar
   └─ Actualizar extra-addons/ODOO_MIGRATION_TRACKER.md
      └─ Estado: "Listo"
```

---

## Comandos Útiles

```bash
# Migrar un módulo
python scripts/odoo_migration_tool.py --source extra-addons/V17 --target extra-addons/V19 --module [nombre]

# Migrar todos
python scripts/odoo_migration_tool.py --source extra-addons/V17 --target extra-addons/V19 --all

# Solo analizar (sin cambios)
python scripts/odoo_migration_tool.py --source extra-addons/V17 --module [nombre] --analyze-only

# Generar reporte
python scripts/odoo_migration_tool.py --source extra-addons/V17 --report --output compat.json

# Ver issues encontrados
cat migration_report.json | jq '.modules[0].steps[] | select(.name=="analysis") | .data'

# Ver fixes aplicados
cat migration_report.json | jq '.modules[0].steps[] | select(.name=="fix") | .data.fixes'

# Logs
tail -f odoo_migration.log

# Ver diferencias
git diff extra-addons/V19/[modulo]/
```

---

## Checklist por Módulo

- [ ] `python scripts/... --module X` (5 min)
- [ ] Revisar migration_report.json (2 min)
- [ ] Copiar a servidor test Odoo 19
- [ ] Instalar módulo (2 min)
- [ ] Verificar sin errores en logs (2 min)
- [ ] Abrir menús y vistas (3 min)
- [ ] Probar flujo principal (5 min)
- [ ] git review de cambios (3 min)
- [ ] Actualizar TRACKER (1 min)
- [ ] ✅ Done! (Total: ~30 min)

---

## Estructura Actual

```
extra-addons/
├── V17/              ← Módulos originales (v17)
│   ├── 3cxcrm/
│   ├── account_custom/
│   ├── [+20 módulos]
│   └── ...
├── V19/              ← Módulos migrados (v19)
│   ├── [vacío, esperar migración]
│   └── ...
├── ODOO_MIGRATION_TRACKER.md    ← Tracking live
├── MODULE_MIGRATION_TEMPLATE.md ← Template
└── Migration.md                 ← Guía operativa
```

---

## Estado Inicial

```bash
# Ver módulos en V17
ls extra-addons/V17/ | wc -l
# Resultado: ~25-40 módulos

# Ver si V19 está vacío
ls extra-addons/V19/
# Resultado: vacío (por llenar)

# Ver reporte baseline
cat baseline_compatibility.json | jq '.modules | length'
# Resultado: Total de módulos analizados
```

---

## Próximo: Plan Detallado

Para entender:
- Estrategia general → Leer: `docs/ODOO_MIGRATION_V17_TO_V19.md`
- Cómo funciona la herramienta → Leer: `ODOO_MIGRATION_TOOL_README.md`
- Tracking de módulos → Actualizar: `extra-addons/ODOO_MIGRATION_TRACKER.md`

---

## Soporte

```bash
# Ver ayuda de la herramienta
python scripts/odoo_migration_tool.py --help

# Ver logs detallados
tail -100 odoo_migration.log

# Ver reporte completo
cat migration_report.json | jq '.'

# Contactar: DevOps team
```

---

**¡Listo para comenzar!**

Próximo paso: Generar baseline compatibility report (5 min)
