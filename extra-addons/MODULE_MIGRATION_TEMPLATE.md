# 📦 Template de Migración de Módulo
## Odoo 17 → 19

**Copiar este template para cada módulo que se migren**

---

## ℹ️ Información Básica

**Nombre del Módulo**: `[module_name]`
**Versión Original**: `17.0.X.X.X`
**Versión Target**: `19.0.X.X.X`
**Owner Técnico**: `[Nombre]`
**Fecha Inicio**: `[YYYY-MM-DD]`
**Fecha Objetivo**: `[YYYY-MM-DD]`
**Prioridad**: 🔴 ALTA / 🟡 MEDIA / 🟢 BAJA

---

## 📋 Análisis Previo

### 1. Información del Módulo

```
Módulo: [nombre]
Path v17: extra-addons/V17/[grupo]/[modulo]/
Path v19: extra-addons/V19/[grupo]/[modulo]/
Tamaño: [pequeño/medio/grande]
Criticidad: [core/complementario/experimental]
```

### 2. Análisis de `__manifest__.py`

**Checklist**:
- [ ] Revisar que fields existentes son válidos en v19
- [ ] Listar nuevos fields que podrían ser requeridos
- [ ] Revisar `depends`
- [ ] Revisar `external_dependencies`
- [ ] Revisar `installable`
- [ ] Revisar `auto_install`
- [ ] Revisar `license`

**Cambios Observados**:
```python
# v17 manifest
{
    'name': 'Module Name',
    'version': '17.0.1.0.0',
    'category': 'Category',
    'depends': ['base', 'sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/view_name.xml',
    ],
    'external_dependencies': {
        'python': ['requests', 'pandas'],
        'bin': []
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

# v19 cambios necesarios
Cambio 1: [Descripción]
Cambio 2: [Descripción]
```

### 3. Análisis de Dependencias

**Dependencias Internas**:
| Módulo | Estado | Riesgo |
|--------|--------|--------|
| [dep1] | Migrado/No migrado | Alto/Medio/Bajo |
| [dep2] | Migrado/No migrado | Alto/Medio/Bajo |

**Dependencias Externas**:
| Paquete | Versión v17 | Versión v19 | Compatible |
|---------|-------------|------------|-----------|
| requests | 2.x | 2.x+ | ✅ |
| pandas | 1.x | 1.x+ | ✅ |

**Bloqueadores**: Ninguno / [Descripción]

### 4. Análisis de Código Python

**Archivos a revisar**:
```
extra-addons/V17/[grupo]/[modulo]/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── model_a.py
│   └── model_b.py
├── views/
│   ├── view_a.xml
│   └── view_b.xml
├── security/
│   └── ir.model.access.csv
└── static/
    ├── src/js/
    └── src/css/
```

**Decoradores Encontrados**:
```python
# Patrones encontrados en v17
@api.multi              # ❌ REMOVIDO en v18 - REFACTOR REQUERIDO
@api.one                # ❌ REMOVIDO en v17 - REFACTOR REQUERIDO
@api.model              # ⚠️ DEPRECADO en v18 - REVISAR
@api.constrains         # ✅ MANTENER
@api.onchange           # ✅ MANTENER
@api.depends            # ✅ MANTENER
```

**Cambios de ORM Necesarios**:
```python
# v17 → v19 transformaciones

# Antes (v17)
@api.multi
def action_confirm(self):
    for record in self:
        record.state = 'confirmed'

# Después (v19)
def action_confirm(self):
    for record in self:
        record.state = 'confirmed'

# Antes (v17)
@api.model
def create(self, vals):
    return super().create(vals)

# Después (v19) - Usar @api.model_create_multi si es multi
@api.model_create_multi
def create(self, vals_list):
    return super().create(vals_list)
```

**Imports a revisar**:
```python
# Estos imports pueden cambiar
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
# Revisar que existen en v19
```

### 5. Análisis de Vistas XML

**Patrones encontrados**:
- [ ] `<tree>` - Sin cambios esperados
- [ ] `<form>` - Revisar nuevos atributos
- [ ] `<search>` - Sin cambios esperados
- [ ] `<kanban>` - Revisar templates
- [ ] `<pivot>` - Sin cambios esperados
- [ ] `<graph>` - Sin cambios esperados
- [ ] `<calendar>` - Revisar atributos
- [ ] `<qweb>` - REVISAR (cambios en v18)

**Cambios en QWeb**:
```xml
<!-- v17 -->
<t t-as="item" t-foreach="items">
    <span t-field="item.name"/>
</t>

<!-- v19 - Probably compatible, pero revisar -->
<!-- Cambios esperados en template syntax -->
```

### 6. Análisis de Seguridad

**ACLs encontrados**:
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_module_user,module.user,model_module_model,base.group_user,1,1,1,0
access_module_manager,module.manager,model_module_model,base.group_system,1,1,1,1
```

**Reglas de Seguridad** (`ir.rule`):
- [ ] Revisar domínios
- [ ] Revisar modelos
- [ ] Verificar grupos

**Cambios Necesarios**:
- Ninguno / [Descripción]

### 7. Análisis de Assets (JS/CSS)

**Assets web encontrados**:
```
static/
├── src/
│   ├── js/
│   │   ├── module.js
│   │   └── helpers.js
│   └── css/
│       ├── module.scss
│       └── style.css
└── tests/
    └── [test files]
```

**Cambios necesarios en JS**:
```javascript
// v17
odoo.define('module.name', function(require) {
    var Widget = require('web.Widget');
    // code
});

// v19 - Puede haber cambios en module system
// Revisar si es necesario ES6 modules
```

**Cambios necesarios en CSS/SCSS**:
```scss
// v17
.module-class {
    color: red;
}

// v19 - Probablemente compatible
```

---

## 🔧 Ejecución de Migración

### Fase 1: Preparación

```bash
# 1. Copiar módulo
cp -r extra-addons/V17/[grupo]/[modulo] \
      extra-addons/V19/[grupo]/[modulo]

# 2. Crear rama de trabajo
git checkout -b feature/migrate-[modulo]-v19

# 3. Verificar estructura
ls -la extra-addons/V19/[grupo]/[modulo]/
```

### Fase 2: Actualizar `__manifest__.py`

```python
{
    'name': 'Module Name',
    'version': '19.0.1.0.0',  # ← Cambiar versión
    'category': 'Category',
    'depends': [
        'base',  # Verificar que existen en v19
        'sale',  # Verificar que existen en v19
        'account'  # Verificar que existen en v19
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/view_name.xml',
    ],
    'external_dependencies': {
        'python': ['requests>=2.28.0', 'pandas>=1.3.0'],  # Actualizar versiones
        'bin': []
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    # Nuevos campos opcionales en v19
    'author': 'Company',
    'website': 'https://...',
    'support': 'support@...',
}
```

### Fase 3: Actualizar Python/ORM

**Buscar y reemplazar decoradores**:
```bash
# Encontrar @api.multi
grep -r "@api.multi" extra-addons/V19/[grupo]/[modulo]/

# Encontrar @api.one
grep -r "@api.one" extra-addons/V19/[grupo]/[modulo]/

# Encontrar @api.model (revisar caso a caso)
grep -r "@api.model" extra-addons/V19/[grupo]/[modulo]/
```

**Refactor por patrón**:

**Patrón 1: @api.multi con loop**
```python
# ❌ ANTES
@api.multi
def action_do_something(self):
    for record in self:
        record.name = 'Updated'

# ✅ DESPUÉS
def action_do_something(self):
    for record in self:
        record.name = 'Updated'
```

**Patrón 2: @api.multi que retorna algo**
```python
# ❌ ANTES
@api.multi
def get_data(self):
    results = []
    for record in self:
        results.append(record.compute_something())
    return results

# ✅ DESPUÉS
def get_data(self):
    results = []
    for record in self:
        results.append(record.compute_something())
    return results
```

**Patrón 3: @api.model para create/write**
```python
# ❌ ANTES
@api.model
def create(self, vals):
    # Single record creation
    return super(ClassName, self).create(vals)

# ✅ DESPUÉS (si se mantiene single)
def create(self, vals):
    return super().create(vals)

# ✅ MEJOR (multi-create)
@api.model_create_multi
def create(self, vals_list):
    return super().create(vals_list)
```

### Fase 4: Actualizar XML/Vistas

**Checklist por tipo de vista**:

**Form views**:
- [ ] Revisar atributos `widget`
- [ ] Revisar atributos `mode`
- [ ] Revisar `invisible/readonly` domains
- [ ] Revisar `<field>`
- [ ] Revisar `<label>`
- [ ] Revisar `<button>`

**Tree views**:
- [ ] Revisar columnas
- [ ] Revisar sorting
- [ ] Revisar colores

**Search views**:
- [ ] Revisar filtros
- [ ] Revisar groupby
- [ ] Revisar campos searchable

**Cambios típicos**:
```xml
<!-- v17 -->
<field name="name" widget="char"/>

<!-- v19 - Probablemente compatible -->
<!-- Solo revisar si falla instalación -->
```

### Fase 5: Actualizar Assets

**Revisión de JS**:
```javascript
// Buscar patrones deprecated
odoo.define  // Aún válido en v19
_.each()     // Usar Array.forEach() o for...of
$.ajax()     // Usar fetch() o http service

// Actualizar imports si es necesario
import { Component } from '@odoo/owl';  // v19
```

**Revisión de CSS/SCSS**:
```scss
// Revisar que variables de bootstrap existan
// Revisar que mixins existan
// Generalmente compatible
```

### Fase 6: Validar Seguridad

**Checklist de ACLs**:
```
- [ ] Todos los modelos tienen ACLs
- [ ] Todos los grupos tienen permisos apropiados
- [ ] No hay conflictos de reglas
- [ ] Roles están definidos en depends
```

---

## ✅ Testing

### Test 1: Instalación

```bash
# En servidor Odoo 19 de test
odoo-bin -d test_db --init=[modulo_name] -i [modulo_name]

# Verificar en logs:
# - No hay errores de import
# - No hay errores de SQL
# - El módulo aparece como instalado
```

### Test 2: Carga de Vistas

```python
# En Odoo shell
env['ir.ui.view'].search([('module', '=', '[modulo_name]')])
# Debería retornar todas las vistas sin errores

# Abrir cada vista en navegador:
# https://localhost:8069/web#id=[view_id]&model=[model_name]
```

### Test 3: Menús

```python
# En Odoo shell
env['ir.ui.menu'].search([('module', '=', '[modulo_name]')])
# Debería retornar los menús
# Verificar que aparecen en UI
```

### Test 4: Acceso de Usuarios

```python
# Crear usuario con grupo específico
user = env['res.users'].create({
    'name': 'Test User',
    'login': 'test_user',
    'groups_id': [(6, 0, [group_id])]
})

# Verificar permisos
# Crear record como usuario
# Editar record
# Eliminar record (si permitido)
```

### Test 5: Flujo Principal

**Checklist específico por módulo**:
```
Módulo: [name]
Flujo Principal:
1. [ ] Crear objeto
2. [ ] Editar objeto
3. [ ] Cambiar estado
4. [ ] Ejecutar acción principal
5. [ ] Eliminar objeto (si aplica)
```

### Test 6: Validaciones

```python
# Probar validaciones
# Probar constrains
# Probar onchanges

# Debe retornar errores apropiados
```

### Test 7: Logs

```bash
# Revisar logs sin errores
tail -f /var/log/odoo/odoo-bin.log | grep ERROR

# Debería estar limpio
```

---

## 📝 Documentación de Cambios

### Cambios Realizados

**Resumen**:
```
Total de cambios: [N]
Archivos modificados: [N]
Líneas de código: +[N] -[N]
```

**Detalle por archivo**:

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `__manifest__.py` | Actualizar versión | 1 |
| `models/model_a.py` | Remover @api.multi | 3 |
| `views/view_a.xml` | Sin cambios | 0 |
| `static/src/js/module.js` | Actualizar imports | 2 |

### Breaking Changes

```
Breaking Change 1:
- Afecta: [modelos/vistas/datos]
- Mitigación: [cómo manejar]
- Migration Script: [sí/no]

Breaking Change 2:
- ...
```

### Data Migration Scripts

Si se requieren scripts de migración de datos:

```python
# post_migration/[modulo]_data_migration.py

def migrate_data(cr, registry):
    """Migra datos de v17 a v19"""

    env = api.Environment(cr, SUPERUSER_ID, {})

    # Buscar datos que necesitan actualización
    # records = env['model.name'].search([...])

    # Actualizar
    # for record in records:
    #     record.write({...})

    pass
```

---

## 🔍 Validación Pre-Merge

### Checklist Final

- [ ] Código compila sin errores
- [ ] Módulo instala en Odoo 19
- [ ] Menús aparecen correctamente
- [ ] Vistas cargan sin errores
- [ ] Acceso de usuarios funciona
- [ ] Flujo principal completado
- [ ] No hay errores en logs
- [ ] Documentación actualizada
- [ ] Code review completado
- [ ] Tests automáticos pasando (si aplica)

### Code Review

**Checklist para Reviewer**:
- [ ] ¿Todos los decoradores `@api.multi` removidos?
- [ ] ¿Todos los decoradores `@api.one` removidos?
- [ ] ¿Manifest actualizado correctamente?
- [ ] ¿Dependencias válidas en v19?
- [ ] ¿Cambios de XML son compatibles?
- [ ] ¿Assets web son válidos?
- [ ] ¿Seguridad revisada?
- [ ] ¿Performance aceptable?
- [ ] ¿Documentación clara?

---

## 📊 Resultados Finales

### Módulo Completado ✅

- **Estado**: Listo para Producción
- **Fecha de Cierre**: `[YYYY-MM-DD]`
- **Tiempo Total**: `[X horas/días]`
- **Issues Reportados**: `[N]`
- **Bugs Críticos**: `[N]`

### Lecciones Aprendidas

```
1. [Lección]
2. [Lección]
3. [Lección]
```

### Recomendaciones

```
1. [Recomendación]
2. [Recomendación]
```

---

## 📎 Archivos Adjuntos

- [ ] Screenshot de instalación exitosa
- [ ] Screenshot de vistas funcionales
- [ ] Log de testing
- [ ] Code review comments
- [ ] Diff detallado

---

**Documento de Migración Creado**: 2026-02-16
**Owner**: [Nombre]
**Última Actualización**: [Fecha]
