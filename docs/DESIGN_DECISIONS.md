# 🎯 Decisiones de Diseño — Sistema de Pagos y Dispersión

## Contexto

Se implementó un sistema completo de pagos para Jeturing ERP que permite:
1. Recibir dinero de clientes (vía Stripe)
2. Dispersar pagos a proveedores (vía Mercury Banking)
3. Validar cuentas bancarias (KYC)
4. Generar reportes de tesorería

---

## 1️⃣ Decisión: Mercury Banking como Provedor Principal

### Opción A (Elegida): Mercury Banking ✅
```
Ventajas:
+ API moderna y bien documentada
+ ACH sin comisiones (crucial para competitividad)
+ Wire transfers disponibles
+ Dashboard integrado
+ Webhooks para notificaciones en tiempo real
+ Soporte técnico USA
+ Permite conectar con Stripe directamente

Desventajas:
- Solo para cuentas US
- Requiere EIN válido
```

### Opción B (Alternativa): Dwolla + Plaid
```
Ventajas:
+ Más flexible geográficamente
+ Mejor soporte para internacional

Desventajas:
- Comisiones más altas en ACH ($0.25)
- Más complejo de integrar
- Menos webhooks
```

### Opción C (No elegida): Stripe Connect Solo
```
Ventajas:
+ Ya tenemos integración Stripe

Desventajas:
- No permite disbursements a cuentas arbitrarias
- Muy enfocado en pagos de tarjeta
- ACH caro ($0.80)
```

**Conclusión**: Mercury es ideal para nuestro caso porque:
- Jeturing necesita dispersar a proveedores domésticos (RD, US)
- ACH sin comisión = máximo ahorro
- API simple y moderna

---

## 2️⃣ Decisión: Arquitectura de 3 Módulos

### Estructura Elegida:
```
mercury_client.py        # Abstracción de API (bajo nivel)
     ↓
payment_processor.py     # Orquestación (lógica de negocio)
     ↓
treasury_manager.py      # Analytics (reportes)
     ↓
routes/payments.py       # HTTP (alto nivel)
```

### Alternativa No Elegida: Todo en Un Archivo
```
✗ Dificultaría testing
✗ Haría mantenimiento más complicado
✗ No permitiría reutilizar lógica
```

**Conclusión**: Separación clara de responsabilidades facilita:
- Testing unitario
- Reusabilidad (mercury_client puede usarse en background jobs)
- Mantenimiento independiente

---

## 3️⃣ Decisión: Flujo de Autorización en Dos Pasos

### Elegido: Manual + Automático ✅
```
1. Payout request creado (automático desde invoice pagada)
2. Admin autoriza en dashboard (manual)
3. Sistema ejecuta transfer (automático)
```

### Alternativa 1: 100% Automático
```
✗ Riesgo: Si hay error en cálculo, dinero se envía equivocadamente
✗ Imposible de auditar quién aprobó
✗ Menos control en caso de problemas
```

### Alternativa 2: 100% Manual
```
✗ Lento: Admin debe crear payouts manualmente
✗ Propenso a errores humanos
✗ No escala con crecimiento
```

**Conclusión**: Híbrido balancea automatización + control:
- Seguridad: Admin revisa antes de ejecutar
- Velocidad: Creación automática desde invoices
- Auditabilidad: Log de quién aprobó

---

## 4️⃣ Decisión: KYC Manual (Por Ahora)

### Elegido: Validación Manual + Mercury Validation ✅
```
1. Sistema valida formato (cuenta, routing)
2. Mercury verifica si está disponible
3. Admin aprueba KYC en dashboard
4. Proveedor puede recibir pagos
```

### Alternativa 1: Micro-depósitos Automáticos
```
✓ Más riguroso
✗ Tarda 3-5 días
✗ Complicado de automatizar
```

### Alternativa 2: Solo Validar Formato
```
✓ Rápido
✗ Riesgo alto de transferencias falladas
```

**Conclusión**: Validación manual es suficiente para MVP porque:
- Jeturing conoce a sus proveedores
- Pueden validar directamente por phone
- Escalable hacia micro-depósitos en futuro

---

## 5️⃣ Decisión: Comisión del 15% (Hardcoded por Ahora)

### Elegido: Hardcoded en payment_processor.py ✅
```python
jeturing_commission_pct = 15.0
```

### Alternativa 1: BD Config
```python
# SELECT commission_pct FROM provider_commission_rules WHERE provider_id = ?
✓ Flexible por proveedor
✗ Más lento (query BD)
✗ Complica tests
```

### Alternativa 2: Parámetro en Request
```python
POST /api/payouts/create
{
  "gross_amount": 5000,
  "commission_pct": 15
}
✓ Flexible por request
✗ Riesgo: Admin puede cambiarla sin autorización
✗ Complica auditoría
```

**Conclusión**: Hardcoded en código es correcto para MVP:
- Toda la lógica centralizada
- Fácil de cambiar si necesita actualización
- Seguro: no hay manera de que admin cambie por accidente
- Migrar a BD si necesita ser dinámica en futuro

---

## 6️⃣ Decisión: ACH por Default, Wire Opcional

### Elegido: ACH por default ✅
```python
transfer_type = "ach"  # Por defecto

# Wire solo si:
# - Provider lo solicita explícitamente
# - Monto > $25K
# - Transfer internacional
```

### Racional:
```
ACH:
- Sin comisión ($0)
- 1-2 días
- Suficiente para mayoría de casos

Wire:
- $15 comisión
- 1 día
- Solo si urgencia
```

**Conclusión**: ACH first minimiza costos:
- Ahorro: $15 * 100 payouts/mes = $1500/mes
- Velocidad aceptable (1-2 días)
- Escalable

---

## 7️⃣ Decisión: Reconciliación Automática Horaria

### Elegido: Cron cada 1 hora ✅
```python
# Ejecutar automáticamente:
# - Sync Stripe balance
# - Sync Mercury balance
# - Calcular discrepancias
# - Alertar si discrepancia > 0.1%
```

### Alternativa 1: Tiempo Real (Event-driven)
```
✓ Más preciso
✗ Complejidad alta
✗ Riesgo de race conditions
✗ Requiere re-arquitecturación
```

### Alternativa 2: Manual (On-demand)
```
✓ Flexible
✗ Fácil de olvidar
✗ Riesgo de desbalances no detectados
```

**Conclusión**: Horaria es balance ideal:
- Automática = no se olvida
- Suficientemente frecuente para detectar problemas
- Simple de implementar
- Puede escalarse a cada 10 min en futuro

---

## 8️⃣ Decisión: Modelos BD (Placeholders por Ahora)

### Elegido: Métodos en payment_processor.py comentados ✅
```python
# TODO: Obtener payout_request desde BD
# TODO: Actualizar estado a "processing"
```

### Racional:
- Sistema funcional sin migración de BD
- Facilita testing
- Permite iterar antes de commitear esquema
- Migración es trabajo separado

### Próximo Paso (Fase 2):
```sql
-- Crear tablas
CREATE TABLE provider_accounts (...)
CREATE TABLE payout_requests (...)
CREATE TABLE mercury_transactions (...)

-- Actualizar routes/payments.py para usar BD real
```

**Conclusión**: Deferred es correcto porque:
- API contracts ya definidos
- Backend lógica lista
- BD migration es trabajo mecánico
- Permite testing con mocks

---

## 9️⃣ Decisión: Error Handling Conservative

### Elegido: Fail-safe con logging ✅
```python
try:
    result = processor.process_customer_payment(...)
except Exception as e:
    logger.error(f"Error: {e}")
    return HTTPException(500, detail=str(e))
```

### Alternativa 1: Retry Automático
```
✓ Resiliente a fallos temporales
✗ Riesgo: duplos si no es idempotente
✗ Complicado de debuggear
```

### Alternativa 2: Fail Silently
```
✓ No molesta al usuario
✗ Peligroso: dinero se queda en limbo
✗ Difícil de detectar
```

**Conclusión**: Conservative + logging es correcto:
- Falla visible = detectada rápidamente
- Logs permiten debugging
- No hay dinero en limbo
- Admin puede reintentar manualmente

---

## 🔟 Decisión: Documentación Dual (Arquitectura + Uso)

### Elegido: 2 Documentos Complementarios ✅
```
PAYMENT_FLOW_ARCHITECTURE.md  # Para developers
                              # Cómo está construido
                              # Decisiones de design
                              # Flujos de datos

PAYMENT_FLOW_USAGE.md         # Para operators
                              # Cómo usar
                              # Ejemplos de curl
                              # Troubleshooting
```

### Alternativa: Un Solo Documento
```
✗ Mezcla conceptos técnicos con operacionales
✗ Difícil de navegar
✗ No está claro quién es el audience
```

**Conclusión**: Separación clara facilita:
- Onboarding de developers
- Training de operators
- Mantenimiento más fácil

---

## ✨ Principios Seguidos

1. **KISS** (Keep It Simple, Stupid)
   - Comenzar con lo mínimo funcional
   - Iterar basado en feedback
   - No sobre-engineerizar

2. **Separación de Concerns**
   - API client ≠ Business Logic ≠ Analytics
   - Cada módulo tiene responsabilidad clara

3. **Seguridad Conservative**
   - Favor fallar que permitir operación insegura
   - Logging completo de transacciones
   - Human approval para operaciones críticas

4. **Documentación Exhaustiva**
   - Código comentado
   - Guías de usuario
   - Examples de curl

5. **Testing-Ready**
   - Módulos desacoplados = fácil de mockar
   - Type hints en funciones
   - Validación temprana de errores

---

## 🚀 Evolución Futura

Las decisiones actuales permiten:

**Fase 2**: Migración de BD
- Crear tablas reales
- Reemplazar stubs por queries

**Fase 3**: Webhooks
- Mercury events → DB updates
- Stripe events → Payment processor

**Fase 4**: Dashboard
- React components para tesorería
- Gráficos de cash flow

**Fase 5**: ML/Analytics
- Forecasting automático
- Detección de anomalías
- Recomendaciones de dispersión

**Fase 6**: Internacionalización
- Soporte para Wire internacional
- Múltiples monedas
- Conversión automática

---

## 📝 Cambios de Decisión Documentados

Cuando se decida cambiar algo (ej: comisión variable), actualizar:
1. Código (payment_processor.py)
2. Documentación (PAYMENT_FLOW_ARCHITECTURE.md)
3. Este archivo (DESIGN_DECISIONS.md)
4. Commit con descripción clara

---

## ✅ Checklist para Futuras Iteraciones

- [ ] ¿La decisión mantiene KISS?
- [ ] ¿Está documentada?
- [ ] ¿Es reversible o complicada de cambiar?
- [ ] ¿Requiere migración de BD?
- [ ] ¿Afecta a otros módulos?
- [ ] ¿Está testeada?
- [ ] ¿Se comunicó al equipo?

