"""
MERCURY CHECKING ACCOUNT CONFIGURATION
Configuración de Cuenta Transaccional "Provedores-Sajet"

Documento: MERCURY_CHECKING_CONFIGURED.md
Fecha: 2026-02-24
Versión: 1.0
"""

# ✅ Cuenta Mercury CHECKING Configurada: Provedores-Sajet

## 📋 Datos de la Cuenta

### Account Details
```
Nombre:              Provedores-Sajet (Transaccional)
Tipo:                Checking Account
Banco:               Choice Financial Group
Dirección:           4501 23rd Avenue S, Fargo, ND 58104

Account Number:      202369307283
Routing Number:      091311229
Account Type:        Checking
```

### Balance Actual
```
Available Balance:   $1,068.46
Type:                Current
Pending:             -$488.70
```

---

## 🔧 Configuración en `.env.production`

Los siguientes valores han sido agregados automáticamente:

```bash
# Mercury API Configuration
MERCURY_API_TOKEN=REDACTED_MERCURY_API_TOKEN
MERCURY_API_URL=https://api.mercury.com/api/v1

# CHECKING Account (Provedores-Sajet - ACTIVA)
MERCURY_CHECKING_ACCOUNT_ID=202369307283
MERCURY_CHECKING_ROUTING_NUMBER=091311229
MERCURY_CHECKING_ACCOUNT_NUMBER=202369307283
MERCURY_CHECKING_BALANCE_AVAILABLE=1068.46

# SAVINGS Account (Pendiente de crear)
MERCURY_SAVINGS_ACCOUNT_ID=                    # TODO: Configurar
MERCURY_SAVINGS_ROUTING_NUMBER=                # TODO: Configurar
MERCURY_SAVINGS_ACCOUNT_NUMBER=                # TODO: Configurar

# Transfer Limits
MERCURY_MIN_TRANSFER_TO_CHECKING=1000
MERCURY_MAX_TRANSFER_TO_CHECKING=100000
MERCURY_CHECKING_MIN_BALANCE=5000
MERCURY_DAILY_LIMIT=100000

# Fees
MERCURY_ACH_FEE=0
MERCURY_WIRE_FEE=15

# Webhook Security
MERCURY_WEBHOOK_SECRET=                        # TODO: Obtener de Mercury
```

---

## ⚠️ Situación Actual

### CHECKING Account (ACTIVA ✅)
```
Status:              ✅ CONFIGURADA Y LISTA
Balance:             $1,068.46
Propósito:           Dispersión a proveedores (ACH/Wire)
Sistema:             Conectada a mercury_account_manager.py
```

### SAVINGS Account (PENDIENTE ⏳)
```
Status:              ⏳ NO CONFIGURADA
Propósito:           Acumular fondos de clientes
Acción requerida:    Crear cuenta en Mercury
Datos requeridos:    Account ID, Routing Number, Account Number
```

---

## 🚀 Próximos Pasos

### Paso 1: Crear SAVINGS Account en Mercury
1. Login a https://app.mercury.com
2. Click "New Account"
3. Nombre: "Jeturing Savings - Reserve" (o similar)
4. Tipo: Business Savings Account
5. Conectar a Stripe para depósitos automáticos
6. Copiar Account ID, Routing Number, Account Number

### Paso 2: Actualizar `.env.production`
```bash
MERCURY_SAVINGS_ACCOUNT_ID=<account_id>
MERCURY_SAVINGS_ROUTING_NUMBER=<routing>
MERCURY_SAVINGS_ACCOUNT_NUMBER=<account_number>
```

### Paso 3: Configurar Webhook Secret
1. En Mercury Dashboard: Settings → Webhooks
2. Copy: Webhook Secret
3. Agregar a `.env.production`:
```bash
MERCURY_WEBHOOK_SECRET=<secret>
```

### Paso 4: Probar API Endpoints
```bash
# Ver estado de cuentas
curl http://localhost:8000/api/treasury/accounts/dual-status

# Expected response:
{
  "status": "warning",  # CHECKING < MIN_BALANCE
  "accounts": {
    "checking": {
      "balance": 1068.46,
      "available": 1068.46
    },
    "savings": {
      "balance": 0,      # Sin configurar aún
      "available": 0
    }
  }
}
```

---

## 🔐 Seguridad

### Token de Mercury
```
Token:     REDACTED_MERCURY_API_TOKEN
Security:  IP whitelist activado (requiere agregar IP del servidor)
```

**Acción Requerida**:
Si recibe error `ipNotWhitelisted`, agregar IP del servidor en:
https://app.mercury.com → Settings → API Tokens → Whitelist

### Restricciones de CHECKING
```
✅ PERMITIDO:
   • ACH transfers a proveedores
   • Wire transfers (con fee $15)
   • Ver balance
   • Historial de transacciones

❌ NO PERMITIDO:
   • Depósitos directos (solo de SAVINGS)
   • Cambio de datos de cuenta
   • Transferencias a otros Mercury accounts sin aprobación
```

---

## 💡 Cómo Funciona el Sistema Ahora

### Sin SAVINGS (Configuración Actual)
```
Cliente paga → Stripe
              ↓
          (Manual) 
              ↓
        CHECKING (Provedores-Sajet)
              ↓
          Proveedores

⚠️ PROBLEMA: Sin auto-replenish automático
   Si CHECKING cae bajo $5,000, pagos fallarán
```

### Con SAVINGS (Próxima Semana)
```
Cliente paga → Stripe
              ↓
         SAVINGS (Ahorros)
              ↓
       Auto-replenish si CHECKING < $5K
              ↓
         CHECKING (Provedores-Sajet)
              ↓
          Proveedores

✅ SOLUCIÓN: Auto-replenish automático
   CHECKING siempre disponible para pagos
```

---

## 📊 Estado del Sistema

| Componente | Status | Detalles |
|-----------|--------|---------|
| Mercury Token | ✅ | Configurado en .env.production |
| CHECKING Account | ✅ | Provedores-Sajet (202369307283) |
| SAVINGS Account | ⏳ | Pendiente de crear |
| API Endpoints | ✅ | 3 endpoints disponibles |
| Database Models | ⏳ | Phase 2 (próxima semana) |
| Webhook Handlers | ⏳ | Phase 2 (próxima semana) |

---

## 🧪 Prueba Rápida del Token

Si necesitas verificar que el token funciona:

```bash
# Desde un servidor con IP whitelisted:
python3 << 'EOF'
import requests

token = 'REDACTED_MERCURY_API_TOKEN'

# Obtener detalles de CHECKING account
response = requests.get(
    'https://api.mercury.com/api/v1/accounts/202369307283',
    auth=(token, '')
)

print("Status:", response.status_code)
if response.status_code == 200:
    print("✅ Token válido")
    print(response.json())
else:
    print("❌ Error:", response.json())
EOF
```

---

## 📋 Checklist de Configuración

### Completado
- [x] Cuenta CHECKING "Provedores-Sajet" configurada
- [x] Token Mercury agregado a .env.production
- [x] mercury_account_manager.py actualizado
- [x] Endpoints REST disponibles

### Pendiente
- [ ] Crear SAVINGS account en Mercury
- [ ] Obtener credenciales de SAVINGS
- [ ] Actualizar .env.production con SAVINGS data
- [ ] Configurar webhook secret
- [ ] Probar endpoints con datos reales

### Próxima Fase
- [ ] Database migrations (provider_accounts, payout_requests)
- [ ] Webhook handlers (Mercury + Stripe)
- [ ] Dashboard UI

---

## 🔗 Referencias

**Documentación de la Arquitectura**:
- [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md)
- [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md)

**Código**:
- [app/services/mercury_account_manager.py](../app/services/mercury_account_manager.py)
- [app/routes/payments.py](../app/routes/payments.py)

**Credenciales**:
- Mercury Dashboard: https://app.mercury.com
- API Docs: https://docs.mercury.com

---

**Status**: ✅ CHECKING CONFIGURADA - LISTA PARA USAR
**Próximo Step**: Crear SAVINGS account y finalizar configuración

---
