# 📦 PAQUETE DE ENTREGA – Flujo de Onboarding Partner-Led (Phase 3)
## Sajet.us / PCT 160 | Febrero 14, 2026

---

## ✅ Qué se Entrega en Este Paquete

### 📋 Documentación (5 archivos principales)

```
docs/
├─ RESUMEN_EJECUTIVO_PHASE_3.md
│  └─ Visión, decisiones, impacto, timeline
│
├─ ONBOARDING_PUBLICO_SIN_PRECIOS.md
│  └─ Flujo usuario, API (7 endpoints), BD, gating, seguridad
│
├─ ROLES_PERMISOS_MATRIZ.md
│  └─ ACL 3 roles (admin/tenant/partner), JWT, ejemplos, transiciones
│
├─ PR_TEMPLATE_ONBOARDING_PARTNER.md
│  └─ Checklist 40+ items, archivos, tests, rollback
│
├─ VALIDACION_NO_REGRESION.md
│  └─ Test matrix, no rompe /signup→/checkout→/webhook
│
└─ [Este archivo] DELIVERY_PCT160.md
   └─ Guía de lectura, validación, integración
```

### 🗂️ Cambios en Repo

```
README.md
  └─ Actualizado con Phase 3 (partner-led, gating, comisiones)

.github/copilot-instructions.md
  └─ (Sin cambios requeridos, pero referencia Phase 3)
```

---

## 📖 Guía de Lectura (Por Rol)

### 👨‍💼 Si eres PRODUCTO/STAKEHOLDER
**Lectura recomendada (5 minutos)**:
1. [RESUMEN_EJECUTIVO_PHASE_3.md](RESUMEN_EJECUTIVO_PHASE_3.md) – Visión, impacto, timeline
2. Preguntas → equipo técnico

### 👨‍💻 Si eres ENGINEER (Backend/Frontend)
**Lectura recomendada (30 minutos)**:
1. [RESUMEN_EJECUTIVO_PHASE_3.md](RESUMEN_EJECUTIVO_PHASE_3.md) – Contexto (5 min)
2. [ONBOARDING_PUBLICO_SIN_PRECIOS.md](ONBOARDING_PUBLICO_SIN_PRECIOS.md) – Flujo, API, BD (15 min)
3. [ROLES_PERMISOS_MATRIZ.md](ROLES_PERMISOS_MATRIZ.md) – ACL, JWT (10 min)
4. [PR_TEMPLATE_ONBOARDING_PARTNER.md](PR_TEMPLATE_ONBOARDING_PARTNER.md) – Checklist (5 min)

### 🔍 Si eres QA/TESTING
**Lectura recomendada (20 minutos)**:
1. [VALIDACION_NO_REGRESION.md](VALIDACION_NO_REGRESION.md) – Test matrix (10 min)
2. [PR_TEMPLATE_ONBOARDING_PARTNER.md](PR_TEMPLATE_ONBOARDING_PARTNER.md) – Tests & rollback (10 min)

### 🔒 Si eres SECURITY
**Lectura recomendada (15 minutos)**:
1. [ROLES_PERMISOS_MATRIZ.md](ROLES_PERMISOS_MATRIZ.md) – ACL, isolation (10 min)
2. [ONBOARDING_PUBLICO_SIN_PRECIOS.md](ONBOARDING_PUBLICO_SIN_PRECIOS.md) – Sección "4. Seguridad y Validaciones" (5 min)

---

## 🎯 Qué Habilita Este PR (Alineado con Acuerdo de Partnership)

| Feature | Status | Detalle |
|---------|--------|---------|
| **Lead Público Sin Precios** | 📋 Spec | Formulario `/onboarding/leads` multi-etapa |
| **Portal de Socios** | 📋 Spec | `/partners/leads` con CRUD leads, create-tenant, comisiones |
| **Nuevo Rol: Proveedor** | 📋 Spec | JWT + API Key, ACL aislado, 50/50 comisiones |
| **Cotizador Interno** | 📋 Spec | Tabla `quotations`, gating automático de Jeturing |
| **Factura a Partner** | 📋 Spec | Pre-creación tenant, genera invoice al proveedor |
| **Trazabilidad Lead→Tenant** | 📋 Spec | Pipeline con estados, logs, portal admin |
| **Seguridad ACL** | 📋 Spec | Isolation por partner, no ver otros partners |

---

## 🔄 Proceso de Integración (Para Devs)

### Paso 1: Review de Documentación (1 hora)
```
[ ] Leer RESUMEN_EJECUTIVO_PHASE_3.md (entender visión)
[ ] Leer ONBOARDING_PUBLICO_SIN_PRECIOS.md (endpoints, BD, flujo)
[ ] Leer ROLES_PERMISOS_MATRIZ.md (ACL, roles)
[ ] Preguntas → canal #product-onboarding en Slack
```

### Paso 2: Validar Arquitectura (30 min)
```
[ ] Revisar migraciones BD propuestas (no modifica heredadas)
[ ] Revisar nuevas rutas (no conflicto con /signup, /checkout, /webhook)
[ ] Revisar permisos (admin > tenant, partner > solo sus leads)
[ ] Validar que flujo actual (/signup→/checkout→/webhook) intacto
```

### Paso 3: Planificar Implementation (1-2 horas)
```
[ ] Asignar Backend: leads.py, partners.py, provisioning.py (mod)
[ ] Asignar Frontend: Svelte onboarding, partner dashboard
[ ] Asignar Tests: test_leads_api, test_partners_api, test_no_regression
[ ] Asignar DB: migraciones Alembic
[ ] Timeline: 6-7 semanas (MVP → GA)
```

### Paso 4: Implementar Fase 1 (Backend MVP, 2 semanas)
```
[ ] Tablas BD (leads, partners, quotations)
[ ] Endpoints: POST /api/leads/public, PUT /api/admin/leads/{id}/qualify
[ ] Endpoints: POST /api/partners/leads/{id}/create-tenant
[ ] JWT con rol "partner"
[ ] ACL en queries
[ ] Tests unitarios (pytest)
```

### Paso 5: Implementar Fase 2 (Frontend, 2 semanas)
```
[ ] Formulario /onboarding/leads (Svelte)
[ ] Status page /onboarding/status/{id}
[ ] Admin dashboard /admin/leads
[ ] Partner dashboard /partners/leads
[ ] Tests E2E (playwright/cypress)
```

### Paso 6: Testing & Regression (1 semana)
```
[ ] Validación no-regresión (/signup→/checkout)
[ ] Test E2E (checkout + partner flow en paralelo)
[ ] Stress test (múltiples leads/tenants simultáneos)
[ ] Rollback plan validado
```

### Paso 7: Pilot & GA (1-2 semanas)
```
[ ] Partner pilot (1 real lead → tenant)
[ ] Monitoring en producción
[ ] Bug fixes / iteraciones
[ ] GA (general availability)
```

---

## ✔️ Validaciones Previas a Aceptación

### ✅ Checklist del Equipo Técnico

```
ARQUITECTURA & DISEÑO
[ ] Migración BD no modifica tablas existentes
[ ] Nuevas rutas no conflictúan con heredadas
[ ] ACL documenta aislamiento de datos
[ ] Flujo actual (/signup→/checkout→/webhook) sigue igual

API & SEGURIDAD
[ ] 7 endpoints principales diseñados y documentados
[ ] Validación Pydantic en todas las rutas nuevas
[ ] JWT claims incluyen partner_id (sin romper admin/tenant)
[ ] Rate limiting documentado (5 leads/hora por IP)
[ ] Logs NO exponen secretos (teléfono, tokens, Stripe keys)

TESTING
[ ] Test matriz completa en VALIDACION_NO_REGRESION.md
[ ] Criterios de aceptación definidos (✅ PASS / ❌ FAIL)
[ ] Scripts de test proporcionados (bash + pytest)
[ ] Rollback plan validado

COMPLIANCE
[ ] Alineado con acuerdo de partnership (comisiones 50/50)
[ ] Trazabilidad de leads 100% (para auditoría)
[ ] Confidencialidad: partner NO ve otros partners
[ ] Documentación en español
```

### 📊 Criterios de Aceptación (Pre-Merge)

**DEBE pasar**:
1. Checkout actual (`/signup → /api/checkout → /webhook/stripe`) funciona sin cambios.
2. Todos los tests en `test_no_regression.py` pasan.
3. Provisioning crea tenants idénticamente desde ambos flujos.
4. Partner NO puede ver leads de otro partner (ACL validado).
5. Tenant NO puede ver datos de otro tenant.

**NO debe haber**:
- Breaking changes en rutas públicas.
- Datos mock en BD.
- Secretos en logs.
- Ambigüedad en transiciones de estado.

---

## 🚀 Deployment (Paso a PCT 160)

### Pre-Deployment Checklist
```bash
# 1. Validar código
pytest tests/ -v --cov=app
black --check app/
isort --check-only app/

# 2. Validar BD
alembic upgrade head
alembic downgrade -1  # Validar rollback
alembic upgrade head  # Volver a producción

# 3. Validar tests E2E
bash scripts/test_checkout_flow.sh        # Flujo actual
bash scripts/test_partner_flow.sh          # Flujo nuevo
bash scripts/test_parallel_flows.sh        # Stress

# 4. Seed de datos
bash scripts/seed_partners.sh

echo "✅ Listo para deploy a PCT 160"
```

### Deployment Steps
```bash
# En PCT 160
git pull origin main

# Backend
cd /opt/Erp_core
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
systemctl restart fastapi-app

# Frontend (si aplica)
cd frontend
npm install
npm run build
# (deploy estático o reiniciar servidor)

# Verificación
curl https://sajet.us/api/health    # 200 OK
curl https://sajet.us/onboarding/leads  # 200 OK (formulario HTML)
curl https://sajet.us/api/leads/public  # 405 Method Not Allowed (POST solo)
```

---

## 📞 Soporte & Contacto

| Pregunta | Contacto |
|----------|----------|
| ¿Cómo implementar? | Ver [PR_TEMPLATE_ONBOARDING_PARTNER.md](PR_TEMPLATE_ONBOARDING_PARTNER.md) |
| ¿Cómo probar? | Ver [VALIDACION_NO_REGRESION.md](VALIDACION_NO_REGRESION.md) |
| ¿Preguntas arquitectura? | Ver [ONBOARDING_PUBLICO_SIN_PRECIOS.md](ONBOARDING_PUBLICO_SIN_PRECIOS.md) → Sección "2. Flujo Operativo" |
| ¿Preguntas seguridad? | Ver [ROLES_PERMISOS_MATRIZ.md](ROLES_PERMISOS_MATRIZ.md) → Sección "4. Control de Acceso" |
| ¿En vivo? | Slack #product-onboarding o GitHub Discussions |

---

## 📚 Archivos Relacionados (Contexto Existente)

```
Heredado (intacto):
├─ .github/copilot-instructions.md          (guardrails, brand)
├─ docs/ADMIN_DASHBOARD.md                  (admin endpoints existentes)
├─ docs/IMPLEMENTATION_SUMMARY.md           (tenants CRUD existente)
├─ docs/INTEGRATION_SUMMARY.md              (onboarding Stripe Phase 2)
├─ docs/INDICE.md                           (índice de documentación)
└─ app/routes/onboarding.py                 (checkout Stripe)

Nueva (este entrega):
├─ docs/RESUMEN_EJECUTIVO_PHASE_3.md
├─ docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md
├─ docs/ROLES_PERMISOS_MATRIZ.md
├─ docs/PR_TEMPLATE_ONBOARDING_PARTNER.md
├─ docs/VALIDACION_NO_REGRESION.md
└─ README.md (actualizado con Phase 3)
```

---

## 🎯 Resumen Final

**Este paquete entrega**:
- ✅ Especificación completa de flujo partner-led (leads → tenants → comisiones).
- ✅ Diseño de BD (3 nuevas tablas, sin modificar heredadas).
- ✅ Contratos de API (7 endpoints con payloads y ejemplos).
- ✅ Matriz de roles y ACL (admin/tenant/partner con isolation).
- ✅ Checklist de implementación (40+ items, tests, rollback).
- ✅ Plan de validación (test matrix, criterios de aceptación).
- ✅ Garantía: flujo actual intacto, seguro, auditable.

**Timeline**: 6-7 semanas (MVP → GA).

**Próximo paso**: 
1. Review de documentación (equipo técnico).
2. Planificación de implementation (sprints).
3. Desarrollo Fase 1 (backend MVP).

---

**Versión**: 1.0  
**Fecha**: Febrero 14, 2026  
**Preparado para**: PCT 160 / Sajet.us  
**Alineado con**: Acuerdo de Partnership v2.0 (Feb 2026)

