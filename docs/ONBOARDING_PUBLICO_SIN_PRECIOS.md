# Onboarding Público sin Precios – Sajet.us

## Objetivo General

Captar leads calificados desde landing público (**sin mostrar precios**), dimensionar requerimientos en 2-3 minutos, y transferir al partner (proveedor de servicio) para convertir en tenant activo con factura emitida.

**Principio**: Partner-led, Jeturing-gated (solo custom entra).

---

## 1. Flujo de Usuario Final (Cliente Potencial)

### Entrada: Landing / Botón CTA
```
https://sajet.us/ 
  └─ Botón: "Comenzar evaluación" 
     └─ Lleva a `/onboarding/leads` (formulario público sin precios)
```

### Etapa A: Datos Básicos (1 minuto)
```
Nombre de la empresa
Industria / Giro (dropdown)
País(es) de operación (multiselect)
Moneda(s) principal(es) (based on país)
Nombre del contacto
Email
WhatsApp / Teléfono
¿Cómo se enteró de Sajet? (Referido / Web / Partner / Campaña / Otro)
```

**Validaciones**:
- Email unique (validar duplicidad en BD antes de guardar)
- Teléfono formato internacional (+código país)
- Empresa no vacío, mín 3 caracteres

---

### Etapa B: Operación (1 minuto)
```
¿Cuántas sedes/sucursales hoy?
  → Rango: 1 / 2-5 / 6-10 / 11+

¿Abrirán nuevas sedes en 12 meses?
  → Sí / No
  → Si Sí: cuántas y cuándo (mes/año)

Horario de operación
  → L-V 08:00-17:00 / L-S 24/7 / Otro
```

---

### Etapa C: Alcance Fase 1 (1.5 minutos)
**Checklist de módulos**:
- [ ] Ventas / CRM
- [ ] Compras
- [ ] Inventario / Almacenes
- [ ] Facturación
- [ ] Contabilidad
- [ ] Bancos / Cobros y pagos
- [ ] Proyectos / Servicios
- [ ] RRHH (empleados/nómina)
- [ ] Mantenimiento / Activos
- [ ] Producción (MRP)
- [ ] Helpdesk / Tickets
- [ ] eCommerce

**Campos adicionales**:
```
Objetivo principal (1 frase)
Fecha objetivo para iniciar (date picker)
```

---

### Etapa D: Volúmenes (1 minuto)
```
Facturas/mes estimadas
  → Rango: 0-50 / 51-200 / 201-1000 / 1000+

Compras/mes estimadas
  → Rango: 0-50 / 51-200 / 201-1000 / 1000+

Productos/servicios totales
  → Rango: 0-200 / 201-1000 / 1000+

Movimientos inventario/mes (si aplica)
  → N/A / 0-500 / 500+
```

---

### Etapa E: Usuarios (30 segundos)
```
Usuarios totales estimados
  → Rango: 1-5 / 6-15 / 16-50 / 51+

Perfiles principales (multiselect)
  → Ventas, Compras, Almacén, Contabilidad, Gerencia, Operaciones
```

---

### Etapa F: Requerimientos Clave (30 segundos)
```
[ ] Multi-sede con inventario por sede
[ ] Multi-empresa (filiales)
[ ] Multi-moneda (facturación/compras)
[ ] Trazabilidad lote/serie/caducidad
[ ] Aprobaciones por montos (compras/pagos)
```

---

### Etapa G: Integraciones Esenciales (30 segundos)
```
Facturación electrónica (DTE/CFDI/NCF)
  → Sí / No
  → Si Sí: País + proveedor

Pagos / Cobros
  → Stripe / ACH / Transferencia / Otro

Otros sistemas (texto corto)
```

---

### Etapa H: Reportes (30 segundos)
```
3 reportes indispensables (campos de texto, 1 línea cada uno)
  1. _________________________
  2. _________________________
  3. _________________________
```

---

### Cierre (CTA)
```
┌────────────────────────────────────┐
│  ✅ Formulario completado         │
│                                    │
│  "Un especialista validará tu     │
│  escenario y propone el mejor     │
│  plan en 24-48 horas."            │
│                                    │
│  Botones:                          │
│  [Agendar demo] [Hablar WhatsApp] │
└────────────────────────────────────┘
```

---

## 2. Flujo Operativo (Backend)

### 2.1 Transiciones de Estado del Lead (Pipeline)

```
┌──────────┐
│   NUEVO  │  (form completado, email validado)
└────┬─────┘
     │
     ▼
┌──────────────────┐
│ EN CALIFICACIÓN  │  (partner o Jeturing revisa volúmenes/reqs)
└────┬─────────────┘
     │
     ├─ Rechazo (duplicado / invalid / spam) ──→ RECHAZADO
     │
     └─ Calificación completa ──────────────────┐
                                                 ▼
                                          ┌──────────────┐
                                          │ CALIFICADO   │
                                          └────┬─────────┘
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        │                      │                      │
                        ▼                      ▼                      ▼
                  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
                  │ TENANT CREAR │    │ JETURING     │    │  PROPUESTA   │
                  │   (Standard) │    │  WORK ORDER  │    │  ESPECIAL    │
                  └────┬─────────┘    └────┬─────────┘    └────┬─────────┘
                       │                    │                    │
                       ▼                    ▼                    ▼
                  Tenant creado        Custom aprobado     Negociación
                  + Factura Partner        en backlog        con cliente
                       │                    │                    │
                       └────────────┬───────┴────────────────────┘
                                    │
                                    ▼
                            ┌──────────────┐
                            │ FACTURADO    │ (Partner o Jeturing)
                            └────┬─────────┘
                                 │
                                 ▼
                         ┌──────────────┐
                         │ ACTIVO       │ (Tenant live)
                         │ EN OPERACIÓN │
                         └──────────────┘
```

---

### 2.2 Modelo de Datos (PostgreSQL)

#### Tabla: `leads`
```sql
CREATE TABLE leads (
  id SERIAL PRIMARY KEY,
  
  -- Datos básicos
  company_name VARCHAR(255) NOT NULL,
  industry VARCHAR(100),
  country VARCHAR(100),
  currencies TEXT, -- JSON array
  contact_name VARCHAR(255),
  contact_email VARCHAR(255) UNIQUE NOT NULL,
  contact_phone VARCHAR(20),
  how_found VARCHAR(100), -- 'referido', 'web', 'partner', 'campaign', 'other'
  
  -- Operación
  current_branches INT DEFAULT 1,
  new_branches_12m BOOLEAN DEFAULT FALSE,
  new_branches_count INT,
  new_branches_when DATE,
  operation_hours VARCHAR(100),
  
  -- Alcance (JSON array de módulos seleccionados)
  modules TEXT, -- ['ventas', 'compras', 'inventario', ...]
  main_objective TEXT,
  target_go_live_date DATE,
  
  -- Volúmenes
  invoices_monthly_range VARCHAR(50), -- '0-50', '51-200', '201-1000', '1000+'
  purchases_monthly_range VARCHAR(50),
  products_total_range VARCHAR(50),
  inventory_movements_range VARCHAR(50),
  
  -- Usuarios
  total_users_range VARCHAR(50),
  user_profiles TEXT, -- JSON array
  
  -- Requerimientos clave (booleans)
  requires_multi_branch_inventory BOOLEAN DEFAULT FALSE,
  requires_multi_company BOOLEAN DEFAULT FALSE,
  requires_multi_currency BOOLEAN DEFAULT FALSE,
  requires_traceability BOOLEAN DEFAULT FALSE,
  requires_approvals BOOLEAN DEFAULT FALSE,
  
  -- Integraciones
  requires_e_invoice BOOLEAN DEFAULT FALSE,
  e_invoice_country VARCHAR(100),
  e_invoice_provider VARCHAR(100),
  payment_method VARCHAR(100), -- 'stripe', 'ach', 'transfer', 'other'
  other_integrations TEXT,
  
  -- Reportes
  required_reports TEXT, -- JSON array de 3 items
  
  -- Pipeline
  status VARCHAR(50) DEFAULT 'nuevo', -- 'nuevo', 'en_calificacion', 'calificado', 'tenant_crear', 'jeturing_work_order', 'propuesta_especial', 'facturado', 'activo'
  status_reason TEXT,
  assigned_partner_id INT REFERENCES partners(id), -- NULL si no asignado
  
  -- Tiempos
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Trazabilidad
  created_by_user_id INT REFERENCES users(id), -- Partner o Jeturing admin
  notes TEXT
);

CREATE INDEX idx_leads_email ON leads(contact_email);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_partner ON leads(assigned_partner_id);
CREATE INDEX idx_leads_created ON leads(created_at);
```

#### Tabla: `partners` (nueva)
```sql
CREATE TABLE partners (
  id SERIAL PRIMARY KEY,
  
  -- Identidad
  legal_name VARCHAR(255) NOT NULL,
  commercial_name VARCHAR(255),
  country VARCHAR(100) NOT NULL,
  city VARCHAR(100),
  tax_id VARCHAR(50) UNIQUE,
  
  -- Contacto
  representative_name VARCHAR(255),
  email VARCHAR(255) UNIQUE NOT NULL,
  phone VARCHAR(20),
  
  -- Datos operativos
  specialties TEXT, -- JSON array: 'odoo_implementation', 'accounting', 'payroll', 'retail', 'manufacturing', 'support'
  coverage_countries TEXT, -- JSON array
  coverage_industries TEXT, -- JSON array
  
  -- Acuerdo
  partnership_status VARCHAR(50) DEFAULT 'pendiente', -- 'pendiente', 'activo', 'suspendido', 'terminado'
  nda_signed BOOLEAN DEFAULT FALSE,
  nda_signed_date DATE,
  nda_document_url TEXT, -- S3 o local
  agreement_version VARCHAR(20), -- '2.0', '2.1', etc.
  
  -- Financiero (comisiones)
  commission_percentage DECIMAL(5,2) DEFAULT 50.00, -- 50%
  payment_method VARCHAR(50), -- 'stripe', 'bank_transfer', 'other'
  
  -- Tiempos
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Notas
  notes TEXT
);

CREATE INDEX idx_partners_country ON partners(country);
CREATE INDEX idx_partners_status ON partners(partnership_status);
```

#### Tabla: `quotations` (nueva, para cotizador interno)
```sql
CREATE TABLE quotations (
  id SERIAL PRIMARY KEY,
  
  lead_id INT NOT NULL REFERENCES leads(id),
  
  -- Datos de dimensionamiento interno
  complexity_level VARCHAR(50), -- 'bajo', 'medio', 'alto'
  requires_migration BOOLEAN DEFAULT FALSE,
  migration_source VARCHAR(100), -- 'excel', 'erp_anterior', 'quickbooks', 'otro'
  years_to_migrate INT DEFAULT 0,
  requires_accounting_parametrization BOOLEAN DEFAULT FALSE,
  requires_formal_training BOOLEAN DEFAULT FALSE,
  
  -- Riesgos / Bloqueantes
  risks_blockers TEXT, -- descripción textual
  internal_sponsor_assigned BOOLEAN DEFAULT FALSE,
  uat_team_available BOOLEAN DEFAULT FALSE,
  hard_deadline DATE,
  legal_compliance_notes TEXT,
  
  -- Alcance propuesto (auto desde lead + validación manual)
  phase_1_scope TEXT, -- JSON
  phase_2_scope TEXT, -- JSON (opcional)
  
  -- Decisión
  requires_jeturing BOOLEAN DEFAULT FALSE, -- gating automático (ver 2.4)
  requires_jeturing_reason TEXT, -- razón si true
  
  -- Tiempos
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  quoted_at TIMESTAMP,
  
  -- Trazabilidad
  created_by_user_id INT REFERENCES users(id)
);

CREATE INDEX idx_quotations_lead ON quotations(lead_id);
CREATE INDEX idx_quotations_requires_jeturing ON quotations(requires_jeturing);
```

---

### 2.3 Gating Automático (Cuándo Jeturing "se activa")

**Cuando `quotation.requires_jeturing = TRUE`**:

```
requires_jeturing = TRUE si CUALQUIERA de:
  1. requires_migration = TRUE AND years_to_migrate > 1
  2. migration_source != 'excel' (p. ej. sistema legacy)
  3. leads.requires_multi_currency = TRUE
  4. leads.modules contiene 'produccion' o 'mrp'
  5. leads.modules contiene 'facturacion_electronica'
  6. leads.requires_e_invoice = TRUE
  7. complexity_level = 'alto'
  8. invoices_monthly_range in ('201-1000', '1000+') 
     AND (requires_traceability OR requires_approvals)
  9. total_users_range in ('51+')
     AND modules.count > 5
  10. requires_accounting_parametrization = TRUE 
      AND country in lista_paises_complejos (AR, BR, MX, etc.)
  11. Marca manual "Requiere Jeturing" por partner
```

**Si `requires_jeturing = FALSE`**:
- Partner crea tenant directamente + factura.
- Jeturing solo monitorea (sin fricción).

**Si `requires_jeturing = TRUE`**:
- Lead pasa a estado `jeturing_work_order`.
- Jeturing team revisa, aprueba custom, emite Order Form.
- Se cobra custom (no incluido en comisión 50/50 del partner).

---

### 2.4 Flujo de Provisioning y Facturación

#### Pregunta 1: ¿Factura antes o después de crear tenant?

**Respuesta adoptada: ANTES (pre-creación)**

**Lógica**:
```
Partner marca "Crear tenant" desde lead calificado
  ├─ Backend valida: lead.status = 'calificado'
  │
  ├─ Genera Order Form (SaaS estándar para 12 meses, por defecto)
  │
  ├─ Emite factura al proveedor
  │  └─ email_partner con PDF (proforma o definitiva)
  │
  └─ Cambia lead.status = 'facturado'
  │
  └─ Backend crea tenant
     ├─ Genera slug: {comercio_name_slug}.sajet.us
     ├─ Crea BD Odoo vacía con plantilla base
     ├─ Habilita módulos seleccionados
     └─ Cambia lead.status = 'activo'
```

---

#### Pregunta 2: ¿Subdominio público inmediato o ID interno primero?

**Respuesta adoptada: SUBDOMINIO INMEDIATO**

**Lógica**:
```
Nombre del comercio (input en onboarding):
  "Acme Corporation"
  
Slug generado:
  "acme-corporation" (lowercase, sin acentos, reemplaza espacios con guión)
  
Validación:
  1. Disponibilidad en DNS / Cloudflare
  2. No conflicto con dominios reservados (admin, api, portal, etc.)
  3. Uniq en BD (leads.subdomain unique)
  
URL final:
  https://acme-corporation.sajet.us
  
Tipo de provisioning:
  LXC en PCT 105 + Cloudflare tunnel + DNS entry
```

---

#### Pregunta 3: ¿Proveedor entra como "Consultor" o solo desde portal?

**Respuesta adoptada: SOLO DESDE PORTAL (acceso de lectura + gestión onboarding)**

**Justificación**:
- Simplifica permisos (no requiere crear rol `consultor` dentro Odoo).
- Evita acceso al código/datos sensibles del tenant.
- Permite auditoría y control de IP.
- Partner puede entregar acceso `admin` al cliente final directamente.

**Modelo de permisos del Partner**:
```
Desde Portal (https://sajet.us/partners/leads)
  ├─ Ver leads propios
  ├─ Calificar / marcar "Crear tenant"
  ├─ Ver estado de factura (pagada/pending)
  ├─ Adjuntar documentos (SOW, minutas, levantamientos)
  ├─ Ver tenant creado + credentials admin
  └─ Solicitar Work Order a Jeturing (integración, custom)

Dentro del Tenant Odoo (https://acme-corporation.sajet.us)
  ├─ Partner recibe usuario `consultor` (opcional)
  │  Acceso: configuración de módulos + datos mínimos
  │  NO puede: acceder a data financiera, crear usuarios admin
  │
  └─ Cliente Final accede como admin (credencial en email)
     └─ Configura todo, capacita equipo, operación
```

---

## 3. Contratos de API (Endpoints)

### 3.1 Endpoint: Crear/Guardar Lead (público)

```http
POST /api/leads/public
Content-Type: application/json

{
  "company_name": "Acme Corp",
  "industry": "retail",
  "country": "MX",
  "currencies": ["MXN"],
  "contact_name": "Juan García",
  "contact_email": "juan@acme.mx",
  "contact_phone": "+52 55 1234 5678",
  "how_found": "web",
  
  "current_branches": 2,
  "new_branches_12m": true,
  "new_branches_count": 3,
  "new_branches_when": "2026-06-30",
  "operation_hours": "L-S 08:00-20:00",
  
  "modules": ["ventas", "compras", "inventario", "facturacion"],
  "main_objective": "Automatizar ventas y reducir tiempo en inventario",
  "target_go_live_date": "2026-04-15",
  
  "invoices_monthly_range": "201-1000",
  "purchases_monthly_range": "51-200",
  "products_total_range": "201-1000",
  "inventory_movements_range": "500+",
  
  "total_users_range": "6-15",
  "user_profiles": ["ventas", "almacen", "contabilidad"],
  
  "requires_multi_branch_inventory": true,
  "requires_multi_company": false,
  "requires_multi_currency": false,
  "requires_traceability": true,
  "requires_approvals": false,
  
  "requires_e_invoice": true,
  "e_invoice_country": "MX",
  "e_invoice_provider": "SAT",
  "payment_method": "stripe",
  "other_integrations": "Integracion con sistema de CRM Salesforce",
  
  "required_reports": [
    "Ventas por sucursal",
    "Margen de ganancia",
    "Antigüedad de cuentas por cobrar"
  ]
}

Response 201:
{
  "success": true,
  "data": {
    "lead_id": 42,
    "status": "nuevo",
    "company_name": "Acme Corp",
    "contact_email": "juan@acme.mx",
    "created_at": "2026-02-14T10:30:00Z",
    "next_steps": "Un especialista revisará tu información en 24-48 horas."
  },
  "meta": {
    "lead_url": "https://sajet.us/onboarding/status/42"
  }
}

Response 400:
{
  "success": false,
  "error": "VALIDATION_ERROR",
  "detail": "contact_email ya existe en el sistema"
}

Response 409:
{
  "success": false,
  "error": "DUPLICATE_LEAD",
  "detail": "Ya existe un lead con este email. Status: en_calificacion"
}
```

---

### 3.2 Endpoint: Ver Estado del Lead (público + login)

```http
GET /api/leads/{lead_id}/status?token={email_token}
(o autenticado con JWT si cliente logueado)

Response 200:
{
  "success": true,
  "data": {
    "lead_id": 42,
    "status": "calificado",
    "status_reason": "Volúmenes validados, preparado para provisioning",
    "company_name": "Acme Corp",
    "contact_email": "juan@acme.mx",
    "assigned_partner": {
      "id": 5,
      "name": "Palm Innovation Services"
    },
    "created_at": "2026-02-14T10:30:00Z",
    "updated_at": "2026-02-14T14:00:00Z",
    "next_action": "Partner creará tenant y te contactará",
    "cta_buttons": [
      {
        "label": "Agendar demo",
        "url": "https://calendly.com/sajet/demo"
      },
      {
        "label": "Hablar por WhatsApp",
        "url": "https://wa.me/+52..."
      }
    ]
  }
}
```

---

### 3.3 Endpoint: Partner crea Tenant desde Lead Calificado

```http
POST /api/partners/leads/{lead_id}/create-tenant
Authorization: Bearer {partner_jwt_token}
X-API-Key: {partner_api_key}

Response 201:
{
  "success": true,
  "data": {
    "tenant_id": 12,
    "subdomain": "acme-corporation",
    "tenant_url": "https://acme-corporation.sajet.us",
    "invoice": {
      "id": "INV-2026-02-0042",
      "amount": 1200.00,
      "currency": "USD",
      "due_date": "2026-03-14",
      "pdf_url": "https://invoices.sajet.us/INV-2026-02-0042.pdf"
    },
    "admin_credentials": {
      "email": "admin@acme-corporation.sajet.us",
      "temp_password": "TempPass123!",
      "reset_url": "https://acme-corporation.sajet.us/reset-password?token=..."
    },
    "modules_enabled": ["ventas", "compras", "inventario", "facturacion"],
    "status": "activo",
    "created_at": "2026-02-14T15:30:00Z"
  }
}

Response 400:
{
  "success": false,
  "error": "LEAD_NOT_QUALIFIED",
  "detail": "El lead debe estar en estado 'calificado' para crear tenant"
}
```

---

### 3.4 Endpoint: Admin califica Lead (con decisión Jeturing)

```http
PUT /api/admin/leads/{lead_id}/qualify
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "status": "calificado",
  "status_reason": "Volúmenes validados, sin custom",
  "assigned_partner_id": 5,
  "requires_jeturing": false
}

Response 200:
{
  "success": true,
  "data": {
    "lead_id": 42,
    "status": "calificado",
    "assigned_partner": "Palm Innovation Services",
    "requires_jeturing": false,
    "next_step": "Partner puede crear tenant"
  }
}

Response 422:
{
  "success": false,
  "error": "INVALID_STATUS_TRANSITION",
  "detail": "No puedes pasar de 'nuevo' a 'activo' sin 'calificado'"
}
```

---

### 3.5 Endpoint: Crear/Actualizar Cotización (Admin + Partner)

```http
POST /api/admin/leads/{lead_id}/quotation
Authorization: Bearer {admin_or_partner_jwt_token}
Content-Type: application/json

{
  "complexity_level": "medio",
  "requires_migration": true,
  "migration_source": "erp_anterior",
  "years_to_migrate": 2,
  "requires_accounting_parametrization": true,
  "requires_formal_training": true,
  
  "risks_blockers": "Cliente requiere integración con sistema legacy de contabilidad",
  "internal_sponsor_assigned": true,
  "uat_team_available": false,
  "hard_deadline": "2026-04-15",
  "legal_compliance_notes": "Sujeto a normas locales de México",
  
  "phase_1_scope": {
    "modules": ["ventas", "compras", "inventario", "facturacion"],
    "users": 15,
    "duration_days": 30
  },
  "phase_2_scope": {
    "modules": ["contabilidad", "proyectos"],
    "users": 5,
    "duration_days": 15
  }
}

Response 201:
{
  "success": true,
  "data": {
    "quotation_id": 99,
    "lead_id": 42,
    "complexity_level": "medio",
    "requires_jeturing": true,
    "requires_jeturing_reason": "Migration > 1 year + accounting parametrization required",
    "phase_1_scope": {...},
    "created_at": "2026-02-14T16:00:00Z"
  }
}
```

---

## 4. Seguridad y Validaciones

### 4.1 Rate Limiting
```
Endpoint: POST /api/leads/public
Limit: 5 por IP por hora (prevenir spam)
Strategy: sliding window via Redis (si disponible)
Fallback: simple in-memory counter

Endpoint: POST /api/partners/leads/{lead_id}/create-tenant
Limit: 10 por partner por día
Valida: X-API-Key válida y no expirada
```

### 4.2 Validaciones Pydantic

```python
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import date

class LeadPublic(BaseModel):
    company_name: str = Field(..., min_length=3, max_length=255)
    industry: str
    country: str
    currencies: List[str]
    contact_name: str = Field(..., min_length=3)
    contact_email: EmailStr
    contact_phone: str = Field(regex=r'^\+?[0-9\s\-\(\)]+$')
    how_found: Literal['referido', 'web', 'partner', 'campaign', 'other']
    
    modules: List[str]
    invoices_monthly_range: Literal['0-50', '51-200', '201-1000', '1000+']
    # ... más campos
    
    @validator('contact_email')
    def email_not_exists(cls, v):
        # Query DB para validar uniqueness
        if Lead.query.filter_by(contact_email=v).first():
            raise ValueError('Email ya existe')
        return v
    
    @validator('target_go_live_date')
    def date_is_future(cls, v):
        if v <= date.today():
            raise ValueError('Fecha debe ser en el futuro')
        return v

    class Config:
        schema_extra = {
            "example": {
                "company_name": "Acme Corp",
                "industry": "retail",
                # ...
            }
        }
```

### 4.3 No exponer secretos en logs

```python
import logging

logger = logging.getLogger(__name__)

def create_lead(lead_data: LeadPublic):
    logger.info(f"Lead creado: {lead_data.company_name} ({lead_data.contact_email})")
    # NO loguear: contact_phone, full payload con datos sensibles
    # NO loguear: tokens, API keys, stripe data
```

---

## 5. Observabilidad

### 5.1 Eventos a Loguear

| Evento | Nivel | Contexto |
|--------|-------|---------|
| Lead creado | INFO | lead_id, company, email |
| Duplicado detectado | WARN | email, lead_id anterior |
| Lead calificado | INFO | lead_id, partner asignado |
| Cotización creada | INFO | quotation_id, complexity, requires_jeturing |
| Tenant creado | INFO | tenant_id, subdomain, módulos |
| Factura emitida | INFO | invoice_id, amount, partner |
| Jeturing activado | WARN | lead_id, reason |
| Errores de validación | ERROR | lead_id, field, error_msg |

### 5.2 Ejemplo de log

```json
{
  "timestamp": "2026-02-14T15:32:00Z",
  "level": "INFO",
  "event": "lead.qualified",
  "lead_id": 42,
  "company_name": "Acme Corp",
  "assigned_partner_id": 5,
  "requires_jeturing": false,
  "user_id": 123
}
```

---

## 6. Roadmap de Implementación

### Fase 1: MVP (Lead → Tenant)
1. BD: tabla `leads` + `quotation`
2. API: `POST /api/leads/public`
3. API: `PUT /api/admin/leads/{id}/qualify`
4. API: `POST /api/partners/leads/{id}/create-tenant`
5. Email: transaccionales (lead recibido, calificado, tenant creado)
6. Frontend: formulario público sin precios + status page

### Fase 2: Portal de Socios
1. Tabla `partners` + autenticación partner
2. Dashboard: leads propios, pipeline, estado facturas
3. Adjuntar documentos (SOW, minutas)
4. Work Order (solicitar custom a Jeturing)

### Fase 3: Automatización
1. Gating automático (detección de `requires_jeturing`)
2. Email a Jeturing si custom detectado
3. Webhook: partner paga factura → tenant provisioning automático
4. SMS/WhatsApp: notificación a cliente cuando tenant listo

### Fase 4: Analytics
1. Dashboard: conversion rate (lead → tenant)
2. Partner performance (leads, closed, MRR)
3. Reportes: comisiones mensuales

---

## 7. Notas Finales

- **Sin precios en UI pública**: confirmado.
- **Partner-led**: partner crea tenant + factura.
- **Jeturing-gated**: solo custom entra (multi-empresa, migraciones, integraciones).
- **Trazabilidad obligatoria**: todo en portal de socios, comisiones auditables.
- **Factura antes de crear tenant**: genera confianza y orden fiscal.
- **Subdominio público inmediato**: mejora UX y marketing.
- **Partner solo desde portal**: simplifica arquitectura, no requiere rol Odoo.

