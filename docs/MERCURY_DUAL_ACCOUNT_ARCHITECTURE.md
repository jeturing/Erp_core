"""
Arquitectura de Dos Cuentas Mercury
Sistema Separado de Ahorros y Dispersión

Documento: MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md
Fecha: 2026-02-24
Versión: 1.0
"""

# 🏦 Arquitectura de Dos Cuentas Mercury para Jeturing

## 📌 Resumen Ejecutivo

Implementamos un sistema de **dos cuentas Mercury completamente separadas** para mayor control y seguridad:

1. **CUENTA SAVINGS (Ahorros)**
   - Propósito: Acumular fondos de clientes (Stripe deposits)
   - Balance inicial: ~$150,000 (reserva)
   - Transferencias: Recibe depósitos, envía a CHECKING bajo demanda
   - Seguridad: Restringida, sin dispersión directa

2. **CUENTA CHECKING (Transaccional)**
   - Propósito: Dispersar a proveedores (ACH/Wire)
   - Balance operativo: Mantiene ~$50,000 para pagos diarios
   - Transferencias: Recibe de SAVINGS, envía a proveedores
   - Automatización: Pueden ser automáticas dentro de límites

---

## 🔄 Flujo de Dinero — Dos Cuentas

```
┌──────────────────────────────────────────────────────────────┐
│                       CLIENTE                                 │
│            (Paga invoice vía Stripe)                          │
└────────────────────────────┬─────────────────────────────────┘
                             │ $5,000
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                        STRIPE                                 │
│                                                                │
└────────────────────────────┬─────────────────────────────────┘
                             │ Depósito automático
                             ▼
        ┌─────────────────────────────────────┐
        │   MERCURY SAVINGS ACCOUNT            │
        │   (Reserva de Fondos)               │
        │                                      │
        │   Balance: $150,000                 │
        │   Función: Acumular                 │
        │   Clave: Restringida, sin payout    │
        └─────────────────┬────────────────────┘
                          │
                          │ Transfer: $25,000
                          │ (cuando CHECKING < min)
                          ▼
        ┌─────────────────────────────────────┐
        │   MERCURY CHECKING ACCOUNT           │
        │   (Dispersión Operativa)            │
        │                                      │
        │   Balance: $50,000                  │
        │   Función: Pagar proveedores       │
        │   Clave: Operativo, con payout      │
        └─────────────────┬────────────────────┘
                          │
                          │ ACH: $4,250 (gratis)
                          │ Wire: $5,000 (-$15 fee)
                          ▼
        ┌─────────────────────────────────────┐
        │        PROVEEDORES                   │
        │     (Beneficiarios Finales)         │
        │                                      │
        │   - Provider A: $4,250 (ACH)        │
        │   - Provider B: $4,985 (Wire)       │
        │   - Provider C: $9,500 (ACH)        │
        └─────────────────────────────────────┘
```

---

## 🛠️ Componentes Implementados

### 1. **mercury_account_manager.py** (500 líneas)

Nuevo servicio que maneja **ambas cuentas simultáneamente**:

```python
manager = MercuryAccountManager()

# Obtener balances de ambas cuentas
manager.get_both_balances()
# Retorna:
# {
#   "savings": {"balance": 150000, ...},
#   "checking": {"balance": 45000, ...},
#   "total": 195000
# }

# Transferir de SAVINGS → CHECKING
manager.transfer_to_checking(amount=25000, reason="Replenishment")
# Retorna: transfer_id, status, etc.

# Auto-replenish (si CHECKING cae bajo mínimo)
manager.auto_replenish_checking()

# Crear payout a proveedor (desde CHECKING)
manager.create_provider_payout(
    amount=4250,
    provider_name="Acme Corp",
    beneficiary=BankAccount(...),
    transfer_type="ach"  # o "wire"
)

# Monitorear salud de cuentas
manager.get_account_health()
# Retorna:
# {
#   "status": "healthy" | "warning" | "critical",
#   "alerts": [...],
#   "savings": {...},
#   "checking": {...}
# }
```

**Métodos Principales**:
| Método | Propósito | Desde | Hacia |
|--------|----------|-------|-------|
| `get_both_balances()` | Ver ambos balances en tiempo real | - | - |
| `transfer_to_checking()` | Mover fondos | SAVINGS | CHECKING |
| `auto_replenish_checking()` | Reponer automáticamente | SAVINGS | CHECKING |
| `create_provider_payout()` | Pagar a proveedor | CHECKING | Proveedor |
| `get_account_health()` | Estado general + alertas | - | - |

---

## 🔐 Configuración Requerida (.env.production)

Agregar las siguientes variables de entorno:

```bash
# ═══════════════════════════════════════════════════════════════
# MERCURY DUAL ACCOUNT SETUP
# ═══════════════════════════════════════════════════════════════

# ACCOUNT 1: SAVINGS (Ahorros)
MERCURY_SAVINGS_ACCOUNT_ID=acc_xxxxxxxxxxxx_savings
MERCURY_SAVINGS_API_KEY=sk_live_xxxxxxxxxxxx_savings

# ACCOUNT 2: CHECKING (Transaccional)
MERCURY_CHECKING_ACCOUNT_ID=acc_xxxxxxxxxxxx_checking
MERCURY_CHECKING_API_KEY=sk_live_xxxxxxxxxxxx_checking

# API Endpoint
MERCURY_API_URL=https://api.mercury.com/api/v1

# Transfer Limits (Savings → Checking)
MERCURY_MIN_TRANSFER_TO_CHECKING=1000
MERCURY_MAX_TRANSFER_TO_CHECKING=100000

# Minimum balance in CHECKING before auto-replenish triggers
MERCURY_CHECKING_MIN_BALANCE=5000

# Webhook Secret (para Mercury webhooks)
MERCURY_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxx
```

---

## 📊 Flujo Detallado: Cliente → Proveedor (Con Dos Cuentas)

### **Paso 1: Cliente Paga (Stripe)**
```
Cliente: "Pago invoice por $5,000"
  ↓
Stripe: Procesa pago
  ↓
Webhook: payment_intent.succeeded
  ↓
Sistema: Marca invoice como PAID
  ↓
Mercury SAVINGS: Recibe depósito $5,000 (balance = $155,000)
```

### **Paso 2: Sistema Calcula Comisión**
```
Sistema: 
  - Invoice total: $5,000
  - Jeturing commission: 15% = $750
  - Mercury ACH fee: $0
  - Net to provider: $4,250
  
  Payout creado:
  - Status: PENDING
  - Destino: Provider Account
```

### **Paso 3: Admin Autoriza Pago**
```
Admin Dashboard:
  - Ve: "Pending payout: $4,250 to Acme Corp"
  - Click: [AUTHORIZE]
  
Sistema:
  - Valida KYC proveedor ✓
  - Verifica balance CHECKING: $50,000 ✓
  - Verifica límite diario: OK ✓
  - Status → AUTHORIZED
```

### **Paso 4: Sistema Dispersa (Automáticamente)**
```
Si CHECKING balance < CHECKING_MIN_BALANCE:
  Transfer de SAVINGS → CHECKING: $25,000
  (Ahora CHECKING = $75,000)

Luego:
  ACH Transfer CHECKING → Provider:
    - Monto: $4,250
    - Tipo: ACH (gratis, 1-2 días)
    - Status: PENDING
    - Transfer ID: xfr_abc123...
```

### **Paso 5: Provider Recibe Fondos**
```
Día 1: Transfer posted
  - Status: COMPLETED
  - Payout request: COMPLETED
  
Día 2: Fondos en cuenta del proveedor
  - Provider ve $4,250 depositados
  - Confirmación email enviada
```

### **Resultado Final**:
```
SAVINGS:    $155,000 - $25,000 = $130,000 (menos lo transferido)
CHECKING:   $50,000 + $25,000 - $4,250 = $70,750 (menos lo pagado)
TOTAL:      $200,750 (menos comisión $750)
```

---

## 🚀 Ventajas de Arquitectura Dual

### ✅ **Seguridad**
- SAVINGS es **restringida**: sin payouts directos, sin cambios de datos
- CHECKING es **operativa**: solo dispersión, sin modificación de clientes

### ✅ **Control**
- Admin decide **cuándo y cuánto** transferir de SAVINGS → CHECKING
- Previene dispersión accidental de toda la reserva
- Manual oversight para cada inter-account transfer

### ✅ **Claridad Financiera**
- Balance de SAVINGS = Reserva de clientes (intocable sin decisión)
- Balance de CHECKING = Fondos operacionales disponibles

### ✅ **Automatización Segura**
- Auto-replenish de CHECKING es automático (dentro de límites)
- Pero SAVINGS nunca se gasta directamente en dispersión
- Auditoría clara de todas las transferencias

### ✅ **Reconciliación**
- Cada movimiento entre cuentas está registrado
- Fácil auditar: SAVINGS deposits = clientes; CHECKING outflows = proveedores

---

## 📈 Ejemplos de Uso

### Ejemplo 1: Check Daily Account Health

```python
from app.services.mercury_account_manager import get_account_manager

manager = get_account_manager()

# Cada mañana, verificar estado
health = manager.get_account_health()

print(f"Status: {health['status']}")
# Output: "Status: healthy"

print(f"Alerts: {health['alerts']}")
# Output: "Alerts: []"

print(f"Savings: ${health['savings']['balance']}")
print(f"Checking: ${health['checking']['balance']}")
# Output:
# Savings: $150000
# Checking: $52000
```

### Ejemplo 2: Admin Transfers Funds

```python
# Admin via dashboard: "Transfer $50,000 from SAVINGS to CHECKING"
manager = get_account_manager()

result = manager.transfer_to_checking(
    amount=50000,
    reason="Preparing for Q1 provider payouts"
)

print(result)
# {
#   "transfer_id": "xfr_abc123",
#   "from_account": "savings",
#   "to_account": "checking",
#   "amount": 50000,
#   "status": "pending",
#   "created_at": "2026-02-24T10:30:00Z",
#   "expected_delivery": "2026-02-26T00:00:00Z"
# }
```

### Ejemplo 3: Auto-Replenish Triggered

```python
# CHECKING falls below $5,000
# Sistema detecta automáticamente

result = manager.auto_replenish_checking(target_balance=25000)

# Si fue necesario:
# {
#   "transfer_id": "xfr_xyz789",
#   "amount": 23000,  # (25000 - 2000 actual)
#   "status": "pending",
#   "reason": "Auto-replenishment"
# }

# Si no fue necesario:
# None (no transfer creado)
```

### Ejemplo 4: Create Provider Payout

```python
# Dispersar a proveedor desde CHECKING
beneficiary = BankAccount(
    account_number="123456789",
    routing_number="987654321",
    account_holder="Acme Corp",
    account_type="checking",
    bank_name="Wells Fargo"
)

payout = manager.create_provider_payout(
    amount=4250,
    provider_name="Acme Corp",
    beneficiary=beneficiary,
    transfer_type="ach",
    invoice_ref="INV-12345"
)

print(f"Payout created: {payout['transfer_id']}")
# Output: Payout created: xfr_prov123
```

---

## 🔄 Integración con payment_processor.py

El `payment_processor.py` debe actualizarse para usar el nuevo `mercury_account_manager`:

### Antes (Single Account):
```python
from app.services.mercury_client import get_mercury_client

def execute_payout(payout_request):
    client = get_mercury_client()
    # Transferir directamente desde cuenta única
    return client.create_ach_transfer(...)
```

### Después (Dual Account):
```python
from app.services.mercury_account_manager import get_account_manager

def execute_payout(payout_request):
    manager = get_account_manager()
    
    # Verificar y reponer CHECKING si es necesario
    manager.auto_replenish_checking()
    
    # Luego dispersar desde CHECKING
    return manager.create_provider_payout(...)
```

---

## 📋 Checklist de Implementación

- [ ] Crear dos cuentas en Mercury (SAVINGS + CHECKING)
  - [ ] Account 1: Business savings account
  - [ ] Account 2: Business checking account
  
- [ ] Obtener credenciales de Mercury
  - [ ] API Key para SAVINGS account
  - [ ] Account ID para SAVINGS account
  - [ ] API Key para CHECKING account
  - [ ] Account ID para CHECKING account
  - [ ] Webhook secret
  
- [ ] Configurar .env.production con nuevas variables
  - [ ] MERCURY_SAVINGS_ACCOUNT_ID
  - [ ] MERCURY_SAVINGS_API_KEY
  - [ ] MERCURY_CHECKING_ACCOUNT_ID
  - [ ] MERCURY_CHECKING_API_KEY
  - [ ] Transfer limits y thresholds
  
- [ ] Actualizar payment_processor.py
  - [ ] Cambiar imports de mercury_client a mercury_account_manager
  - [ ] Actualizar execute_payout() para usar manager
  - [ ] Agregar auto-replenish lógica
  
- [ ] Crear endpoints dashboard para gestionar cuentas
  - [ ] GET /api/treasury/accounts/dual-status
  - [ ] POST /api/treasury/accounts/transfer
  
- [ ] Tests
  - [ ] Test auto-replenish trigger
  - [ ] Test insufficient CHECKING balance
  - [ ] Test provider payout flow
  - [ ] Test inter-account transfer limits
  
- [ ] Documentación operativa
  - [ ] Procedures para transfers manuales
  - [ ] Alertas y monitoring
  - [ ] Troubleshooting

---

## ⚠️ Consideraciones de Seguridad

### **SAVINGS Account Restrictions**:
1. ✅ Recibe depósitos (Stripe)
2. ✅ Envía a CHECKING (bajo demanda del admin)
3. ❌ No puede enviar directamente a proveedores
4. ❌ No puede modificarse sin auditoría

### **CHECKING Account Permissions**:
1. ✅ Recibe de SAVINGS
2. ✅ Envía a proveedores (ACH/Wire)
3. ✅ Puede ser automático dentro de límites diarios
4. ⚠️ Requiere KYC del proveedor

### **Rate Limiting**:
- Máximo 1 transfer/segundo a Mercury API
- Máximo $100,000 de dispersión/día desde CHECKING
- Máximo $100,000 de transfer de SAVINGS→CHECKING/día

### **Auditoría**:
- Registrar TODAS las transacciones inter-cuenta
- Registrar TODAS las dispersiones (con invoice ref)
- Enviar emails a admin para transfers > $25,000

---

## 🔄 Roadmap

### **Fase 1** (Esta semana) ✅
- [x] Crear mercury_account_manager.py
- [x] Implementar dual account logic
- [x] Crear auto-replenish sistema
- [x] Documentar arquitectura

### **Fase 2** (Próxima semana)
- [ ] Actualizar payment_processor.py
- [ ] Crear endpoints de treasury dashboard
- [ ] Agregar alertas en get_account_health()
- [ ] Tests unitarios

### **Fase 3** (Dos semanas)
- [ ] Integración con webhook handlers
- [ ] Dashboard UI para gestionar transfers
- [ ] Reportes de auditoría
- [ ] Monitoreo en tiempo real

---

## 🎯 Conclusión

La arquitectura de **dos cuentas Mercury separadas** proporciona:
- ✅ **Seguridad**: Separación clara de ahorros y operativa
- ✅ **Control**: Admin visibility sobre inter-account transfers
- ✅ **Claridad**: Balance de SAVINGS = reserva de clientes
- ✅ **Automatización**: CHECKING se repone automáticamente

Sin los riesgos de:
- ❌ Dispersión accidental de la reserva completa
- ❌ Pérdida de visibilidad sobre dónde está cada peso
- ❌ Cambios de datos en SAVINGS (donde están los ahorros)

---

**Siguiente Paso**: Obtener las credenciales de Mercury para ambas cuentas y actualizar `.env.production`.
