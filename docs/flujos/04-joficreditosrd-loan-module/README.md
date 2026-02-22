# 04 - Tenant joficreditosrd: Módulo de Préstamos (jeturing_finance_core)

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


> **Fecha**: 2025-02-18  
> **Nodo**: PCT105 (10.10.10.100)  
> **BD**: `joficreditosrd`  
> **Módulo**: `jeturing_finance_core` v17.0.2.0.0

---

## 1. Configuración Regional

### Idioma y Zona Horaria

| Parámetro | Valor |
|-----------|-------|
| Idioma | `es_DO` (Español - República Dominicana) |
| Zona horaria | `America/Santo_Domingo` |
| Compañía | Jofi Creditos RD |
| web.base.lang | `es_DO` |

**Usuarios configurados:**

| Login | Idioma | TZ |
|-------|--------|----|
| admin@sajet.us | es_DO | America/Santo_Domingo |
| Admin@joficreditosrd.com | es_DO | America/Santo_Domingo |

### Cómo se aplicó

```bash
# Instalación del idioma
odoo-bin -c /etc/odoo/odoo.conf -d joficreditosrd --load-language=es_DO --no-http --stop-after-init

# Configuración vía Odoo Shell
odoo-bin shell -c /etc/odoo/odoo.conf -d joficreditosrd --no-http
>>> users = env["res.users"].search([])
>>> users.write({"lang": "es_DO", "tz": "America/Santo_Domingo"})
>>> env["ir.config_parameter"].sudo().set_param("web.base.lang", "es_DO")
```

---

## 2. Datos Iniciales Cargados (default_loan_setup.xml)

### 2.1 Tipos de Préstamo (`loan.type`)

| ID | Código | Nombre | Tasa | Modo Interés | Método Pago |
|----|--------|--------|------|--------------|-------------|
| 1 | JFC_PERSONAL_FLAT | Préstamo Personal (Tasa Plana) | 12% | flat | direct |
| 2 | JFC_BUSINESS_REDUCING | Préstamo Empresarial (Saldo Insoluto) | 10% | reducing | direct |
| 3 | JFC_EMERGENCY | Préstamo de Emergencia | 15% | flat | payroll |

### 2.2 Políticas (`loan.policies`)

| ID | Código | Nombre | Tipo |
|----|--------|--------|------|
| 1 | JFC_MAX_PERSONAL | Política Máximo Préstamo Personal | max (RD$ 75,000) |
| 2 | JFC_MAX_BUSINESS | Política Máximo Préstamo Empresarial | max (RD$ 250,000) |
| 3 | JFC_GAP_6M | Política Brecha entre Préstamos | gap (6 meses) |
| 4 | JFC_QUALIFY_90D | Política Período de Calificación | qualifying (90 días) |

### 2.3 Documentos Probatorios (`loan.proof`)

| ID | Nombre | Obligatorio |
|----|--------|-------------|
| 1 | Documento de Identidad | ✅ |
| 2 | Comprobante de Ingresos | ✅ |
| 3 | Comprobante de Domicilio | ✅ |

### 2.4 Factores de Score Crediticio (`credit.score.factor`)

| Código | Nombre | Peso | Descripción |
|--------|--------|------|-------------|
| payment_history | Payment History | 35% | Historial de pagos a tiempo |
| loan_performance | Loan Performance | 30% | Rendimiento general de préstamos |
| kyc_completeness | KYC Completeness | 15% | Documentación KYC completa |
| debt_ratio | Debt Ratio | 10% | Ratio deuda/capacidad |
| loan_count | Loan Experience | 10% | Experiencia crediticia |

### 2.5 Otros registros

- **Secuencia**: `LOAN/00001` (ir.sequence code=`loan.request`)
- **Cron**: Recalcular scores crediticios (semanal)
- **Templates email**: Notificación aprobación de préstamo

---

## 3. Validación de Tabla de Amortización

### 3.1 TEST FLAT — Préstamo Personal

```
Parámetros: RD$ 50,000 | 12 meses | 12% anual (tasa plana)
Fórmula:    Principal mensual = P/N = 4,166.67
            Interés total = (P×R×N)/(12×100) = 6,000
            Interés mensual = 6,000/12 = 500.00
```

| # | Fecha | Saldo Ini | Principal | Interés | EMI | Saldo Fin |
|---|-------|-----------|-----------|---------|-----|-----------|
| 1 | 2026-03-01 | 50,000.00 | 4,166.67 | 500.00 | 4,666.67 | 45,833.33 |
| 2 | 2026-04-01 | 45,833.33 | 4,166.67 | 500.00 | 4,666.67 | 41,666.66 |
| 3 | 2026-05-01 | 41,666.66 | 4,166.67 | 500.00 | 4,666.67 | 37,499.99 |
| 4 | 2026-06-01 | 37,499.99 | 4,166.67 | 500.00 | 4,666.67 | 33,333.32 |
| 5 | 2026-07-01 | 33,333.32 | 4,166.67 | 500.00 | 4,666.67 | 29,166.65 |
| 6 | 2026-08-01 | 29,166.65 | 4,166.67 | 500.00 | 4,666.67 | 24,999.98 |
| 7 | 2026-09-01 | 24,999.98 | 4,166.67 | 500.00 | 4,666.67 | 20,833.31 |
| 8 | 2026-10-01 | 20,833.31 | 4,166.67 | 500.00 | 4,666.67 | 16,666.64 |
| 9 | 2026-11-01 | 16,666.64 | 4,166.67 | 500.00 | 4,666.67 | 12,499.97 |
| 10 | 2026-12-01 | 12,499.97 | 4,166.67 | 500.00 | 4,666.67 | 8,333.30 |
| 11 | 2027-01-01 | 8,333.30 | 4,166.67 | 500.00 | 4,666.67 | 4,166.63 |
| 12 | 2027-02-01 | 4,166.63 | 4,166.63 | 500.00 | 4,666.63 | **0.00** |
| **TOTAL** | | | **50,000.00** | **6,000.00** | **56,000.00** | |

**Resultado: ✅ TODAS LAS VALIDACIONES OK**
- Principal total = 50,000.00 ✅
- Interés total = 6,000.00 ✅
- Saldo final = 0.00 ✅
- 12 cuotas generadas ✅
- Última cuota ajustada por redondeo ✅

### 3.2 TEST REDUCING — Préstamo Empresarial (Saldo Insoluto)

```
Parámetros: RD$ 100,000 | 6 meses | 10% anual (saldo insoluto)
Fórmula:    r = 10/(12×100) = 0.008333
            EMI = P × r × (1+r)^n / ((1+r)^n - 1) = 17,156.14
```

| # | Fecha | Saldo Ini | Principal | Interés | EMI | Saldo Fin |
|---|-------|-----------|-----------|---------|-----|-----------|
| 1 | 2026-03-01 | 100,000.00 | 16,322.81 | 833.33 | 17,156.14 | 83,677.19 |
| 2 | 2026-04-01 | 83,677.19 | 16,458.83 | 697.31 | 17,156.14 | 67,218.36 |
| 3 | 2026-05-01 | 67,218.36 | 16,595.99 | 560.15 | 17,156.14 | 50,622.37 |
| 4 | 2026-06-01 | 50,622.37 | 16,734.29 | 421.85 | 17,156.14 | 33,888.08 |
| 5 | 2026-07-01 | 33,888.08 | 16,873.74 | 282.40 | 17,156.14 | 17,014.34 |
| 6 | 2026-08-01 | 17,014.34 | 17,014.34 | 141.79 | 17,156.13 | **0.00** |
| **TOTAL** | | | **100,000.00** | **2,936.83** | **102,936.83** | |

**Resultado: ✅ TODAS LAS VALIDACIONES OK**
- Principal total = 100,000.00 ✅
- EMI esperada (17,156.14 × 6) = 102,936.84 vs real 102,936.83 (diff < $0.01) ✅
- Saldo final = 0.00 ✅
- 6 cuotas generadas ✅
- Interés decrece cada mes (reducing balance correcto) ✅
- Última cuota ajustada por redondeo ✅

---

## 4. Flujo de Préstamo (Máquina de Estados)

```
  draft ──[action_confirm]──► applied ──[action_approve]──► approve
    │                                                           │
    │                                                    [compute_loan]
    │                                                           │
    │                                                    cuotas generadas
    │                                                           │
    │                                                    [disburse_loan]
    │                                                           │
    └──────────[action_cancel]──────────────────────────► cancel
                                                           │
                                                      (unlink installments)
```

### Validaciones por Estado

| Transición | Método | Validaciones |
|-----------|--------|--------------|
| draft → applied | `action_confirm()` | Políticas asignadas, monto ≤ máximo, gap entre préstamos |
| applied → approve | `action_approve()` | Período calificación cumplido (90 días) |
| approve → cuotas | `compute_loan()` | `approve_date` definida, estado válido |
| approve → disbursed | `disburse_loan()` | Cuentas contables configuradas, cuotas calculadas |

### Requisitos para Crear un Préstamo

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `partner_id` | Many2one | ✅ | Cliente (debe estar en `loan_type.partner_ids`) |
| `loan_type_id` | Many2one | ✅ | Tipo de préstamo |
| `principal_amount` | Float | ✅ | Monto del préstamo |
| `duration_months` | Integer | ✅ | Plazo en meses |
| `approve_date` | Date | ✅ | Fecha de aprobación |
| `applied_date` | Date | ✅ | Fecha de solicitud |
| `loan_partner_type` | Selection | ✅ | `customer` o `vendor` |
| `interest_mode` | Selection | | `flat` o `reducing` (hereda del tipo) |
| `rate` | Float | | Tasa anual % (hereda del tipo) |
| `policy_ids` | Many2many | ✅ | Políticas aplicables |

---

## 5. Notas Importantes

### Partner-Whitelist
Cada `loan.type` y `loan.policies` tiene un campo `partner_ids` (M2M). El partner **debe** estar vinculado al tipo de préstamo y a las políticas antes de crear una solicitud, de lo contrario se genera `ValidationError: Partner is not allowed`.

### Período de Calificación
La política `JFC_QUALIFY_90D` impide aprobar préstamos antes de 90 días desde la fecha de solicitud. Para testing se puede saltar con `write({"state": "approve"})`.

### Datos noupdate=1
Los datos del XML tienen `noupdate="1"`, lo que significa que:
- Se cargan **solo** en la primera instalación
- Un `--update` posterior **no** los sobreescribe
- Si se eliminan manualmente, solo se pueden restaurar con `-i` (reinstalación)

### Módulos Instalados

| Módulo | Versión | Estado |
|--------|---------|--------|
| jeturing_finance_core | 17.0.2.0.0 | ✅ installed |
| jeturing_branding | 17.0.1.0.0 | ✅ installed |
| sale_management | 17.0 | ✅ installed |
| website | 17.0 | ✅ installed |
| account | 17.0 | ✅ installed |
| purchase | 17.0 | ✅ installed |
| stock | 17.0 | ✅ installed |
| mail | 17.0 | ✅ installed |
