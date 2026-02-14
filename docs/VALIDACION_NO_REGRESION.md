# Validación de No-Regresión: Flujo Actual `/signup → /checkout → /webhook/stripe`

## 🎯 Objetivo

Asegurar que el nuevo flujo de onboarding público (**sin precios**) + **rol Proveedor** **NO rompe** el flujo de signup/checkout existente para tenants SaaS actuales.

---

## 1. Flujo Actual (Heredado) – Estado Baseline

```
Usuario Stripe
  │
  ├─ Accede a https://sajet.us/signup
  │  └─ Forma: email, empresa, plan (VISIBLE precios)
  │
  └─ POST /api/checkout
     ├─ Crea customer en Stripe (o reutiliza)
     ├─ Retorna session Stripe (checkout URL)
     └─ Usuario redirige a Stripe hosted checkout
        │
        ├─ Ingresa tarjeta
        │
        └─ Confirma compra
           │
           └─ Stripe webhook: POST /webhook/stripe
              │
              ├─ Valida signature (header X-Stripe-Signature)
              ├─ Procesa evento (charge.succeeded, customer.subscription.created)
              ├─ Crea customer + subscription en BD local
              ├─ Provisiona tenant (LXC + Odoo)
              ├─ Envía email confirmación + credenciales admin
              │
              └─ Usuario accede a https://{subdomain}.sajet.us
```

**Archivos involucrados**:
- `templates/onboarding_form.html` (formulario con precios)
- `app/routes/onboarding.py` (POST /api/checkout)
- `app/routes/webhooks.py` (POST /webhook/stripe)
- `app/services/odoo_provisioner.py` (provisioning LXC)
- `app/models/database.py` (Customer, Subscription tables)

---

## 2. Nuevo Flujo (ADICIONAL) – Lead Public

```
Prospecto sin dinero decidido
  │
  ├─ Accede a https://sajet.us/onboarding/leads
  │  └─ Forma: sin precios, solo módulos y volúmenes
  │
  └─ POST /api/leads/public
     ├─ Crea lead (estado "nuevo")
     ├─ Email transaccional al prospecto ("validamos en 24-48h")
     ├─ Email interno a Jeturing admin ("nuevo lead")
     │
     └─ Lead pasa a pipeline (Admin o Partner califica)
        │
        ├─ Si Partner → Crea tenant directamente
        │  └─ Se genera factura partner + tenant activo
        │
        └─ Si Custom detectado → Jeturing Work Order
           └─ Custom se cotiza/negocia
```

**Archivos involucrados**:
- `templates/onboarding_lead_form.html` (formulario sin precios)
- `app/routes/leads.py` (POST /api/leads/public)
- `app/models/database.py` (Lead, Partner, Quotation tables)
- `app/routes/partners.py` (POST /api/partners/leads/{id}/create-tenant)

---

## 3. Matriz de No-Regresión

| Elemento | Flujo Actual | Nuevo Flujo | Estado Esperado | ✅ / ❌ |
|----------|--------------|-------------|-----------------|---------|
| **Rutas** | `/signup` | `/onboarding/leads` | Distintas, sin conflicto | ✅ |
| | `/api/checkout` | `/api/leads/public` | Distintas, sin conflicto | ✅ |
| | `/webhook/stripe` | `/webhook/stripe` | **Mismo endpoint** | ⚠️ Validar |
| **Templates** | `onboarding_form.html` | `onboarding_lead_form.html` | Archivos diferentes | ✅ |
| **Modelos BD** | `Customer` | (sin cambio) | Intacto | ✅ |
| | `Subscription` | (sin cambio) | Intacto | ✅ |
| | (nuevo) | `Lead` | Nueva tabla | ✅ |
| | (nuevo) | `Partner` | Nueva tabla | ✅ |
| **Provisioning** | `odoo_provisioner.py` | `odoo_provisioner.py` | **Mismo módulo** | ⚠️ Validar |
| **Auth** | JWT admin/tenant | JWT + partner | Nuevo rol, sin conflicto | ✅ |

### ⚠️ Puntos Críticos (Validar)

#### 1️⃣ Webhook Stripe (`POST /webhook/stripe`)

**Actual**:
```python
@app.post("/webhook/stripe")
async def webhook_stripe(request: Request):
    event = stripe.Webhook.construct_event(...)  # Valida signature
    
    if event["type"] == "charge.succeeded":
        # Crea customer + subscription
        # Provisiona tenant
        
    return {"success": True}
```

**Riesgo**: Si agregamos validación de payload, podría fallar en eventos antiguos.

**Validación**:
```bash
# Test 1: Webhook actual sigue funcionando
curl -X POST http://localhost:4443/webhook/stripe \
  -H "X-Stripe-Signature: {signature}" \
  -d @test_event_charge_succeeded.json

# Test 2: Webhook no impactado por nuevas tablas
pytest tests/test_webhook_stripe.py::test_charge_succeeded
```

---

#### 2️⃣ Provisioning (`odoo_provisioner.py`)

**Actual**:
```python
async def provision_tenant(customer_id: int, subscription: Subscription):
    # Crea LXC en PCT 105
    # Retorna subdomain + creds
```

**Nuevo**:
```python
# Partner crea tenant directamente
# Mismo provisioning, pero iniciado desde /api/partners/leads/{id}/create-tenant
```

**Riesgo**: Si provisioning tiene estado local (en_process, etc.), podría conflict.

**Validación**:
```bash
# Test: Provisioning sin cambios
pytest tests/test_provisioning.py::test_provision_tenant_from_checkout
pytest tests/test_provisioning.py::test_provision_tenant_from_partner

# Ambos deben crear tenant identicamente
```

---

#### 3️⃣ Emails Transaccionales

**Actual**:
```python
# Checkout → send_confirmation_email(customer_email)
```

**Nuevo**:
```python
# Lead → send_lead_received_email(lead_email)
# Partner → send_tenant_created_email(customer_email)
```

**Riesgo**: Si email service tiene límites, podría saturarse.

**Validación**: Logs muestran ambos flujos sin errores de envío.

---

## 4. Plan de Validación (Test Suite)

### 4.1 Unit Tests

```bash
# Flujo actual intacto
pytest tests/test_checkout_api.py -v
  ✓ test_post_checkout_creates_session
  ✓ test_post_checkout_validates_plan
  ✓ test_webhook_stripe_creates_customer
  ✓ test_webhook_stripe_provisions_tenant

# Flujo nuevo isolado
pytest tests/test_leads_api.py -v
  ✓ test_post_leads_public_creates_lead
  ✓ test_post_leads_public_validates_email_unique
  ✓ test_partner_create_tenant_from_lead
  ✓ test_partner_acl_isolation

# Sin conflictos
pytest tests/test_no_regression.py -v
  ✓ test_old_checkout_routes_unchanged
  ✓ test_new_leads_routes_dont_interfere
  ✓ test_webhook_stripe_still_works
```

---

### 4.2 Integration Tests

```bash
# Escenario 1: Cliente paga vía Stripe (flujo actual)
bash scripts/test_checkout_flow.sh
  1. POST /api/checkout (create session)
  2. Mock Stripe webhook: charge.succeeded
  3. Validar tenant creado + email enviado
  4. Validar customer en BD

# Escenario 2: Prospecto regresa, Partner crea tenant (flujo nuevo)
bash scripts/test_partner_flow.sh
  1. POST /api/leads/public (create lead)
  2. Admin: PUT /api/admin/leads/{id}/qualify (assign partner)
  3. Partner: POST /api/partners/leads/{id}/create-tenant
  4. Validar tenant creado + factura emitida + email enviado
  5. Validar lead status → activo

# Escenario 3: Ambos en paralelo (test stress)
bash scripts/test_parallel_flows.sh
  1. Ejecutar checkout + partner en paralelo
  2. Validar 2 tenants creados sin conflictos
  3. Validar BD sin corruption
```

---

### 4.3 Regression Tests (Checklist Manual)

| Caso | Pasos | Esperado | ✅/❌ |
|------|-------|----------|------|
| **Signup viejo** | 1. Ir a /signup | Forma con precios visible | ✅ |
| | 2. Llenar + submit | Redirige a Stripe checkout | ✅ |
| | 3. Pagar (mock) | Webhook recibido | ✅ |
| | 4. Acceder tenant | Tenant operativo | ✅ |
| **Lead nuevo** | 1. Ir a /onboarding/leads | Forma sin precios visible | ✅ |
| | 2. Llenar + submit | Email confirmación | ✅ |
| | 3. Admin califica | Lead → calificado | ✅ |
| | 4. Partner crea tenant | Tenant creado + factura | ✅ |
| **Auth** | 1. Login admin | JWT con role=admin | ✅ |
| | 2. Login partner | JWT con role=partner + API Key | ✅ |
| | 3. Login tenant | JWT con role=tenant + tenant_id | ✅ |
| **Permisos** | 1. Partner ver admin leads | 403 Forbidden | ✅ |
| | 2. Partner ver otros partners' leads | 403 Forbidden | ✅ |
| | 3. Tenant ver otro tenant | 403 Forbidden | ✅ |

---

## 5. Criterios de Aceptación

✅ **PASS** si:
1. Todos los tests de `test_checkout_api.py` pasan.
2. Webhook Stripe continúa recibiendo eventos correctamente.
3. Provisioning crea tenants identicamente desde ambos flujos.
4. ACL previene acceso cruzado (partner → otro partner, tenant → otro tenant).
5. Logs muestran ambos flujos sin errores.
6. BD no tiene corrupción (constraints, foreign keys intactos).
7. Rollback plan funciona (revertir migración deja BD limpia).

❌ **FAIL** si:
- Checkout actual retorna error 5xx.
- Webhook no procesa eventos Stripe.
- Provisioning falla en cualquiera de los flujos.
- Partner accede datos de otro partner.
- Tenant accede datos de otro tenant.

---

## 6. Antes de Mergear: Checklist Automático

```bash
#!/bin/bash
set -e

echo "🚀 Validación Pre-Merge"

# 1. Tests unitarios
echo "1️⃣  Unit tests..."
pytest tests/ -v --tb=short

# 2. Migración BD
echo "2️⃣  DB migration..."
alembic upgrade head

# 3. Tests E2E
echo "3️⃣  E2E tests (checkout + partner flows)..."
bash scripts/test_checkout_flow.sh
bash scripts/test_partner_flow.sh

# 4. Lint + type check
echo "4️⃣  Code quality..."
black --check app/
isort --check-only app/
mypy app/ --ignore-missing-imports

# 5. Seed de datos de prueba
echo "5️⃣  Seed test data..."
bash scripts/seed_partners.sh
bash scripts/seed_test_leads.sh

echo "✅ Todas las validaciones pasaron. Listo para mergear."
```

---

## 7. Rollback Plan (En Caso de Regresar)

```bash
# Si encuentras bug post-merge:

# 1. Revertir PR
git revert <PR commit hash>
git push origin main

# 2. Revertir migraciones BD
alembic downgrade -1  # Vuelve a estado anterior

# 3. Restart servicio
systemctl restart fastapi-app

# 4. Validar flujo actual
curl https://sajet.us/api/checkout
# Debe retornar 200 (sesión Stripe)
```

---

## 8. Notas

- **No hay breaking changes** en rutas públicas (`/signup`, `/api/checkout`, `/webhook/stripe`).
- **Nuevas rutas**: `/onboarding/leads`, `/api/leads/public`, `/api/partners/leads/{id}/create-tenant`.
- **Nuevas tablas**: `leads`, `partners`, `quotations`, `work_orders` (aisladas, sin tocar existentes).
- **Provisioning**: mismo código, nuevos entry points.
- **Auth**: JWT con soporte nuevo rol `partner`, sin cambios en `admin`/`tenant`.

---

