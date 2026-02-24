# 🏦 Sistema de Pagos y Dispersión — Guía de Uso

## 📌 Resumen Ejecutivo

Sistema completo para:
1. **Recibir** pagos de clientes (vía Stripe)
2. **Gestionar** fondos en Mercury Banking
3. **Dispersar** pagos a proveedores (ACH, Wire)
4. **Validar** cuentas bancarias (KYC)
5. **Reconciliar** saldos automáticamente

---

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

En `.env.production`:
```bash
# Mercury Banking
MERCURY_API_KEY=your_api_key_here
MERCURY_API_URL=https://api.mercury.com/api/v1
MERCURY_ACCOUNT_ID=your_account_id
MERCURY_WEBHOOK_SECRET=your_webhook_secret

# Stripe Connect (depósitos automáticos)
STRIPE_CONNECT_ACCOUNT_ID=acct_xxx
STRIPE_CONNECT_WEBHOOK_SECRET=whsec_xxx

# Configuración de pagos
PAYOUT_MIN_AMOUNT=5
PAYOUT_MAX_AMOUNT=50000
MERCURY_ACH_FEE=0
MERCURY_WIRE_FEE=15
MERCURY_DAILY_LIMIT=100000
MERCURY_BALANCE_THRESHOLD=5000
```

### 2. Verificar Balance Actual

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.sajet.us/api/payments/balance
```

Response:
```json
{
  "stripe": {
    "balance": 15000.00,
    "pending": 2500.00,
    "connected_accounts": 3
  },
  "mercury": {
    "balance": 25000.00,
    "available": 25000.00,
    "pending": 0,
    "account_name": "Jeturing Labs"
  },
  "total": 40000.00,
  "reserved": 5000.00,
  "available": 35000.00
}
```

---

## 💳 Flujo 1: Procesar Pago de Cliente

**Trigger**: Cliente paga invoice en Stripe

```bash
POST /api/payments/process-invoice
Content-Type: application/json
Authorization: Bearer $TOKEN

{
  "invoice_id": 123,
  "stripe_payment_intent_id": "pi_1MX9XK2eZvKYlo2Caq5L4gUL",
  "amount_received": 5000.00
}
```

**Response**:
```json
{
  "success": true,
  "invoice_id": 123,
  "amount": 5000.00,
  "status": "paid",
  "stripe_pi_id": "pi_1MX9XK2eZvKYlo2Caq5L4gUL",
  "next_action": "auto_sync_balance",
  "timestamp": "2026-02-24T15:30:00Z"
}
```

**Qué ocurre automáticamente**:
1. ✅ Invoice marcada como "paid"
2. ✅ Mercury balance sincronizado
3. ✅ Si hay proveedor asociado, se crea payout_request automáticamente
4. ✅ Email de confirmación al cliente

---

## 📤 Flujo 2: Crear y Ejecutar Payout

### Paso 1: Registrar Cuenta Bancaria del Proveedor

```bash
POST /api/providers/accounts
Content-Type: application/json
Authorization: Bearer $TOKEN

{
  "provider_id": 42,
  "account_holder_name": "Acme Corporation Inc.",
  "account_number": "123456789",
  "routing_number": "021000021",
  "account_type": "checking",
  "bank_name": "Wells Fargo"
}
```

**Response**:
```json
{
  "account_id": 456,
  "provider_id": 42,
  "account_number": "****6789",
  "bank_name": "Wells Fargo",
  "kyc_status": "pending",
  "message": "Account registered successfully. Awaiting KYC verification."
}
```

### Paso 2: Verificar Cuenta (Admin)

```bash
POST /api/providers/kyc-check?provider_id=42
Authorization: Bearer $TOKEN
```

**Response**:
```json
{
  "provider_id": 42,
  "kyc_status": "approved",
  "verified_at": "2026-02-24T15:30:00Z",
  "account_verified": true
}
```

### Paso 3: Crear Payout

```bash
POST /api/payouts/create
Content-Type: application/json
Authorization: Bearer $TOKEN

{
  "provider_id": 42,
  "invoice_id": 123,
  "gross_amount": 5000.00,
  "notes": "Comisión por venta de servicios — Feb 2026"
}
```

**Response**:
```json
{
  "payout_id": 123,
  "provider_id": 42,
  "gross_amount": 5000.00,
  "jeturing_commission": 750.00,
  "mercury_fee": 0,
  "net_amount": 4250.00,
  "status": "pending",
  "created_at": "2026-02-24T15:30:00Z"
}
```

### Paso 4: Autorizar Payout (Admin)

```bash
POST /api/payouts/123/authorize
Content-Type: application/json
Authorization: Bearer $TOKEN

{
  "approved": true,
  "notes": "Aprobado. Fondos disponibles. — Admin"
}
```

**Validaciones**:
- ✅ KYC del proveedor aprobado
- ✅ Balance en Mercury suficiente
- ✅ Límite diario no excedido
- ✅ Cuenta bancaria verificada

**Response**:
```json
{
  "authorized": true,
  "payout_id": 123,
  "status": "authorized",
  "authorized_at": "2026-02-24T12:00:00Z",
  "ready_to_execute": true
}
```

### Paso 5: Ejecutar Transferencia (Mercury)

```bash
POST /api/payouts/123/execute
Authorization: Bearer $TOKEN
```

**Response**:
```json
{
  "executed": true,
  "payout_id": 123,
  "mercury_transfer_id": "xfr_abc123",
  "status": "processing",
  "created_at": "2026-02-24T15:30:00Z"
}
```

**Qué ocurre**:
1. ✅ Mercury recibe instrucción de transferencia ACH
2. ✅ Fondos reservados en Mercury
3. ✅ Status actualizado a "processing"
4. ✅ Email enviado a proveedor con confirmación
5. ⏳ ~1-2 días hábiles: fondos llegan a cuenta proveedor
6. ✅ Webhook de Mercury confirma entrega

---

## 📊 Flujo 3: Dashboard de Tesorería

### Ver Resumen Ejecutivo

```bash
GET /api/treasury/summary
Authorization: Bearer $TOKEN
```

**Response**:
```json
{
  "balance": {
    "total": 40000.00,
    "stripe": 15000.00,
    "mercury": 25000.00
  },
  "payouts": {
    "pending_count": 3,
    "pending_amount": 6400.00,
    "total_paid_today": 4250.00
  },
  "alerts": {
    "critical": [],
    "warnings": [
      "3 payouts pending authorization"
    ]
  }
}
```

### Ver Payouts Pendientes

```bash
GET /api/payouts?status=pending&limit=50
Authorization: Bearer $TOKEN
```

**Response**:
```json
{
  "payouts": [
    {
      "id": 123,
      "provider": "Acme Corp",
      "amount": 4250.00,
      "status": "pending",
      "transfer_type": "ach",
      "requested_at": "2026-02-24T10:00:00Z",
      "authorized_at": null,
      "estimated_delivery": null
    },
    {
      "id": 124,
      "provider": "Tech Solutions",
      "amount": 2150.00,
      "status": "authorized",
      "transfer_type": "ach",
      "requested_at": "2026-02-24T14:00:00Z",
      "authorized_at": "2026-02-24T16:00:00Z",
      "estimated_delivery": "2026-02-26T00:00:00Z"
    }
  ],
  "total": 15,
  "limit": 50,
  "offset": 0
}
```

### Ver Cash Flow (30 días)

```bash
GET /api/payments/summary?days=30
Authorization: Bearer $TOKEN
```

**Response**:
```json
{
  "period": {
    "start": "2026-01-23T00:00:00Z",
    "end": "2026-02-24T23:59:59Z"
  },
  "inflows": {
    "total": 50000.00,
    "from_customers": 50000.00,
    "from_interest": 0,
    "transactions_count": 12
  },
  "outflows": {
    "total": 12000.00,
    "to_providers": 10000.00,
    "bank_fees": 500.00,
    "other": 1500.00,
    "transactions_count": 8
  },
  "net": 38000.00,
  "balance": {
    "opening": 25000.00,
    "closing": 63000.00
  }
}
```

### Forecasting (Próximos 7 días)

```bash
GET /api/treasury/forecast?days=7
Authorization: Bearer $TOKEN
```

**Response**:
```json
{
  "forecast_period": {
    "start": "2026-02-24T00:00:00Z",
    "end": "2026-03-03T23:59:59Z",
    "days": 7
  },
  "projected_inflows": 0,
  "projected_outflows": 15000.00,
  "projected_balance": 25000.00,
  "buffer": 10000.00,
  "recommendation": "proceed",
  "timeline": [
    {
      "date": "2026-02-26",
      "payout_count": 3,
      "payout_total": 10000.00,
      "balance_after": 15000.00
    }
  ]
}
```

### Alertas de Tesorería

```bash
GET /api/treasury/alerts
Authorization: Bearer $TOKEN
```

**Response**:
```json
{
  "critical": [],
  "warnings": [
    "3 payouts pending authorization",
    "Daily payout limit 75% utilized"
  ],
  "info": [
    "Weekly settlement due Feb 28"
  ]
}
```

---

## 🔄 Reconciliación Automática

Sistema verifica automáticamente cada 1 hora:

```
Stripe Balance ↔ Mercury Balance
```

Si hay discrepancia > 0.1%, se genera alerta:

```bash
GET /api/treasury/alerts
```

Response con warning:
```json
{
  "warnings": [
    "⚠️ Discrepancy: Stripe $25000.50 vs Mercury $24999.50 (0.002%)"
  ]
}
```

---

## 🔐 Seguridad & Cumplimiento

### PCI Compliance
- ✅ Números de cuenta encriptados en BD
- ✅ Tokens de Stripe (no guardar números de tarjeta)
- ✅ Acceso solo para roles autorizados

### Webhook Validation
```python
# Mercury valida firma HMAC-SHA256
if not mercury_client.verify_webhook_signature(payload, signature):
    return 401 Unauthorized
```

### Auditoría
Todos los movimientos registran:
- ✅ Quién (user ID)
- ✅ Cuándo (timestamp)
- ✅ Qué (acción + monto)
- ✅ Resultado (success/error)

### Rate Limiting
- Maximum 1 request/segundo a Mercury API
- Máximo 100 transfers/día
- Máximo $100K/día en dispersión

---

## ❌ Manejo de Errores

### Payout Rechazado

```bash
POST /api/payouts/123/authorize
{
  "approved": false,
  "notes": "Cuenta no verificada aún"
}
```

Response:
```json
{
  "authorized": false,
  "payout_id": 123,
  "status": "rejected",
  "reason": "Cuenta no verificada aún"
}
```

### Balance Insuficiente

```bash
POST /api/payouts/124/execute
```

Response:
```json
{
  "executed": false,
  "error": "Mercury balance $2000 insufficient for $4250 payout"
}
```

### Transferencia Fallida

```bash
GET /api/payouts/123
```

Response:
```json
{
  "id": 123,
  "status": "failed",
  "failure_reason": "Invalid routing number",
  "mercury_transfer_id": "xfr_failed_123"
}
```

---

## 📱 Webhooks Mercury

Endpoint para recibir notificaciones:
```
POST https://api.sajet.us/api/webhooks/mercury
```

Tipos de eventos:
- `transfer.pending` → Transferencia creada
- `transfer.posted` → Fondos llegaron
- `transfer.failed` → Transferencia rechazada
- `account.low_balance` → Saldo bajo

**Ejemplo**:
```json
{
  "event_type": "transfer.posted",
  "transfer_id": "xfr_abc123",
  "amount": 4250.00,
  "status": "posted",
  "posted_at": "2026-02-26T12:00:00Z"
}
```

Sistema actualiza automáticamente:
1. ✅ payout_request.status = "completed"
2. ✅ provider invoice actualizada
3. ✅ settlement reconciliado
4. ✅ Email de confirmación enviado

---

## 🧮 Ejemplo Completo: De Cliente a Proveedor

### 1️⃣ Cliente paga $5000

```bash
POST /api/payments/process-invoice
{
  "invoice_id": 100,
  "stripe_payment_intent_id": "pi_xxx",
  "amount_received": 5000.00
}
```

Result: Invoice = PAID, Mercury recibe fondos

---

### 2️⃣ Sistema calcula comisión (15%)

```
Gross:              $5000.00
Jeturing (15%):     -$750.00
Mercury Fee (ACH):  -$0
Net (Proveedor):    $4250.00
```

Payout creado automáticamente → Status: PENDING

---

### 3️⃣ Admin autoriza

```bash
POST /api/payouts/123/authorize
{ "approved": true }
```

Status: AUTHORIZED

---

### 4️⃣ Sistema ejecuta (Mercury)

```bash
POST /api/payouts/123/execute
```

Mercury recibe: `transfer_out("ACH", $4250, account_123)`

Status: PROCESSING

---

### 5️⃣ Proveedor recibe (1-2 días hábiles)

Mercury webhook confirma → Status: COMPLETED

Proveedor recibe $4250 en su cuenta

---

## 📚 API Reference Completa

Ver documentación completa:
```
GET https://api.sajet.us/sajet-api-docs
```

---

## 🎯 Próximos Pasos

- [ ] Integrar con contabilidad (asientos en Odoo)
- [ ] Dashboard web para visualizar payouts
- [ ] Reportes automáticos para contadores
- [ ] Integración con Tesoro (tesorería avanzada)
- [ ] Alertas por SMS/email en tiempo real

---

## ❓ FAQ

**P: ¿Cuánto tarda un ACH?**
R: 1-2 días hábiles. Wire tarda 1 día pero cuesta $15.

**P: ¿Qué sucede si falla el transfer?**
R: Mercury reinenta automáticamente. Admin recibe alerta. Status = FAILED después de 3 intentos.

**P: ¿Se puede anular un payout?**
R: Sí, antes de ejecutar. Si ya está "processing", contactar a Mercury.

**P: ¿Cómo validar cuenta bancaria?**
R: Sistema verifica formato + routing number. Mercury puede hacer micro-depósitos (2-3 días) para verificación adicional.

**P: ¿Dónde veo el historial de pagos a un proveedor?**
R: `GET /api/treasury/transactions?provider_id=42`

