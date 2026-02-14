# PR Template – Flujo de Onboarding Público, Cotizador Interno y Rol Proveedor

## 🎯 Objetivo del PR

Este PR integra el **nuevo flujo de onboarding público sin precios** + **cotizador interno** + **nuevo rol de Proveedor de Servicio (Partner)** en Sajet.us, alineado con el acuerdo de partnership no exclusivo y operación partner-led.

**Documento de referencia**: [docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md](../docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md)  
**Matriz de roles**: [docs/ROLES_PERMISOS_MATRIZ.md](../docs/ROLES_PERMISOS_MATRIZ.md)  

---

## 📋 Descripción Detallada

### Qué se habilita

#### 1️⃣ Onboarding Público Sin Precios
- Formulario multi-etapa (`/onboarding/leads`) para clientes potenciales.
- Captura: datos básicos, operación, alcance, volúmenes, usuarios, requerimientos, integraciones, reportes.
- **Sin mostrar precios** (solo planes y módulos).
- Validación en tiempo real (email duplicate, teléfono formato, fechas futuras).
- Resultado: Lead "nuevo" en pipeline, listo para Partner o Jeturing.

#### 2️⃣ Portal de Socios (Proveedor de Servicio)
- Acceso restringido a leads asignados por Jeturing admin.
- Calificar leads, adjuntar documentos, crear tenants, ver comisiones.
- **No puede**: cambiar precios, prometer custom, ver otros partners.
- API Key + JWT para autenticación segura.

#### 3️⃣ Cotizador Interno
- Formulario de dimensionamiento (complejidad, migración, riesgos, requerimientos técnicos).
- Gating automático: detecta si requiere custom (Jeturing entra).
- Visible solo para Admin y Partner (no público).

#### 4️⃣ Nuevo Rol: Proveedor de Servicio
- Autenticación separada (JWT + API Key).
- Permisos granulares (ver leads propios, crear tenants, solicitar Work Orders).
- ACL en rutas y queries (isolation de datos).

#### 5️⃣ Flujo Partner-Led
- Lead calificado → Partner crea tenant → Factura emitida → Tenant activo.
- Jeturing solo entra si custom (Work Order).
- Comisiones 50/50 (Ingresos Netos) conforme acuerdo de partnership.

---

## 🏗️ Archivos Afectados / Creados

### Documentación (NUEVA)
```
docs/
  ├─ ONBOARDING_PUBLICO_SIN_PRECIOS.md     [NUEVA] Flujo completo, API, reglas
  ├─ ROLES_PERMISOS_MATRIZ.md              [NUEVA] ACL, JWT, ejemplos
  └─ PARTNERSHIP_INTEGRATION_GUIDE.md      [NUEVA] Cómo integrar partners
```

### Backend – Modelos (MODIFICADO)
```
app/models/database.py
  + Tabla: leads
  + Tabla: partners
  + Tabla: quotations
  + Tabla: invoices (modificar para partner tracking)
  + Tabla: work_orders (nuevas Work Orders para custom)
```

### Backend – Rutas (NUEVA / MODIFICADA)
```
app/routes/
  ├─ leads.py                       [NUEVA]  POST /api/leads/public
  │                                           GET /api/leads/{id}/status
  │                                           (control público + privado)
  │
  ├─ partners.py                    [NUEVA]  GET /api/partners/leads
  │                                           POST /api/partners/leads/{id}/create-tenant
  │                                           GET /api/partners/commissions
  │
  ├─ admin_leads.py                 [NUEVA]  PUT /api/admin/leads/{id}/qualify
  │                                           PUT /api/admin/leads/{id}/quotation
  │                                           GET /api/admin/leads (con filtros)
  │
  ├─ authentication.py               [MOD]   Soporte para rol "partner"
  │                                           POST /api/auth/login (all roles)
  │                                           JWT con partner_id claim
  │
  └─ provisioning.py                 [MOD]   POST /api/provisioning/tenant
  │                                           Integración con leads + factura
```

### Frontend – Svelte (NUEVA)
```
frontend/src/
  ├─ routes/
  │  ├─ onboarding/
  │  │  ├─ +page.svelte             [NUEVA]  Landing sin precios
  │  │  ├─ leads/
  │  │  │  ├─ +page.svelte          [NUEVA]  Formulario multi-etapa
  │  │  │  └─ [id]/
  │  │  │      └─ +page.svelte      [NUEVA]  Status página (public token)
  │  │  └─ partners/
  │  │      ├─ +page.svelte         [NUEVA]  Dashboard partners
  │  │      └─ leads/[id]/
  │  │          └─ +page.svelte     [NUEVA]  Lead detail (partner)
  │  │
  │  └─ admin/
  │      └─ leads/
  │          ├─ +page.svelte        [NUEVA]  Listado admin con calificación
  │          └─ [id]/
  │              └─ +page.svelte    [NUEVA]  Lead detail + cotización
  │
  └─ lib/
      ├─ api/leads.ts               [NUEVA]  Funciones API
      ├─ api/partners.ts            [NUEVA]  Funciones API partners
      ├─ stores/auth.ts             [MOD]   Soporte rol partner
      └─ components/
          ├─ LeadForm.svelte         [NUEVA]  Componente formulario
          ├─ QuotationForm.svelte    [NUEVA]  Componente cotización
          └─ PartnerDashboard.svelte [NUEVA]  Dashboard partner
```

### Frontend – Jinja (MODIFICADO, si aún activo)
```
templates/
  ├─ onboarding_lead_form.html      [NUEVA]  Formulario público
  ├─ onboarding_status.html         [NUEVA]  Status página
  └─ admin/
      └─ leads_management.html      [NUEVA]  Admin calificación
```

### Base de Datos (MIGRACIONES)
```
migrations/ (Alembic)
  ├─ 001_create_leads_table.py      [NUEVA]
  ├─ 002_create_partners_table.py   [NUEVA]
  ├─ 003_create_quotations_table.py [NUEVA]
  ├─ 004_create_work_orders_table.py [NUEVA]
  └─ 005_add_partner_tracking_to_invoices.py [NUEVA]
```

### Tests
```
tests/
  ├─ test_leads_api.py              [NUEVA]  POST /api/leads/public
  ├─ test_partners_api.py           [NUEVA]  Partner endpoints
  ├─ test_admin_leads.py            [NUEVA]  Admin calificación
  ├─ test_partner_acl.py            [NUEVA]  ACL y isolation
  └─ test_provisioning_flow.py      [MOD]   Incluir nuevo flujo
```

### Scripts Operativos
```
scripts/
  ├─ seed_partners.sh               [NUEVA]  Crear partners demo
  ├─ test_partner_onboarding.sh     [NUEVA]  E2E test (lead → tenant)
  └─ migrate_database.sh            [MOD]   Ejecutar migraciones Alembic
```

### Documentación
```
docs/
  ├─ PARTNERSHIP_INTEGRATION_GUIDE.md [NUEVA]  Cómo usar portal de socios
  ├─ API_LEADS_REFERENCE.md         [NUEVA]  Endpoints lead (público/privado)
  ├─ PROVISIONING_FLOW.md           [MOD]   Actualizar con partner
  └─ CHANGELOG.md                   [MOD]   Registrar cambios Phase 3
```

---

## 📊 Cambios en BD (Migraciones)

### Tabla: `leads`
```sql
CREATE TABLE leads (
  id SERIAL PRIMARY KEY,
  company_name VARCHAR(255) NOT NULL,
  industry VARCHAR(100),
  country VARCHAR(100),
  currencies JSONB,
  contact_name VARCHAR(255),
  contact_email VARCHAR(255) UNIQUE NOT NULL,
  contact_phone VARCHAR(20),
  how_found VARCHAR(100),
  
  -- Operación
  current_branches INT DEFAULT 1,
  new_branches_12m BOOLEAN DEFAULT FALSE,
  new_branches_count INT,
  new_branches_when DATE,
  operation_hours VARCHAR(100),
  
  -- Alcance
  modules JSONB,
  main_objective TEXT,
  target_go_live_date DATE,
  
  -- Volúmenes
  invoices_monthly_range VARCHAR(50),
  purchases_monthly_range VARCHAR(50),
  products_total_range VARCHAR(50),
  inventory_movements_range VARCHAR(50),
  
  -- Usuarios
  total_users_range VARCHAR(50),
  user_profiles JSONB,
  
  -- Requerimientos
  requires_multi_branch_inventory BOOLEAN DEFAULT FALSE,
  requires_multi_company BOOLEAN DEFAULT FALSE,
  requires_multi_currency BOOLEAN DEFAULT FALSE,
  requires_traceability BOOLEAN DEFAULT FALSE,
  requires_approvals BOOLEAN DEFAULT FALSE,
  
  -- Integraciones
  requires_e_invoice BOOLEAN DEFAULT FALSE,
  e_invoice_country VARCHAR(100),
  e_invoice_provider VARCHAR(100),
  payment_method VARCHAR(100),
  other_integrations TEXT,
  
  -- Reportes
  required_reports JSONB,
  
  -- Pipeline
  status VARCHAR(50) DEFAULT 'nuevo',
  status_reason TEXT,
  assigned_partner_id INT REFERENCES partners(id),
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  created_by_user_id INT REFERENCES users(id),
  notes TEXT
);
```

### Tabla: `partners`
```sql
CREATE TABLE partners (
  id SERIAL PRIMARY KEY,
  legal_name VARCHAR(255) NOT NULL,
  commercial_name VARCHAR(255),
  country VARCHAR(100) NOT NULL,
  city VARCHAR(100),
  tax_id VARCHAR(50) UNIQUE,
  
  representative_name VARCHAR(255),
  email VARCHAR(255) UNIQUE NOT NULL,
  phone VARCHAR(20),
  
  specialties JSONB,
  coverage_countries JSONB,
  coverage_industries JSONB,
  
  partnership_status VARCHAR(50) DEFAULT 'pendiente',
  nda_signed BOOLEAN DEFAULT FALSE,
  nda_signed_date DATE,
  nda_document_url TEXT,
  agreement_version VARCHAR(20),
  
  commission_percentage DECIMAL(5,2) DEFAULT 50.00,
  payment_method VARCHAR(50),
  
  api_key VARCHAR(255) UNIQUE,
  api_key_created_at TIMESTAMP,
  api_key_last_used TIMESTAMP,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  notes TEXT
);
```

### Tabla: `quotations`
```sql
CREATE TABLE quotations (
  id SERIAL PRIMARY KEY,
  lead_id INT NOT NULL REFERENCES leads(id),
  
  complexity_level VARCHAR(50),
  requires_migration BOOLEAN DEFAULT FALSE,
  migration_source VARCHAR(100),
  years_to_migrate INT DEFAULT 0,
  requires_accounting_parametrization BOOLEAN DEFAULT FALSE,
  requires_formal_training BOOLEAN DEFAULT FALSE,
  
  risks_blockers TEXT,
  internal_sponsor_assigned BOOLEAN DEFAULT FALSE,
  uat_team_available BOOLEAN DEFAULT FALSE,
  hard_deadline DATE,
  legal_compliance_notes TEXT,
  
  phase_1_scope JSONB,
  phase_2_scope JSONB,
  
  requires_jeturing BOOLEAN DEFAULT FALSE,
  requires_jeturing_reason TEXT,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  quoted_at TIMESTAMP,
  created_by_user_id INT REFERENCES users(id)
);
```

---

## 🔐 Seguridad

- ✅ **Validación Pydantic**: todos los payloads validados en entrada.
- ✅ **Rate Limiting**: 5 leads/hora por IP, 10 tenants/día por partner.
- ✅ **JWT + API Key**: autenticación partner con 2 factores.
- ✅ **ACL en queries**: isolation de leads/tenants por partner.
- ✅ **Logs sin secretos**: no loguear teléfono, tokens, stripe keys.
- ✅ **CORS**: solo sajet.us + partners autorizados.
- ✅ **HTTPS**: obligatorio en producción.

---

## 🧪 Pruebas

### Test Unitarios (Backend)
```bash
pytest tests/test_leads_api.py -v
pytest tests/test_partners_api.py -v
pytest tests/test_admin_leads.py -v
pytest tests/test_partner_acl.py -v
```

### Test E2E (Flujo Completo)
```bash
bash scripts/test_partner_onboarding.sh
```

**Pasos manuales reproducibles**:

#### 1. Cliente Público (Lead)
```
1. Acceder a https://localhost:4443/onboarding/leads
2. Completar formulario (8 etapas, ~3 minutos)
3. Enviar
4. Recibir confirmación + email
5. Ver status en https://localhost:4443/onboarding/status/{lead_id}?token={email_token}
```

#### 2. Admin Califica Lead
```
1. Login admin (https://localhost:4443/admin)
2. Ir a "Leads" → buscar by company
3. Abrir lead, revisar formulario
4. Click "Calificar"
5. Asignar partner (dropdown)
6. Enviar
7. Lead status → "calificado"
```

#### 3. Partner Crea Tenant
```
1. Login partner (https://localhost:4443/partners/login)
   - Email + API Key
2. Dashboard: ver leads asignados
3. Abrir lead "Acme Corp" (status = "calificado")
4. Click "Crear tenant"
5. Sistema genera factura + provisiona tenant
6. Recibir: URL + creds admin (email)
7. Copiar creds → enviar a cliente
```

#### 4. Cliente Accede Tenant
```
1. Cliente recibe email con credenciales
2. Accede https://acme-corporation.sajet.us
3. Login con creds admin
4. Modifica contraseña
5. Ve módulos habilitados (ventas, compras, inventario, facturación)
```

### Datos Mínimos Necesarios
```
Clientes de prueba (seed):
  - 3 leads en estado "nuevo"
  - 2 leads en estado "calificado"
  
Partners de prueba:
  - Palm Innovation Services (tax_id: DOM123456, API key activa)
  - Otro partner local (tax_id: otro, API key activa)
  
Planes/módulos (heredado):
  - basic, pro, enterprise (familiar)
  - Módulos: ventas, compras, inventario, facturación, etc.
```

---

## ⚡ Validaciones Críticas

### ✅ No rompe flujo actual
- Onboarding público actual (`/signup` → `/api/checkout` → `/webhook/stripe`) sigue intacto.
- Clientes actuales no ven cambios.
- New feature: `/onboarding/leads` es ruta NUEVA, sin conflicto.

### ✅ Sin datos mock
- Todo desde PostgreSQL.
- Validación en entrada (Pydantic).
- Queries reales.

### ✅ Estándares de marca
- Texto en español.
- Colores Jeturing (sin pink/purple).
- Dark mode por defecto.

### ✅ Observabilidad
- Logs de eventos clave (lead creado, calificado, tenant creado, factura, work order).
- Sin exponer secretos.

---

## 🚨 Riesgos y Plan de Rollback

### Riesgo 1: Duplicados en email
**Mitigación**: Validación unique en BD + check antes de insertar.  
**Rollback**: Revertir migración 001_create_leads_table.py.

### Riesgo 2: Partner ve datos de otros
**Mitigación**: ACL en queries + tests de isolation.  
**Rollback**: Remover filters, validar en tests.

### Riesgo 3: Factura no se emite antes de tenant
**Mitigación**: Transacción DB (ambos o nada), logs de eventos.  
**Rollback**: Evento de rollback: eliminar tenant, marcar lead como "facturado" ← rechazado.

### Riesgo 4: Migración BD falsa
**Mitigación**: Script de migración idempotente, backup pre-migración.  
**Rollback**: `alembic downgrade -1` (Alembic maneja reversa).

### Plan de Rollback General
```bash
# Si necesitas rollback completo:
git revert <PR commit>                    # Revertir código
alembic downgrade base                    # Revertir BD (elimina tablas)
systemctl restart fastapi-app             # Reiniciar servicio
```

---

## 📝 Checklist de Integración (Copiar/Pegar)

Completa este checklist antes de mergear:

### Código
- [ ] Archivos: 0 conflictos con main
- [ ] Imports: sin errores de import
- [ ] Tipos: mypy clean (si aplica)
- [ ] Lint: black + isort clean
- [ ] Tests: 100% pass (pytest)
- [ ] Coverage: >= 80% en nuevas rutas

### BD
- [ ] Migración Alembic: probada en local
- [ ] Rollback: reversible sin pérdida de datos
- [ ] Índices: creados en PK, FK, status
- [ ] Constraints: unique, not null validados

### API
- [ ] Endpoints documentados en Swagger/OpenAPI
- [ ] Payloads: validación Pydantic
- [ ] Respuestas: formato standard (success/data/meta)
- [ ] Errores: códigos 400/401/403/409 documentados
- [ ] Rate limit: implementado

### Frontend
- [ ] Svelte: compilación sin warnings
- [ ] Componentes: reutilizable, con PropTypes/TypeScript
- [ ] Estilos: Tailwind + marca Jeturing
- [ ] Accesibilidad: labels, alt text, WCAG 2.1 AA
- [ ] Responsivo: mobile, tablet, desktop

### Seguridad
- [ ] Validación en entrada (Pydantic)
- [ ] ACL en queries (no exponer datos)
- [ ] CORS: solo dominios autorizados
- [ ] No exponer secretos en logs
- [ ] Tokens: expiración, refresh
- [ ] 2FA: obligatorio para admin/partner

### Testing
- [ ] Tests unitarios: >= 80% coverage
- [ ] Tests E2E: flujo completo funciona
- [ ] Datos de prueba: seed script funciona
- [ ] Manual: pasos reproducibles verificados

### Documentación
- [ ] README: actualizado con nuevas rutas
- [ ] API Docs: Swagger refleja cambios
- [ ] ADRs: decisiones registradas (si aplica)
- [ ] Changelog: versión y cambios listados

### Producción
- [ ] Env vars: todas documentadas (.env.example)
- [ ] Monitoring: logs + alerts configurados
- [ ] Rollback: script probado
- [ ] Notificación: equipo avisado de release

---

## 📞 Contacto y Preguntas

**Maintainer**: [Tu nombre]  
**Slack**: #onboarding-dev  
**Docs**: https://sajet.us/docs/onboarding-publico

---

## 🎉 Resumen

Este PR habilita un **onboarding partner-led, trazable y auditable** que:
- Captura leads sin mostrar precios.
- Permite partners crear tenants directamente.
- Emite facturas y gestiona comisiones 50/50.
- Jeturing solo entra para custom (Work Orders).
- Mantiene control total sobre IP, datos y cumplimiento.

**Alineado con**: Acuerdo de Partnership v2.0 (Feb 2026).

