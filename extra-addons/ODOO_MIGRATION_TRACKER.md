# 📊 Odoo 17 → 19 Migration Tracker
## Extra-Addons Module Migration

**Última actualización**: 2026-02-16
**Responsable**: DevOps/Backend Team
**Estado General**: 🔴 No iniciado

---

## 📋 Estructura del Proyecto

```
extra-addons/
├── V17/                          # Módulos fuente (Odoo 17)
│   ├── contabilidad/
│   ├── rrhh/
│   ├── ventas/
│   ├── integraciones/
│   ├── utilidades/
│   └── verticales/
├── V19/                          # Módulos migrados (Odoo 19)
│   ├── contabilidad/
│   ├── rrhh/
│   ├── ventas/
│   ├── integraciones/
│   ├── utilidades/
│   └── verticales/
├── MIGRATION_CHECKLIST.md        # Checklist por módulo
├── COMPATIBILITY_MATRIX.md       # Matrix de compatibilidad
└── ODOO_MIGRATION_TRACKER.md     # Este archivo
```

---

## 🎯 Plan de Migración por Fases

### Fase 1️⃣: Inventario y Análisis (Semana 1)

**Objetivo**: Identificar todos los módulos y sus dependencias

**Tareas**:
- [ ] Listar todos los módulos en V17
- [ ] Analizar `__manifest__.py` de cada módulo
- [ ] Identificar dependencias internas y externas
- [ ] Crear matriz de compatibilidad Odoo 19
- [ ] Clasificar módulos por prioridad
- [ ] Documentar estado actual en producción

**Entregables**:
- Lista completa de módulos
- Matriz de dependencias
- Clasificación de riesgo por módulo
- Backlog priorizado

### Fase 2️⃣: Migración Núcleo (Semanas 2-4)

**Objetivo**: Migrar módulos críticos de negocio

**Módulos de Alta Prioridad**:
1. Contabilidad y Facturación
2. RRHH y Nómina
3. Ventas / CRM
4. Utilidades Técnicas

**Por módulo**:
- [ ] Copiar estructura desde V17 a V19
- [ ] Actualizar `__manifest__.py`
- [ ] Revisar dependencias
- [ ] Corregir Python/ORM
- [ ] Corregir XML/vistas
- [ ] Validar seguridad
- [ ] Testing básico
- [ ] Documentar cambios

### Fase 3️⃣: Migración Funcional (Semanas 5-6)

**Objetivo**: Migrar módulos complementarios

**Módulos de Media Prioridad**:
1. POS y Restaurante
2. Website / Portal
3. Integraciones (WhatsApp, Stripe, API)
4. Reportes y Dashboards

### Fase 4️⃣: Estabilización (Semana 7-8)

**Objetivo**: QA, hardening y release

**Actividades**:
- [ ] QA funcional completa
- [ ] Testing de integración
- [ ] Hardening de seguridad
- [ ] Optimización de rendimiento
- [ ] Documentación final
- [ ] Capacitación de equipo

---

## 📊 Matriz de Módulos - Estado Actual

### Grupo: Contabilidad y Facturación

| Módulo | V17 | Prioridad | Estado | Owner | Bloqueos | Notas |
|--------|-----|-----------|--------|-------|----------|-------|
| account | ✅ | ALTA | Pendiente | | | Core de Odoo - debe migrar |
| account_invoice | ✅ | ALTA | Pendiente | | | Part of core |
| account_payment | ✅ | ALTA | Pendiente | | | Core |
| l10n_do | ✅ | ALTA | Pendiente | | | Localización DO |
| account_custom_reports | ✅ | MEDIA | Pendiente | | | Custom reports |

**Status**: 🔴 No iniciado

---

### Grupo: RRHH y Nómina

| Módulo | V17 | Prioridad | Estado | Owner | Bloqueos | Notas |
|--------|-----|-----------|--------|-------|----------|-------|
| hr | ✅ | ALTA | Pendiente | | | Core HR |
| hr_payroll | ✅ | ALTA | Pendiente | | | Core payroll |
| hr_payroll_expense | ✅ | MEDIA | Pendiente | | | Gastos de nómina |
| hr_org_chart | ✅ | BAJA | Pendiente | | | Organigrama |

**Status**: 🔴 No iniciado

---

### Grupo: Ventas / CRM

| Módulo | V17 | Prioridad | Estado | Owner | Bloqueos | Notas |
|--------|-----|-----------|--------|-------|----------|-------|
| sale | ✅ | ALTA | Pendiente | | | Core sales |
| crm | ✅ | ALTA | Pendiente | | | Core CRM |
| sale_management | ✅ | ALTA | Pendiente | | | Sales management |
| stock | ✅ | ALTA | Pendiente | | | Inventory |

**Status**: 🔴 No iniciado

---

### Grupo: POS y Restaurante

| Módulo | V17 | Prioridad | Estado | Owner | Bloqueos | Notas |
|--------|-----|-----------|--------|-------|----------|-------|
| pos | ✅ | MEDIA | Pendiente | | | Point of Sale |
| pos_cache | ✅ | MEDIA | Pendiente | | | POS optimization |
| pos_restaurant | ✅ | MEDIA | Pendiente | | | Restaurant module |

**Status**: 🔴 No iniciado

---

### Grupo: Website / Portal

| Módulo | V17 | Prioridad | Estado | Owner | Bloqueos | Notas |
|--------|-----|-----------|--------|-------|----------|-------|
| website | ✅ | MEDIA | Pendiente | | | Core website |
| website_form | ✅ | MEDIA | Pendiente | | | Website forms |
| portal | ✅ | MEDIA | Pendiente | | | Customer portal |
| custom_theme | ✅ | MEDIA | Pendiente | | | Custom theme |

**Status**: 🔴 No iniciado

---

### Grupo: Integraciones

| Módulo | V17 | Prioridad | Estado | Owner | Bloqueos | Notas |
|--------|-----|-----------|--------|-------|----------|-------|
| integration_stripe | ✅ | ALTA | Pendiente | | | Stripe payments |
| integration_whatsapp | ✅ | ALTA | Pendiente | | | WhatsApp integration |
| integration_api_rest | ✅ | ALTA | Pendiente | | | REST API |
| integration_sync | ✅ | MEDIA | Pendiente | | | Data sync |

**Status**: 🔴 No iniciado

---

### Grupo: Utilidades Técnicas

| Módulo | V17 | Prioridad | Estado | Owner | Bloqueos | Notas |
|--------|-----|-----------|--------|-------|----------|-------|
| queue | ✅ | ALTA | Pendiente | | | Job queue |
| web_helpers | ✅ | ALTA | Pendiente | | | Web utilities |
| api_authentication | ✅ | ALTA | Pendiente | | | API auth |
| monitoring | ✅ | MEDIA | Pendiente | | | System monitoring |

**Status**: 🔴 No iniciado

---

### Grupo: Verticales

| Módulo | V17 | Prioridad | Estado | Owner | Bloqueos | Notas |
|--------|-----|-----------|--------|-------|----------|-------|
| vertical_hotel | ✅ | BAJA | Pendiente | | | Hotel management |
| vertical_gym | ✅ | BAJA | Pendiente | | | Gym management |
| vertical_health | ✅ | BAJA | Pendiente | | | Health clinic |
| vertical_education | ✅ | BAJA | Pendiente | | | Education |

**Status**: 🔴 No iniciado

---

## 🔄 Estados de Migración

### Estados Permitidos
```
🔴 Pendiente      → No iniciado
🟡 En Análisis    → Analizando compatibilidad
🟠 En Migración   → Migrando código
🔵 En Pruebas     → Testing
🟢 Listo          → Completado y validado
⚫ Bloqueado      → Dependencias pendientes
```

---

## ✅ Checklist por Módulo

### Template: Checklist Técnico

```markdown
## Módulo: [nombre]

### Análisis
- [ ] Analizar `__manifest__.py`
- [ ] Identificar dependencias
- [ ] Revisar modelos Python
- [ ] Revisar vistas XML
- [ ] Revisar seguridad (ACLs)
- [ ] Revisar assets (JS/CSS)

### Migración
- [ ] Copiar a V19
- [ ] Actualizar `__manifest__.py`
- [ ] Actualizaciones de dependencies
- [ ] Corregir imports de Python
- [ ] Actualizar decoradores ORM si aplica
- [ ] Corregir XML/QWeb
- [ ] Actualizar assets web
- [ ] Revisar reglas de seguridad

### Testing
- [ ] Instalación sin errores
- [ ] Menús principales cargan
- [ ] Vistas principales abren
- [ ] Acceso de usuarios OK
- [ ] Flujo principal funciona
- [ ] No hay errores en logs
- [ ] Performance aceptable

### Validación
- [ ] Documentar cambios realizados
- [ ] Identificar breaking changes
- [ ] Crear datos de migración si aplica
- [ ] Documentar pasos post-instalación
```

---

## 🔗 Matriz de Dependencias

### Dependencias Críticas

```
contabilidad/
├── account (CORE)
│   ├── account_invoice
│   ├── account_payment
│   └── l10n_do
├── l10n_do (Localización)
└── custom_reports

ventas/
├── sale (CORE)
│   ├── sale_management
│   └── stock
├── crm (CORE)
└── stock (Inventory)

rrhh/
├── hr (CORE)
│   ├── hr_payroll
│   └── hr_org_chart
└── hr_payroll

integraciones/
├── integration_api_rest (Requerido por varias)
├── integration_stripe
│   └── account
└── integration_whatsapp

utilidades/
├── queue (Requerido por muchas)
├── web_helpers
├── api_authentication
└── monitoring
```

### Orden Recomendado de Migración

```
1. CORE (Sin dependencias):
   - queue
   - web_helpers
   - api_authentication
   - l10n_do

2. NÚCLEO (Depende de CORE):
   - account
   - sale
   - crm
   - hr
   - stock

3. FUNCIONAL (Depende de NÚCLEO):
   - account_invoice
   - account_payment
   - sale_management
   - hr_payroll
   - pos

4. COMPLEMENTARIO (Depende de FUNCIONAL):
   - Integraciones
   - Reportes
   - Verticales
```

---

## 🚨 Riesgos y Mitigaciones

### Riesgo Alto 🔴

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|-------------|-----------|
| Incompatibilidad de dependencias Odoo | CRÍTICO | ALTA | Usar matrix de compat., testing temprano |
| Breaking changes en ORM | CRÍTICO | MEDIA | Revisar docs v18/v19, refactoring |
| Pérdida de datos en migración | CRÍTICO | BAJA | Backups, validación pre/post |
| Downtime de operación | CRÍTICO | MEDIA | Estrategia gradual, ambientes paralelos |

### Riesgo Medio 🟡

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|-------------|-----------|
| Módulos custom no actualizados | ALTO | MEDIA | Audit de código, documentación |
| Performance degradado | ALTO | MEDIA | Profiling, optimización |
| Problemas de seguridad | ALTO | BAJA | Code review, security scan |
| Integraciones externas rotas | MEDIO | MEDIA | Testing con providers, updates |

---

## 📞 Escalación y Contactos

### Roles y Responsabilidades

| Rol | Responsable | Teléfono | Email |
|-----|-------------|----------|-------|
| Líder Técnico | [Nombre] | | |
| DevOps | [Nombre] | | |
| Backend Engineer | [Nombre] | | |
| QA Lead | [Nombre] | | |
| Product Manager | [Nombre] | | |

### Escalation Path

1. **Nivel 1** (Tech Lead): Bloqueos técnicos menores
2. **Nivel 2** (Director): Decisiones arquitectónicas
3. **Nivel 3** (C-Level): Riesgos críticos, timeline

---

## 📈 Métricas de Progreso

### KPIs de Migración

```
Módulos Migrados: 0/[TOTAL]
Cobertura de Testing: 0%
Bugs Críticos Abiertos: 0
Tiempo vs Plan: On Track

Velocidad: 0 módulos/semana
Burndown: [Gráfico]
Riesgo Actual: 🔴 ROJO (No iniciado)
```

### Reporte Semanal

```markdown
Semana X (Fechas):
- Módulos completados: 0
- Módulos en progreso: 0
- Bloqueadores: Ninguno
- Riesgo: ROJO/AMARILLO/VERDE
- Siguiente hito: [Descripción]
```

---

## 🔄 Proceso de Cambios

### Workflow por Módulo

```
1. Crear Issue/Task
   └─ Título: "Migrate [módulo] to Odoo 19"

2. Análisis (1-2 días)
   ├─ Revisar `__manifest__.py`
   ├─ Documentar dependencias
   ├─ Identificar breaking changes
   └─ Actualizar estado a "En Análisis"

3. Migración (2-5 días según tamaño)
   ├─ Copiar código
   ├─ Actualizar manifests
   ├─ Corregir ORM/XML/Assets
   ├─ Commit con referencia a Issue
   └─ Actualizar estado a "En Migración"

4. Testing (2-3 días)
   ├─ Instalar en ambiente Odoo 19
   ├─ Ejecutar flujos principales
   ├─ Validar permisos
   ├─ Buscar errores en logs
   └─ Actualizar estado a "En Pruebas"

5. Validación (1 día)
   ├─ Code review
   ├─ Merge a rama dev/v19
   ├─ Crear PR con documentación
   └─ Actualizar estado a "Listo"

6. Cierre
   ├─ Documentar cambios realizados
   ├─ Actualizar MIGRATION_TRACKER.md
   ├─ Crear release notes
   └─ Cerrar Issue
```

---

## 📚 Referencias y Recursos

### Documentación Oficial Odoo

- [Odoo 19 API Docs](https://www.odoo.com/documentation/19.0/)
- [Odoo 18 Release Notes](https://www.odoo.com/documentation/18.0/release_notes.html)
- [Odoo 17 → 18 Migration Guide](https://www.odoo.com/documentation/18.0/migration.html)

### Cambios Importantes v17→v19

**Python/ORM**:
- `api.multi` - removido en v18
- `api.one` - removido en v17+
- `api.model` - deprecado en v18
- Decorador `@api.model_create_multi` - nuevo en v18

**XML/Vistas**:
- Nuevos atributos en campos
- Cambios en qweb syntax
- Nuevos componentes web

**Assets**:
- Migration de SCSS
- Webpack changes
- JS module system changes

### Tools Útiles

```bash
# Comparar manifests
diff extra-addons/V17/modulo/__manifest__.py \
     extra-addons/V19/modulo/__manifest__.py

# Validar módulo
python -m py_compile extra-addons/V19/modulo/models.py

# Buscar patrones v17
grep -r "@api.multi" extra-addons/V17/

# Analizar dependencias
grep "depends" extra-addons/V17/*/_ manifest__.py
```

---

## 🎯 Próximos Pasos

1. **Inmediato** (Esta semana):
   - [ ] Confirmar estructura de módulos
   - [ ] Listar todos los módulos en V17
   - [ ] Crear documento de dependencias
   - [ ] Asignar owners técnicos

2. **Corto plazo** (Próximas 2 semanas):
   - [ ] Preparar ambiente Odoo 19
   - [ ] Iniciar migración de módulos CORE
   - [ ] Crear CI/CD para testing automático
   - [ ] Documentar cambios por módulo

3. **Mediano plazo** (Semanas 3-6):
   - [ ] Completar migración NÚCLEO
   - [ ] Iniciar migración FUNCIONAL
   - [ ] Validar integraciones externas
   - [ ] Testing de integración

4. **Largo plazo** (Semanas 7-8):
   - [ ] QA final completa
   - [ ] Hardening de seguridad
   - [ ] Optimización de rendimiento
   - [ ] Preparación para release

---

## 📝 Notas y Decisiones

### Decisiones Tomadas
- [ ] Estrategia: Gradual (v17 → v19)
- [ ] Ambientes: Paralelos o in-place?
- [ ] Módulos custom: Mantener o reescribir?
- [ ] Deprecados: Migrar o eliminar?

### Preguntas Abiertas
- [ ] ¿Cuáles son los módulos realmente activos en producción?
- [ ] ¿Hay módulos que pueden eliminarse?
- [ ] ¿Se requieren nuevos módulos en v19?
- [ ] ¿Timeline es flexible?

---

**Documento creado**: 2026-02-16
**Próxima revisión**: Después de Semana 1 (Inventario)
**Owner**: DevOps Team
