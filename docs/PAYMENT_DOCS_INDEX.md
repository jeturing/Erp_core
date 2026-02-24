"""
PAYMENT SYSTEM DOCUMENTATION INDEX
Índice Completo de Documentación del Sistema de Pagos y Dispersión

Documento: PAYMENT_DOCS_INDEX.md
Fecha: 2026-02-24
Versión: 1.0
"""

# 📚 Índice Completo: Sistema de Pagos y Dispersión Dual Mercury

## 🎯 Por Dónde Empezar

### Para Administradores (No Técnicos)
1. **Comienza aquí**: [DUAL_ACCOUNT_SUMMARY.md](DUAL_ACCOUNT_SUMMARY.md)
   - Resumen ejecutivo de 10 minutos
   - Qué cambió y por qué
   - Comparación antes/después
   - Ventajas principales

2. **Luego**: [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md)
   - Cómo crear las cuentas Mercury
   - Cómo probar los endpoints
   - Troubleshooting

### Para Developers (Técnicos)
1. **Comienza aquí**: [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md)
   - Diseño técnico detallado
   - Flujo de dinero
   - Componentes de código
   - Modelos de BD necesarios

2. **Luego**: [PAYMENT_SYSTEM_EVOLUTION.md](PAYMENT_SYSTEM_EVOLUTION.md)
   - Cómo evolucionó el sistema
   - Decisiones de diseño
   - Lecciones aprendidas

3. **Referencia**: Código fuente
   - [app/services/mercury_account_manager.py](../app/services/mercury_account_manager.py)
   - [app/services/payment_processor.py](../app/services/payment_processor.py)
   - [app/routes/payments.py](../app/routes/payments.py)

---

## 📖 Documentación por Tipo

### Guías de Setup
| Documento | Propósito | Líneas | Audiencia |
|-----------|----------|--------|-----------|
| [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) | Configuración paso a paso | 400 | Ops + Devs |

### Diseño Técnico
| Documento | Propósito | Líneas | Audiencia |
|-----------|----------|--------|-----------|
| [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) | Arquitectura detallada | 350 | Devs + Architects |
| [PAYMENT_SYSTEM_EVOLUTION.md](PAYMENT_SYSTEM_EVOLUTION.md) | Evolución y decisiones | 485 | Devs + Architects |

### Resúmenes Ejecutivos
| Documento | Propósito | Líneas | Audiencia |
|-----------|----------|--------|-----------|
| [DUAL_ACCOUNT_SUMMARY.md](DUAL_ACCOUNT_SUMMARY.md) | Resumen ejecutivo | 395 | Todos |
| [PAYMENT_DOCS_INDEX.md](PAYMENT_DOCS_INDEX.md) | Este índice | - | Todos |

### Referencia (De Fases Anteriores)
| Documento | Propósito | Líneas | Status |
|-----------|----------|--------|--------|
| [PAYMENT_FLOW_ARCHITECTURE.md](PAYMENT_FLOW_ARCHITECTURE.md) | Arquitectura original (una cuenta) | 250 | ✅ Actualizada |
| [PAYMENT_FLOW_USAGE.md](PAYMENT_FLOW_USAGE.md) | Guía de uso (endpoints) | 400 | ✅ Compatible |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Resumen Phase 1 | 424 | ✅ Referencia |
| [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) | Decisiones de diseño Phase 1 | 418 | ✅ Referencia |

---

## 🔍 Mapa de Documentación por Tema

### Flujo de Dinero
**¿Cómo fluye el dinero desde cliente a proveedor?**

📄 Documentos:
- [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) → Flujo General de Dinero (sección)
- [PAYMENT_SYSTEM_EVOLUTION.md](PAYMENT_SYSTEM_EVOLUTION.md) → Caso de Uso: Día Normal (sección)
- [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) → Flujo Completo: Cliente → Proveedor (sección)

### Arquitectura Técnica
**¿Cómo está construido el sistema?**

📄 Documentos:
- [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) → Componentes a Implementar (sección)
- [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) → Integración con Modelos Existentes (sección)

📁 Código:
- [app/services/mercury_account_manager.py](../app/services/mercury_account_manager.py) → Gestor de cuentas dual
- [app/services/payment_processor.py](../app/services/payment_processor.py) → Orquestación de pagos
- [app/routes/payments.py](../app/routes/payments.py) → Endpoints REST

### Configuración
**¿Qué necesito configurar?**

📄 Documentos:
- [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) → Paso 2: Actualizar .env.production (sección)
- [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) → Configuración Requerida (sección)

### Endpoints y API
**¿Qué endpoints están disponibles?**

📄 Documentos:
- [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) → Paso 4: Usar los API Endpoints (sección)
- [DUAL_ACCOUNT_SUMMARY.md](DUAL_ACCOUNT_SUMMARY.md) → Endpoints Nuevos (sección)
- [PAYMENT_FLOW_USAGE.md](PAYMENT_FLOW_USAGE.md) → API Reference completa (Phase 1, aún válida)

### Seguridad
**¿Cómo está protegido el sistema?**

📄 Documentos:
- [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) → Consideraciones de Seguridad (sección)
- [DUAL_ACCOUNT_SUMMARY.md](DUAL_ACCOUNT_SUMMARY.md) → Seguridad Mejorada (sección)
- [PAYMENT_SYSTEM_EVOLUTION.md](PAYMENT_SYSTEM_EVOLUTION.md) → Mejoras de Seguridad (sección)

### Testing y Troubleshooting
**¿Cómo pruebo el sistema? ¿Cómo resuelvo problemas?**

📄 Documentos:
- [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) → Test Scenarios (sección)
- [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) → Troubleshooting (sección)
- [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) → Paso 3: Verificar Instalación (sección)

---

## 🚀 Guía Rápida por Rol

### Admin/Manager
**Tu rol**: Autorizar transfers y monitorear balances

Lectura recomendada:
1. [DUAL_ACCOUNT_SUMMARY.md](DUAL_ACCOUNT_SUMMARY.md) (15 min)
2. [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) → Paso 4: API Endpoints (10 min)
3. Bookmarks:
   - `GET /api/treasury/accounts/dual-status` → Ver balances
   - `POST /api/treasury/accounts/transfer-to-checking` → Transferir manualmente

### Backend Engineer
**Tu rol**: Mantener, actualizar y debuggear el sistema de pagos

Lectura recomendada:
1. [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) (20 min)
2. [PAYMENT_SYSTEM_EVOLUTION.md](PAYMENT_SYSTEM_EVOLUTION.md) (15 min)
3. Code:
   - [app/services/mercury_account_manager.py](../app/services/mercury_account_manager.py) (read)
   - [app/services/payment_processor.py](../app/services/payment_processor.py) (read)
   - [app/routes/payments.py](../app/routes/payments.py) (read)

### Data Analyst
**Tu rol**: Reportes, auditoría y análisis de cash flow

Lectura recomendada:
1. [DUAL_ACCOUNT_SUMMARY.md](DUAL_ACCOUNT_SUMMARY.md) (10 min)
2. [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) → Dashboard (5 min)
3. [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) → Dashboard Queries (10 min)

### CTO/Architect
**Tu rol**: Entender diseño, validar seguridad, guiar evolution

Lectura recomendada:
1. [PAYMENT_SYSTEM_EVOLUTION.md](PAYMENT_SYSTEM_EVOLUTION.md) (20 min) - Decisiones tomadas
2. [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) (25 min) - Diseño completo
3. [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) (Phase 1, aún relevante)

---

## 📊 Estructura de Archivos

```
/opt/Erp_core/
├── docs/
│   ├── PAYMENT_DOCS_INDEX.md                      ← Estás aquí
│   ├── DUAL_ACCOUNT_SUMMARY.md                    (ejecutivo)
│   ├── DUAL_ACCOUNT_SETUP_GUIDE.md               (setup)
│   ├── MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md      (diseño)
│   ├── PAYMENT_SYSTEM_EVOLUTION.md                (evolución)
│   ├── PAYMENT_FLOW_ARCHITECTURE.md              (Phase 1)
│   ├── PAYMENT_FLOW_USAGE.md                     (Phase 1)
│   ├── IMPLEMENTATION_SUMMARY.md                 (Phase 1)
│   └── DESIGN_DECISIONS.md                       (Phase 1)
│
├── app/services/
│   ├── mercury_client.py                         (Mercury API)
│   ├── mercury_account_manager.py                (Dual accounts) ← NUEVO
│   ├── payment_processor.py                      (Orchestration)
│   └── treasury_manager.py                       (Analytics)
│
├── app/routes/
│   └── payments.py                               (Endpoints + 3 nuevos)
│
└── app/main.py                                   (Router registrado)
```

---

## 🔄 Flujo de Lectura Recomendado

### Para Entender Rápido (30 minutos)
```
1. Este índice (5 min)
   ↓
2. DUAL_ACCOUNT_SUMMARY.md (15 min)
   ↓
3. DUAL_ACCOUNT_SETUP_GUIDE.md → Paso 4 (10 min)
```

### Para Entender Profundamente (2 horas)
```
1. DUAL_ACCOUNT_SUMMARY.md (15 min)
   ↓
2. MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md (30 min)
   ↓
3. PAYMENT_SYSTEM_EVOLUTION.md (30 min)
   ↓
4. DUAL_ACCOUNT_SETUP_GUIDE.md completo (30 min)
   ↓
5. Código fuente (app/services/) (15 min)
```

### Para Implementar (6 horas)
```
1. DUAL_ACCOUNT_SETUP_GUIDE.md completo (1 hora)
   ├─ Paso 1: Crear cuentas Mercury
   ├─ Paso 2: Configurar .env.production
   ├─ Paso 3: Verificar instalación
   └─ Paso 4: Usar API endpoints
   ↓
2. Crear dos cuentas reales en Mercury (1 hora)
   ↓
3. Configurar credenciales (30 min)
   ↓
4. Probar endpoints con curl (30 min)
   ↓
5. Leer código fuente (1 hora)
   ↓
6. Setup database (próxima fase, 1 hora+)
```

---

## 🎓 Glosario de Términos

| Término | Definición | Referencia |
|---------|-----------|-----------|
| **SAVINGS Account** | Cuenta Mercury para ahorros (reserva de clientes) | [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) |
| **CHECKING Account** | Cuenta Mercury para operativa (pagos a proveedores) | [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) |
| **Auto-replenish** | Transferencia automática SAVINGS → CHECKING cuando cae bajo mínimo | [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) |
| **Mercury Banking** | Plataforma de banking API usada para ACH/Wire transfers | [MERCURY_DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) |
| **ACH Transfer** | Transferencia ACH (gratis, 1-2 días) | [PAYMENT_SYSTEM_EVOLUTION.md](PAYMENT_SYSTEM_EVOLUTION.md) |
| **Wire Transfer** | Wire transfer internacional ($15 fee, 1 día) | [PAYMENT_SYSTEM_EVOLUTION.md](PAYMENT_SYSTEM_EVOLUTION.md) |
| **KYC** | Know Your Customer - validación de cuentas | [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) |
| **Payout** | Dispersión de fondos a proveedor | [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md) |
| **Reconciliation** | Sincronización de balances Stripe ↔ Mercury | [PAYMENT_SYSTEM_EVOLUTION.md](PAYMENT_SYSTEM_EVOLUTION.md) |

---

## 🔗 Enlaces Útiles

### Documentación Externa
- [Mercury Banking API Docs](https://mercury.com/docs)
- [Stripe API Documentation](https://stripe.com/docs/api)
- [ACH Transfers](https://stripe.com/docs/payments/ach-debit)
- [Bank Account Validation](https://plaid.com) (referencia)

### Dentro del Proyecto
- [Código fuente: mercury_account_manager.py](../app/services/mercury_account_manager.py)
- [Código fuente: payment_processor.py](../app/services/payment_processor.py)
- [Código fuente: payments.py routes](../app/routes/payments.py)

---

## 📞 Contacto y Soporte

### Para Preguntas sobre:

**Configuración**
→ Ver [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) → Troubleshooting

**Diseño Técnico**
→ Ver [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md)

**Endpoints API**
→ Ver [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md) → Paso 4 + [PAYMENT_FLOW_USAGE.md](PAYMENT_FLOW_USAGE.md)

**Decisiones de Diseño**
→ Ver [PAYMENT_SYSTEM_EVOLUTION.md](PAYMENT_SYSTEM_EVOLUTION.md)

**Código**
→ Ver código fuente directamente + [MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md](MERCURY_DUAL_ACCOUNT_ARCHITECTURE.md)

---

## ✅ Checklist para Setup

- [ ] Leo [DUAL_ACCOUNT_SUMMARY.md](DUAL_ACCOUNT_SUMMARY.md)
- [ ] Leo [DUAL_ACCOUNT_SETUP_GUIDE.md](DUAL_ACCOUNT_SETUP_GUIDE.md)
- [ ] Creo dos cuentas en Mercury
- [ ] Obtengo credenciales (API keys + account IDs)
- [ ] Configuro .env.production
- [ ] Pruebo endpoints con curl
- [ ] Leo código fuente
- [ ] Estoy listo para Phase 2 (Database migrations)

---

## 📈 Estado del Proyecto

**Phase 1** (Sistema Base): ✅ COMPLETADO
- mercury_client.py
- payment_processor.py
- treasury_manager.py
- routes/payments.py

**Phase 2** (Dual Account): ✅ COMPLETADO
- mercury_account_manager.py
- Actualización de payment_processor.py
- Nuevos endpoints
- Documentación completa

**Phase 3** (Database + Webhooks): 🔄 PRÓXIMA
- Database migrations
- Webhook handlers
- Integration testing

**Phase 4** (Dashboard + Reporting): 📅 FUTURA
- Dashboard UI
- Automated reporting
- Real-time monitoring

---

**Última actualización**: 2026-02-24
**Versión**: 1.0
**Status**: ✅ LISTO PARA USAR (credenciales pendientes)

---

*Para volver al inicio, ve a [README.md](../README.md)*
