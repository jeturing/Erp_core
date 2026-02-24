# 🏦 Flujo de Pago y Dispersión a Proveedores — Arquitectura Completa

## 📋 Contexto

**Objetivo**: Implementar un sistema de pago y dispersión de fondos con soporte para:
1. **Recibir dinero** de clientes (Stripe → Mercury account)
2. **Pagar a proveedores** (dispersión vía Mercury/ACH/Wire)
3. **KYC** para validar cuentas de proveedores
4. **Reconciliación** automática Stripe ↔ Mercury

---

## 🎯 Flujo General de Dinero

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENTE (Cliente Jeturing)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       STRIPE (Payment)                           │
│  - Recibe pagos del cliente                                      │
│  - Genera invoices, webhooks                                     │
│  - Conecta con Mercury vía Stripe Connect (opcional)             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MERCURY ACCOUNT                              │
│  - Cuenta bancaria de Jeturing (US, depósitos Stripe)           │
│  - Balance actual disponible para pagos                         │
│  - Historial de transacciones (ACH, Wire, etc.)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│         MERCURY PAYOUT ENGINE (Dispersión)                       │
│  - ACH Transfer (proveedores US)                                │
│  - Wire Transfer (proveedores internacionales)                  │
│  - Check Mailing (legacy support)                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PROVEEDORES (Benef)                            │
│  - Validación de cuenta (KYC)                                    │
│  - Reciben pagos según schedule                                 │
│  - Confirmación de deposito                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes a Implementar

### 1️⃣ **mercury_client.py** — Cliente de Mercury Banking API

**Responsabilidades**:
- Conectarse a Mercury API (SDK Python o HTTP client)
- Obtener balance de la cuenta
- Crear transfers (ACH, Wire)
- Listar transacciones
- Validar cuentas de beneficiarios

**Métodos principales**:
```python
class MercuryClient:
    def get_account_balance() -> Dict  # Saldo actual
    def get_account_details() -> Dict  # Info de la cuenta Jeturing
    def list_transactions(limit, offset) -> List
    def create_ach_transfer(beneficiary, amount, memo) -> Dict
    def create_wire_transfer(beneficiary, amount, memo) -> Dict
    def validate_bank_account(account_number, routing_number) -> Dict
    def get_transfer_status(transfer_id) -> Dict
    def list_bank_accounts() -> List  # Cuentas vinculadas
```

### 2️⃣ **payment_processor.py** — Orquestador Unificado

**Responsabilidades**:
- Decisiones de enrutamiento (Stripe vs Mercury)
- Cálculo de comisiones y montos netos
- Validación de reglas de negocio
- Logging y auditoría de transacciones

**Métodos principales**:
```python
class PaymentProcessor:
    def process_customer_payment(invoice_id, stripe_event) -> Dict
        # Recibir pago del cliente, actualizar balance
    
    def calculate_provider_payout(
        provider_id, 
        invoice_id, 
        amount
    ) -> Dict
        # Calcular monto neto (menos comisiones, retenciones, etc.)
    
    def authorize_payout(payout_request) -> Dict
        # Validar y autorizar pago (reglas, KYC, balance)
    
    def execute_payout(authorized_payout) -> Dict
        # Ejecutar transferencia vía Mercury
    
    def reconcile_stripe_mercury() -> Dict
        # Comparar saldos y registrar discrepancias
```

### 3️⃣ **treasury_manager.py** — Gestor de Tesorería

**Responsabilidades**:
- Dashboard de flujo de caja
- Reportes de ingresos/egresos
- Forecasting de pagos pendientes
- Alertas de saldo bajo

**Métodos principales**:
```python
class TreasuryManager:
    def get_cash_flow_summary(start_date, end_date) -> Dict
    def get_pending_payouts() -> List
    def get_mercury_balance() -> Dict
    def get_stripe_balance() -> Dict
    def forecast_cash_needs(days_ahead) -> Dict
    def get_transaction_logs(filter) -> List
```

### 4️⃣ **routes/payments.py** — Endpoints REST

**Endpoints**:
```
POST   /api/payments/process-invoice          # Procesar pago de cliente
GET    /api/payments/balance                  # Balance actual
POST   /api/payouts/create                    # Crear dispersión a proveedor
GET    /api/payouts/{id}                      # Estado de pago
GET    /api/payouts                           # Listar pagos
POST   /api/providers/kyc-check               # Validar KYC proveedor
POST   /api/treasury/summary                  # Resumen tesorería
```

---

## 💾 Modelos de Base de Datos

### Nuevas tablas necesarias:

#### **provider_accounts** — Cuentas bancarias de proveedores
```sql
CREATE TABLE provider_accounts (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES partners(id),
    account_holder_name VARCHAR(200) NOT NULL,
    account_number VARCHAR(50) NOT NULL UNIQUE,
    routing_number VARCHAR(20),
    bank_name VARCHAR(200),
    account_type VARCHAR(20),  -- "checking", "savings"
    currency VARCHAR(3) DEFAULT 'USD',
    is_verified BOOLEAN DEFAULT FALSE,  -- KYC checked
    kyc_status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected
    kyc_checked_at TIMESTAMP,
    metadata_json JSONB,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

#### **payout_requests** — Solicitudes de pago a proveedores
```sql
CREATE TABLE payout_requests (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES partners(id),
    invoice_id INTEGER REFERENCES invoices(id),
    amount FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'pending',  -- pending, authorized, processing, completed, failed
    transfer_type VARCHAR(20),  -- ach, wire, check
    provider_account_id INTEGER REFERENCES provider_accounts(id),
    mercury_transfer_id VARCHAR(100),  -- ID de Mercury
    commission FLOAT DEFAULT 0,  -- Comisión Mercury/banco
    net_amount FLOAT NOT NULL,  -- Monto final (amount - commission)
    notes TEXT,
    requested_at TIMESTAMP DEFAULT now(),
    authorized_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_reason TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

#### **mercury_transactions** — Espejo de transacciones Mercury
```sql
CREATE TABLE mercury_transactions (
    id SERIAL PRIMARY KEY,
    mercury_transaction_id VARCHAR(100) UNIQUE,
    transaction_type VARCHAR(20),  -- transfer_in, transfer_out, fee, interest
    amount FLOAT NOT NULL,
    currency VARCHAR(3),
    description TEXT,
    counterparty VARCHAR(200),
    status VARCHAR(20),  -- pending, posted, failed, canceled
    posted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## 🔐 Integración KYC

**Flujo**:
1. Proveedor registro → datos bancarios
2. Sistema valida con Mercury API (si disponible) o manualmente
3. KYC aprobado → puede recibir pagos
4. Re-validación periódica (ej: anual)

**Campos requeridos**:
- Nombre del titular
- Número de cuenta
- Routing number (US) o IBAN (internacionales)
- Tipo de cuenta (checking/savings)
- Banco

**Métodos**:
```python
def validate_bank_account(account_number, routing_number) -> bool
    # Llamar Mercury API o usar Plaid/Dwolla

def mark_account_verified(provider_account_id) -> bool
    # Marcar cuenta como verificada

def is_account_verified(provider_account_id) -> bool
    # Verificar si puede recibir pagos
```

---

## 🛠️ Configuración Requerida

**Variables de entorno** (agregar a `.env.production`):

```env
# Mercury Banking
MERCURY_API_KEY=<key>
MERCURY_API_URL=https://api.mercury.com
MERCURY_ACCOUNT_ID=<account_id>
MERCURY_WEBHOOK_SECRET=<secret>

# Stripe Connect (para depósitos automáticos)
STRIPE_CONNECT_ACCOUNT_ID=acct_xxx
STRIPE_CONNECT_WEBHOOK_SECRET=<secret>

# Configuración de pagos
PAYOUT_MIN_AMOUNT=5  # Mínimo a dispersar
PAYOUT_MAX_AMOUNT=50000  # Máximo por transferencia
MERCURY_ACH_FEE=0  # ACH gratuito en Mercury
MERCURY_WIRE_FEE=15  # Wire fee
MERCURY_DAILY_LIMIT=100000  # Límite diario de dispersión
```

---

## 🔄 Flujo Completo: De Cliente a Proveedor

```
1. Cliente paga invoice vía Stripe
   │
   ├─→ Stripe webhook: payment_intent.succeeded
   ├─→ Invoice marcada como "paid"
   └─→ Saldo Mercury actualizado (sync automático)

2. Sistema detecta comisión owed a proveedor
   │
   ├─→ Crea payout_request (pending)
   ├─→ Valida KYC del proveedor
   └─→ Calcula monto neto (monto - comisión)

3. Admin autoriza pago
   │
   ├─→ Payout request → "authorized"
   ├─→ Verifica balance disponible en Mercury
   └─→ Bloquea fondos (hold)

4. Sistema ejecuta transferencia
   │
   ├─→ Llama Mercury API: create_transfer()
   ├─→ Guarda mercury_transfer_id
   └─→ Status → "processing"

5. Mercury confirma transferencia
   │
   ├─→ Webhook: transfer.completed
   ├─→ Payout request → "completed"
   └─→ Settlement línea marcada como pagada

6. Proveedor recibe fondos
   │
   └─→ Notification email con confirmación
```

---

## 🔗 Integración con Modelos Existentes

### **Settlement** (ya existe)
- Agregue field: `payout_status` (pending, paid, partially_paid)
- Agregue field: `mercury_settlement_id`
- Referencia a payout_requests

### **Partner** (proveedores)
- Agregue relación: `provider_accounts` (1:N)
- Agregue field: `kyc_status` (pending, approved, rejected)
- Agregue field: `preferred_payout_method` (ach, wire)

### **Commission** (comisiones)
- Agregue field: `payout_request_id` (FK a payout_requests)
- Agregue field: `payout_status` (pending, paid)

---

## 📊 Admin Dashboard

**Secciones**:
1. **Balance Actual**: Mercury + Stripe balance en tiempo real
2. **Payouts Pendientes**: Lista de pagos por hacer (by priority)
3. **Cash Flow**: Gráfico ingresos vs egresos (últimos 30 días)
4. **Providers**: KYC status, últimos pagos, balance owed
5. **Transacciones**: Log de todas las transacciones Mercury ↔ Stripe

---

## ⚠️ Consideraciones de Seguridad

1. **PCI Compliance**: No guardar números de tarjeta
2. **Encryption**: Números de cuenta encriptados en BD (usar `FIELD_ENCRYPT_KEY`)
3. **API Keys**: Almacenar en .env.production (no commit)
4. **Auditoría**: Registrar todas las transacciones (quién, cuándo, qué, resultado)
5. **Rate Limiting**: Máximo 1 request/segundo a Mercury API
6. **Webhooks Validation**: Validar signature de Mercury antes de procesar
7. **Account Lockdown**: Si balance < $5K, alertar y pausar dispersión

---

## 📈 Roadmap de Implementación

### **Fase 1** (Priority 1 — Esta semana):
- ✅ Crear `mercury_client.py` con métodos base
- ✅ Crear `payment_processor.py` con orquestación
- ✅ Crear tablas: `provider_accounts`, `payout_requests`
- ✅ Crear endpoints básicos: GET /api/payments/balance

### **Fase 2** (Priority 2 — Próxima semana):
- ✅ Integrar KYC validation
- ✅ Crear endpoints: POST /api/payouts/create
- ✅ Webhook handlers para Mercury
- ✅ Admin dashboard (balance, pending payouts)

### **Fase 3** (Priority 3 — Dos semanas):
- ✅ Reconciliación automática Stripe ↔ Mercury
- ✅ Reportes de tesorería
- ✅ Tests exhaustivos
- ✅ Documentación de API

---

## 🎯 Preguntas a Resolver

1. **¿Mercury tiene SDK Python?** → Usar directo o HTTP client (requests)
2. **¿Aceptar solo ACH domésticos o también Wire internacionales?** → Ambos por ahora
3. **¿Cuál es la comisión típica que cobra Jeturing a proveedores?** → De invoice total o montomensual?
4. **¿Admin debe autorizar cada pago manualmente o automático?** → Por ahora: Manual + confirmar
5. **¿Enviar confirmación por email a proveedores?** → Sí, con detalles de pago

---

## 📚 Referencias

- **Mercury Banking**: https://mercury.com/docs
- **Stripe Connect**: https://stripe.com/docs/connect
- **ACH Transfers**: https://stripe.com/docs/payments/ach-debit
- **Bank Account Validation**: Plaid, Dwolla, Mercury native

