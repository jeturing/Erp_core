# Skills OCA - Automatización de Migración Odoo V17→V19

**Fecha**: 17 de febrero de 2026  
**Status**: 📋 DOCUMENTACIÓN LISTA PARA IMPLEMENTACIÓN  
**Enfoque**: Automatizar migración incremental de 152+ módulos

---

## 📊 Contexto

Necesitamos migrar **152+ módulos** de Odoo 17 a Odoo 19:
- **Ubicación actual**: `/extra-addons/V17/`
- **Destino**: `/extra-addons/V19/`
- **Estrategia**: Etapas (Inventario → Core → Funcional → Estabilización)

### Herramientas Disponibles

| Herramienta | Propósito | Maintainer |
|-------------|----------|-----------|
| **odoo-upgrade** | Script base migración automática | Ahmed Lakos |
| **odoo-19** | Actualizaciones OCA v19 | unclecatvn |
| **odoo-oca-developer** | Herramientas OCA estándar | MiquelAlzanillas |

---

## 🚀 Instalación

### 1. Instalar Node.js (si no existe)
```bash
# macOS
brew install node npm

# Linux
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs npm
```

### 2. Instalar Skills OCA (npm global)
```bash
# Instalar packages del repo OCA
npm install -g odoo-upgrade odoo-19 odoo-oca-developer

# Verificar instalación
npm list -g | grep odoo
```

**Output esperado**:
```
└── odoo-upgrade@latest
└── odoo-19@latest
└── odoo-oca-developer@latest
```

### 3. Configurar directorio de trabajo
```bash
cd /opt/Erp_core/extra-addons

# Crear estructura
mkdir -p V19/{
  contabilidad,
  rrhh,
  ventas,
  pos,
  website,
  integraciones,
  verticales,
  no_migrado
}

# Copiar V17 como referencia
cp -r V17 V17_backup
```

---

## 📋 Matriz de Módulos (Plantilla)

Ver `/extra-addons/Migration.md` para lista completa.

### Estados Permitidos
- **Pendiente** - No iniciada migración
- **En análisis** - Revisando compatibilidad V17→V19
- **En migración** - Actualmente siendo migrado
- **En pruebas** - Migrado, requiere QA
- **Listo** - Aprobado para producción
- **Bloqueado** - Requiere refactor mayor

---

## 🔧 Workflow de Migración

### Etapa 1: Inventario de Módulos (AHORA)
```bash
# Escanear módulos V17
odoo-upgrade scan /extra-addons/V17 --output inventory.json

# Categorizar por severidad
odoo-upgrade categorize inventory.json --output categories.json
```

**Salida esperada**:
```json
{
  "high_priority": [
    {"name": "account", "dependencies": 5, "complexity": "high"},
    {"name": "sale", "dependencies": 3, "complexity": "medium"}
  ],
  "medium_priority": [...],
  "low_priority": [...]
}
```

### Etapa 2: Preparar Core (Semana 1)
```bash
# Para cada módulo de alta prioridad:
cd V17/nombre_modulo

# 1. Analizar cambios manifesto
odoo-upgrade analyze --manifest=__manifest__.py --from=17.0 --to=19.0

# 2. Generar upgrade script
odoo-upgrade generate-upgrade \
  --source=V17/nombre_modulo \
  --target=../V19/nombre_modulo \
  --auto-fix

# 3. Verificar cambios
odoo-upgrade validate ../V19/nombre_modulo
```

### Etapa 3: Ejecutar Migraciones
```bash
# Batch processing para múltiples módulos
for modulo in account sale stock purchase; do
  echo "Migrando $modulo..."
  odoo-upgrade migrate \
    --source=V17/$modulo \
    --target=V19/$modulo \
    --checklist
done
```

### Etapa 4: Validación QA
```bash
# Checklist automático por módulo
odoo-oca-developer validate V19/nombre_modulo --strict
```

**Valida**:
- ✅ Estructura de carpetas OCA
- ✅ `__manifest__.py` válido
- ✅ `__init__.py` completo
- ✅ Imports correctos
- ✅ XML bien formado
- ✅ ACLs en security/
- ✅ No hay deprecated imports

---

## 📝 Checklist por Módulo

Para cada módulo a migrar, usar esta lista:

```
Módulo: __name__
Versión origen: 17.0
Versión destino: 19.0
Fecha inicio: YYYY-MM-DD
Responsable: [nombre]

PRE-MIGRACIÓN
[ ] Backup de código V17
[ ] Documentar dependencias
[ ] Revisar cambios v17→v19 en OCA

MIGRACIÓN
[ ] Ejecutar odoo-upgrade
[ ] Resolver conflictos
[ ] Actualizar imports
[ ] Actualizar XML
[ ] Actualizar ACLs

POST-MIGRACIÓN
[ ] odoo-oca-developer validate (PASS)
[ ] Tests unitarios (si existen)
[ ] Tests manuales en staging
[ ] Security review
[ ] Docs actualizadas

SIGN-OFF
[ ] Code review aprobado
[ ] QA sign-off
[ ] Pronto para producción
```

---

## 🔍 Casos de Uso Comunes

### Caso 1: Módulo con cambios de API
```bash
# Detectar APIs deprecated
odoo-upgrade analyze-api V17/nombre_modulo/models/*.py

# Obtener sugerencias de migración
odoo-upgrade suggest-fixes \
  --deprecated-apis \
  --from=17.0 --to=19.0
```

### Caso 2: Módulo con JS legacy
```bash
# Convertir a Odoo 19 JS patterns
odoo-upgrade convert-js \
  --source=V17/nombre_modulo/static/src \
  --target=V19/nombre_modulo/static/src
```

### Caso 3: Módulo sin tests
```bash
# Generar stubs de tests
odoo-oca-developer generate-tests \
  --module=V19/nombre_modulo \
  --coverage=50%
```

---

## 📊 Monitoreo de Progreso

### Dashboard de Migración
```bash
# Ver status en tiempo real
odoo-upgrade progress \
  --source=V17 \
  --target=V19 \
  --output=dashboard.html
```

Genera HTML interactivo con:
- Total módulos: __/%
- Estado por etapa
- Bloqueados: __
- Listos: __

### Reporte JSON para CI/CD
```bash
odoo-upgrade report \
  --source=V17 \
  --target=V19 \
  --format=json \
  --output=migration-status.json
```

---

## 🚨 Troubleshooting

### Error: "Dependencia no encontrada en v19"
```bash
# Buscar reemplazo en OCA
odoo-upgrade find-replacement --deprecated=old_module

# Opción 1: Usar módulo OCA nuevo
# Opción 2: Mantener módulo pero marcar como legacy
```

### Error: "XML validation failed"
```bash
# Ver detalles del error
odoo-upgrade validate V19/modulo --verbose

# Auto-fijar errores comunes
odoo-upgrade fix-xml V19/modulo
```

### Error: "Import errors en módulos"
```bash
# Verificar imports disponibles
odoo-upgrade check-imports V19/modulo

# Sugerencias de reemplazo
odoo-upgrade suggest-imports --from=17.0 --to=19.0
```

---

## 📈 Métricas de Éxito

Medir progreso con:

```
Módulos migrados: X/152 (Y%)
  • Listos: X
  • En pruebas: X
  • En migración: X
  • Bloqueados: X

Tiempo promedio por módulo: X min
Tasa de éxito (sin bloqueos): Y%
Defectos encontrados (QA): Z
```

---

## 🔗 Integración con Git

### Rama por módulo
```bash
git checkout -b feature/migrate-modulo-nombre

# Hacer cambios
git add extra-addons/V19/modulo_nombre/
git commit -m "feat: migrar módulo_nombre de v17→v19

- Actualizar __manifest__.py
- Migrar models/
- Actualizar vistas XML
- Revisar ACLs"

git push origin feature/migrate-modulo-nombre
```

### PR Template
```markdown
## Migración: [nombre_modulo]

**De**: Odoo 17 → **A**: Odoo 19

### Cambios
- [ ] __manifest__.py actualizado
- [ ] models/ migrados
- [ ] XML revisado
- [ ] Security ACLs OK
- [ ] Tests pasados

### Checklist Validación
- [ ] odoo-upgrade validate: PASS
- [ ] odoo-oca-developer validate: PASS
- [ ] QA manual: PASS
- [ ] Docs actualizadas

### Bloqueadores / Issues
[Listar cualquier problema encontrado]
```

---

## 📚 Referencias OCA

- **Docs**: https://github.com/OCA/project-tools
- **Manifesto v19**: https://github.com/OCA/server-tools
- **API Changes**: https://github.com/odoo/odoo/releases/tag/19.0

---

## ✅ Timeline Estimado

| Etapa | Duración | Inicio | Status |
|-------|----------|--------|--------|
| 1. Inventario | 4 horas | Hoy | 📋 Pendiente |
| 2. Core migration | 3-5 días | Mañana | ⏳ Próxima |
| 3. Funcional | 5-7 días | Semana 1 | 📅 Planificado |
| 4. Estabilización | 2-3 días | Semana 2 | 📅 Planificado |
| 5. Production readiness | 1-2 días | Semana 2 | 📅 Planificado |

**Total**: 2-3 semanas para migración completa

---

## 🎯 Próximos Pasos

1. **HOY**: Ejecutar `odoo-upgrade scan` para inventario
2. **MAÑANA**: Iniciar migración de módulos core (account, sale, stock)
3. **SEMANA 1**: Completar Etapa 2 (Core)
4. **SEMANA 2**: Etapas 3-4 (Funcional + Estabilización)
5. **SEMANA 3**: QA y producción

---

## 📞 Soporte

Para issues con Skills OCA:
- GitHub: https://github.com/OCA/project-tools/issues
- Forum: https://github.com/orgs/OCA/discussions

Para issues en Sajet ERP:
- Contactar: [engineering@sajet.us]
- Docs: [enlace a guía interna]

---

**Documentación generada**: 2026-02-17  
**Versión**: 1.0  
**Autor**: Sajet ERP Engineering
