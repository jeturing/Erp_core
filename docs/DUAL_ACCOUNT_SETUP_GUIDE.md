"""
DUAL ACCOUNT SETUP GUIDE
Guía de Configuración e Implementación de Arquitectura Dual Mercury

Documento: DUAL_ACCOUNT_SETUP_GUIDE.md
Fecha: 2026-02-24
Versión: 1.0
"""

# 📋 Guía de Configuración: Sistema Dual de Cuentas Mercury

## 🎯 Objetivo

Implementar un sistema **seguro y controlado** con:
- **SAVINGS Account**: Acumula fondos de clientes (reserva intocable)
- **CHECKING Account**: Dispersa a proveedores (operativa automática)

---

## 📝 Paso 1: Crear Dos Cuentas en Mercury

### 1.1 Crear SAVINGS Account (Ahorros)

1. Login a Mercury: https://app.mercury.com
2. Click "New Account"
3. Nombre: "Jeturing Savings - Reserve"
4. Tipo: Business Savings Account
5. Conectar Stripe (para depósitos automáticos)
6. Copiar:
   - Account ID (ej: `acc_1234567890_savings`)
   - API Key (ej: `sk_live_1234567890_savings`)

### 1.2 Crear CHECKING Account (Transaccional)

1. Click "New Account" nuevamente
2. Nombre: "Jeturing Checking - Payouts"
3. Tipo: Business Checking Account
4. NO conectar Stripe (solo recibe de SAVINGS)
5. Copiar:
   - Account ID (ej: `acc_1234567890_checking`)
   - API Key (ej: `sk_live_1234567890_checking`)

### 1.3 Obtener Webhook Secret

1. Settings → Webhooks
2. Copy: Webhook Secret (ej: `whsec_1234567890`)

---

## 🔧 Paso 2: Actualizar .env.production

Agregar estas variables:

```bash
# ═══════════════════════════════════════════════════════════════
# MERCURY DUAL ACCOUNT CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Account 1: SAVINGS (Ahorros - Reserva de clientes)
MERCURY_SAVINGS_ACCOUNT_ID=acc_1234567890_savings
MERCURY_SAVINGS_API_KEY=sk_live_1234567890_savings

# Account 2: CHECKING (Transaccional - Dispersión a proveedores)
MERCURY_CHECKING_ACCOUNT_ID=acc_1234567890_checking
MERCURY_CHECKING_API_KEY=sk_live_1234567890_checking

# API Configuration
MERCURY_API_URL=https://api.mercury.com/api/v1
MERCURY_WEBHOOK_SECRET=whsec_1234567890

# Transfer Configuration (Savings → Checking)
MERCURY_MIN_TRANSFER_TO_CHECKING=1000          # Mínimo a transferir
MERCURY_MAX_TRANSFER_TO_CHECKING=100000        # Máximo por transferencia
MERCURY_CHECKING_MIN_BALANCE=5000              # Threshold para auto-replenish
MERCURY_DAILY_LIMIT=100000                     # Límite diario de dispersión

# Existing Mercury Configuration (si había)
MERCURY_ACH_FEE=0                              # ACH es gratis
MERCURY_WIRE_FEE=15                            # Wire cuesta $15
```

---

## ✅ Paso 3: Verificar Instalación

### 3.1 Probar Importación del Módulo

```python
# En una sesión Python
from app.services.mercury_account_manager import get_account_manager

manager = get_account_manager()
print(f"SAVINGS Account: {manager.savings_account_id}")
print(f"CHECKING Account: {manager.checking_account_id}")
```

Expected output:
```
SAVINGS Account: acc_1234567890_savings
CHECKING Account: acc_1234567890_checking
```

### 3.2 Probar Obtener Balances

```python
balances = manager.get_both_balances()
print(balances)
```

Expected output:
```json
{
  "savings": {
    "balance": 150000.00,
    "available": 150000.00,
    ...
  },
  "checking": {
    "balance": 50000.00,
    "available": 50000.00,
    ...
  },
  "total": 200000.00
}
```

### 3.3 Probar Health Check

```python
health = manager.get_account_health()
print(health)
```

Expected output:
```json
{
  "status": "healthy",
  "savings": {
    "balance": 150000,
    "status": "ok"
  },
  "checking": {
    "balance": 50000,
    "status": "ok",
    "needs_replenishment": false
  },
  "alerts": []
}
```

---

## 🚀 Paso 4: Usar los API Endpoints

### 4.1 Ver Estado de Cuentas

```bash
curl -X GET "http://localhost:8000/api/treasury/accounts/dual-status" \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "status": "healthy",
  "accounts": {
    "savings": {
      "account_type": "savings",
      "balance": 150000.00,
      "available": 150000.00,
      "purpose": "Reserve for customer funds"
    },
    "checking": {
      "account_type": "checking",
      "balance": 50000.00,
      "available": 50000.00,
      "purpose": "Operational for provider payouts"
    }
  },
  "totals": {
    "total_balance": 200000.00,
    "total_available": 200000.00
  },
  "health": {
    "status": "healthy",
    "alerts": []
  }
}
```

### 4.2 Transferir Manualmente SAVINGS → CHECKING

```bash
curl -X POST "http://localhost:8000/api/treasury/accounts/transfer-to-checking" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 25000,
    "reason": "Replenishing for Q1 provider payouts"
  }'
```

Response:
```json
{
  "success": true,
  "transfer": {
    "transfer_id": "xfr_abc123def456",
    "from_account": "savings",
    "to_account": "checking",
    "amount": 25000.00,
    "status": "pending",
    "created_at": "2026-02-24T10:30:00Z",
    "expected_delivery": "2026-02-26T00:00:00Z",
    "reason": "Replenishing for Q1 provider payouts"
  }
}
```

### 4.3 Forzar Auto-Replenish

```bash
curl -X POST "http://localhost:8000/api/treasury/accounts/auto-replenish" \
  -H "Content-Type: application/json" \
  -d '{
    "target_balance": 30000
  }'
```

Response (si fue necesario):
```json
{
  "success": true,
  "replenished": true,
  "transfer": {
    "transfer_id": "xfr_xyz789",
    "amount": 26000.00,
    "status": "pending",
    "reason": "Auto-replenishment"
  }
}
```

Response (si NO fue necesario):
```json
{
  "success": true,
  "replenished": false,
  "transfer": null
}
```

---

## 💰 Flujo Completo: Cliente → Proveedor

### Escenario: Cliente paga $5,000 a Jeturing

#### **Día 1: Cliente Paga**
```
1. Cliente paga via Stripe: $5,000
2. Stripe webhook: payment_intent.succeeded
3. Sistema: Marca invoice como PAID
4. Mercury SAVINGS recibe depósito automático: $5,000
```

#### **Sistema Detecta: Auto-replenish Necesario**
```
1. CHECKING balance: $3,500 (debajo de $5,000 mínimo)
2. Sistema automáticamente detecta: CHECKING < mínimo
3. Transfer creado: SAVINGS → CHECKING: $24,000
   - Ahora CHECKING: $27,500
   - Ahora SAVINGS: $130,000
```

#### **Admin Autoriza Payout a Proveedor**
```
1. Admin ve en dashboard: "Pending payout: $4,250 to Acme Corp"
2. Admin click: [AUTHORIZE]
3. Sistema valida:
   - KYC del proveedor: ✅ APPROVED
   - CHECKING balance: $27,500 >= $4,250 ✅
   - Límite diario: $95,750 disponible de $100,000 ✅
4. Status → AUTHORIZED
```

#### **Día 2: Sistema Dispersa**
```
1. Sistema crea ACH Transfer desde CHECKING:
   - Monto: $4,250
   - Destinatario: Acme Corp bank account
   - Tipo: ACH (gratis, 1-2 días)
   - Transfer ID: xfr_prov123
2. Status → PROCESSING
```

#### **Día 3-4: Fondos Llegan al Proveedor**
```
1. Mercury webhook: transfer.completed
2. Sistema marca payout: COMPLETED
3. Proveedor recibe: $4,250 en su cuenta bancaria
4. Email confirmación enviado al proveedor
```

#### **Estado Final de Cuentas**
```
SAVINGS:     $130,000 (menos lo que se transfirió)
CHECKING:    $23,250 (menos lo que se pagó: $27,500 - $4,250)
TOTAL:       $153,250
```

---

## 🔍 Monitoreo y Alertas

### Health Status Possible Values

```
"status": "healthy"     → Todo OK, no hay alertas
"status": "warning"     → CHECKING está bajo mínimo, o SAVINGS está bajo
"status": "critical"    → CHECKING está muy bajo (<$1,000) o balance muy bajo
```

### Auto-Replenish Logic

El sistema automáticamente repone CHECKING si:

```python
IF CHECKING.balance < MERCURY_CHECKING_MIN_BALANCE:
    TRANSFER = min(
        SAVINGS.balance - 5000,  # Dejar mínimo en SAVINGS
        MERCURY_MAX_TRANSFER_TO_CHECKING
    )
    TRANSFER_TO_CHECKING(TRANSFER)
```

**Ejemplo**:
- SAVINGS: $100,000
- CHECKING: $3,000 (menos de $5,000 mínimo)
- Target: $10,000 (2x mínimo)
- Transfer: $7,000 (para llegar a $10,000)
- Resultado:
  - SAVINGS: $93,000
  - CHECKING: $10,000

---

## 🔐 Seguridad & Límites

### Límites Configurables

```bash
MERCURY_MIN_TRANSFER_TO_CHECKING=1000           # Mínimo a transferir
MERCURY_MAX_TRANSFER_TO_CHECKING=100000         # Máximo por transferencia
MERCURY_CHECKING_MIN_BALANCE=5000               # Threshold para replenish
MERCURY_DAILY_LIMIT=100000                      # Límite diario total
```

### Validaciones en Cada Payout

✅ **Antes de autorizar**:
- [ ] KYC del proveedor aprobado
- [ ] Cuenta bancaria verificada
- [ ] Balance en CHECKING suficiente
- [ ] Límite diario no excedido

✅ **Antes de ejecutar**:
- [ ] Auto-replenish CHECKING si es necesario
- [ ] Validar balance una última vez
- [ ] Crear idempotency key para evitar duplicados

✅ **Después de ejecutar**:
- [ ] Guardar transfer ID de Mercury
- [ ] Log evento en base de datos
- [ ] Monitorear status vía webhook

---

## 📊 Dashboard Queries

### Query 1: Ver dinero en cada cuenta

```bash
curl "http://localhost:8000/api/treasury/accounts/dual-status" | jq '.accounts'
```

Output:
```json
{
  "savings": {
    "balance": 150000.00
  },
  "checking": {
    "balance": 50000.00
  }
}
```

### Query 2: Ver alertas activas

```bash
curl "http://localhost:8000/api/treasury/accounts/dual-status" | jq '.health.alerts'
```

Output:
```json
[
  "CHECKING balance below minimum: $3500 (minimum: $5000)"
]
```

### Query 3: Forzar verificación de salud

```bash
curl "http://localhost:8000/api/treasury/accounts/dual-status" | jq '.health.status'
```

Output:
```
"warning"
```

---

## 🧪 Test Scenarios

### Scenario 1: Normal Flow

**Setup**:
- SAVINGS: $100,000
- CHECKING: $50,000

**Actions**:
1. Crear payout: $4,250 para Acme Corp
2. Autorizar payout
3. Ejecutar payout

**Expected**:
- CHECKING balance: $45,750 (menos payout)
- Status: COMPLETED después de 1-2 días

### Scenario 2: Auto-Replenish Triggered

**Setup**:
- SAVINGS: $100,000
- CHECKING: $3,000 (menos de $5,000 mínimo)

**Actions**:
1. Sistema detecta auto-replenish necesario
2. Transfer de $25,000 de SAVINGS → CHECKING
3. Luego crear payout: $4,250

**Expected**:
- CHECKING: $23,750 (25,000 + 3,000 - 4,250)
- SAVINGS: $75,000
- Payout status: COMPLETED

### Scenario 3: Insufficient CHECKING Balance

**Setup**:
- SAVINGS: $2,000 (muy bajo!)
- CHECKING: $1,000

**Actions**:
1. Intentar crear payout: $5,000
2. Sistema intenta auto-replenish
3. SAVINGS no tiene suficiente

**Expected**:
- Error: "Insufficient balance in SAVINGS"
- Status: CRITICAL alert
- Admin debe transferir fondos manualmente o depositar más

---

## 🆘 Troubleshooting

### Error: "SAVINGS client not configured"

**Solución**:
1. Verificar `.env.production` tiene `MERCURY_SAVINGS_ACCOUNT_ID` y `MERCURY_SAVINGS_API_KEY`
2. Verificar valores NO están vacíos
3. Reiniciar aplicación: `systemctl restart erp-core`

### Error: "Insufficient balance in SAVINGS"

**Solución**:
1. Depositar fondos en SAVINGS vía Stripe
2. O transferir de otra cuenta bancaria
3. Esperar depósito (típicamente 1-2 días)

### Error: "Auto-replenish failed"

**Solución**:
1. Verificar SAVINGS tiene balance >= transfer amount
2. Verificar no hay rate limiting (máx 1 req/seg)
3. Checkear Mercury API status: https://status.mercury.com

### Balance discrepancy between Stripe and Mercury

**Solución**:
1. Ejecutar reconciliación manual: `POST /api/treasury/reconcile`
2. Si discrepancia > 1%, contactar Mercury support
3. Verificar webhooks están llegando correctamente

---

## 📈 Roadmap Próximas Fases

### Fase 2 (Esta semana)
- [ ] Database migrations: `provider_accounts`, `payout_requests`
- [ ] Update models: `Provider.kyc_status`, `Invoice.stripe_pi_id`
- [ ] Binding payment_processor a BD

### Fase 3 (Próxima semana)
- [ ] Webhook handlers para Mercury events
- [ ] Webhook handlers para Stripe events
- [ ] Dashboard UI para gestionar transfers

### Fase 4 (Dos semanas)
- [ ] Automated reporting y auditoría
- [ ] Scheduled reconciliations
- [ ] Email alerts para balance bajo

---

## 📞 Support

Para problemas o preguntas:
1. Check this guide first
2. Review MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md
3. Contact: tech@jeturing.com

---

**Next Steps**: 
1. ✅ Crear dos cuentas en Mercury
2. ✅ Configurar .env.production
3. ✅ Probar endpoints
4. 🔄 Ir a Phase 2: Database migrations
