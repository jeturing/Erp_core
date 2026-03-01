# Sistema de Migración Automática de Planes

## 📋 Descripción

Sistema inteligente que **monitorea el consumo de almacenamiento** (base de datos + filestore) de cada tenant y **recomienda/ejecuta migraciones automáticas** de plan cuando se acercan o superan los límites.

## 🎯 Características

✅ **Evaluación en tiempo real** del consumo de BD + filestore  
✅ **Alertas por umbrales** (75%, 90%, 100%)  
✅ **Recomendación inteligente** de plan superior  
✅ **Migración automática** (con dry-run)  
✅ **Migración batch** para múltiples tenants  
✅ **API REST completa** + CLI de administración  
✅ **Reportes ejecutivos** con resúmenes por estado  

---

## 📊 Umbrales de Alerta

| Estado | % Uso | Descripción | Acción |
|--------|-------|-------------|--------|
| **OK** | 0-74% | ✅ Dentro del límite | Ninguna |
| **Warning** | 75-89% | 🟡 Acercándose al límite | Notificar |
| **Critical** | 90-99% | 🔴 Cerca del límite | Recomendar migración |
| **Exceeded** | ≥100% | ⚠️ Límite superado | Migración urgente |

---

## 🔧 Configuración de Planes

### Ejemplo de límites de storage por plan:

```python
# Básico: 512 MB
# Professional: 2 GB
# Enterprise: Ilimitado (0 = sin límite)

from app.models.database import SessionLocal, Plan

db = SessionLocal()
plan = db.query(Plan).filter(Plan.name == "basic").first()
plan.max_storage_mb = 512  # 512 MB
db.commit()
```

### Planes actuales:

| Plan | Display Name | Storage | Precio Base | Por Usuario |
|------|--------------|---------|-------------|-------------|
| basic | Basic | 512 MB | $160 | $40 |
| pro | Professional | 2 GB | $200 | $38 |
| enterprise | Enterprise | ∞ Ilimitado | $400 | $35 |

---

## 🚀 Uso

### 1. CLI de Administración

```bash
cd /opt/Erp_core

# Listar planes disponibles
python3 scripts/plan_migration_cli.py plans

# Evaluar un tenant específico
python3 scripts/plan_migration_cli.py evaluate --tenant sattra

# Evaluar todos los tenants
python3 scripts/plan_migration_cli.py evaluate-all

# Ver resumen ejecutivo
python3 scripts/plan_migration_cli.py summary

# Ver tamaño actual de un tenant
python3 scripts/plan_migration_cli.py size --tenant sattra

# Simular migración (dry-run)
python3 scripts/plan_migration_cli.py migrate --tenant sattra --dry-run

# Ejecutar migración real
python3 scripts/plan_migration_cli.py migrate --tenant sattra

# Migración batch (todos los que requieran)
python3 scripts/plan_migration_cli.py migrate-all --dry-run
python3 scripts/plan_migration_cli.py migrate-all  # REAL (con confirmación)
```

### 2. API REST

**Headers requeridos:**
```
X-API-Key: <PROVISIONING_API_KEY>
```

#### Evaluar un tenant

```bash
POST /api/plan-migration/evaluate
Content-Type: application/json

{
  "tenant_db": "sattra",
  "customer_id": 5
}
```

**Respuesta:**
```json
{
  "company_name": "Sattra",
  "subdomain": "sattra",
  "tenant_db": "sattra",
  "plan_name": "basic",
  "plan_display": "Basic",
  "plan_storage_limit_mb": 512,
  "storage_unlimited": false,
  "current_usage": {
    "tenant_db": "sattra",
    "db_size_mb": 73.2,
    "filestore_size_mb": 0,
    "total_size_mb": 73.2
  },
  "status": "ok",
  "usage_percent": 14.3,
  "should_migrate": false,
  "recommendation": {
    "plan_name": "pro",
    "plan_display": "Professional",
    "storage_limit_mb": 2048,
    "base_price": 200.0
  },
  "message": "✅ OK: 73.2MB / 512MB (14.3%). Uso dentro del límite."
}
```

#### Evaluar todos los tenants

```bash
GET /api/plan-migration/evaluate-all
X-API-Key: <API_KEY>
```

#### Resumen ejecutivo

```bash
GET /api/plan-migration/summary
X-API-Key: <API_KEY>
```

**Respuesta:**
```json
{
  "success": true,
  "summary": {
    "total_tenants": 7,
    "ok": 5,
    "warning": 1,
    "critical": 1,
    "exceeded": 0,
    "migration_recommended": 1,
    "tenants_by_status": {
      "ok": [...],
      "warning": [...],
      "critical": [
        {
          "company_name": "Techeels",
          "subdomain": "techeels",
          "usage_percent": 95.2,
          "current_plan": "Basic",
          "recommendation": {
            "plan_name": "pro",
            "plan_display": "Professional"
          }
        }
      ],
      "exceeded": []
    }
  }
}
```

#### Migración automática

```bash
POST /api/plan-migration/auto-migrate
Content-Type: application/json
X-API-Key: <API_KEY>

{
  "tenant_db": "sattra",
  "dry_run": true  // false para ejecutar real
}
```

#### Migración batch

```bash
POST /api/plan-migration/batch-migrate?dry_run=true
X-API-Key: <API_KEY>
```

#### Ver tamaño de un tenant

```bash
GET /api/plan-migration/tenant/sattra/size
X-API-Key: <API_KEY>
```

#### Listar planes disponibles

```bash
GET /api/plan-migration/plans
X-API-Key: <API_KEY>
```

---

## 🤖 Automatización con Cron

### Evaluación diaria + alertas

```bash
# Crontab: Evaluar todos los tenants diariamente a las 2 AM
0 2 * * * cd /opt/Erp_core && python3 scripts/plan_migration_cli.py summary >> /var/log/plan-migration.log 2>&1

# Evaluación semanal con resumen ejecutivo
0 8 * * 1 cd /opt/Erp_core && python3 scripts/plan_migration_cli.py evaluate-all | mail -s "Reporte Semanal Planes" admin@sajet.us
```

### Migración automática (opcional)

```bash
# ⚠️ PRECAUCIÓN: Solo habilitar después de testing exhaustivo
# Ejecutar migraciones automáticas semanalmente en dry-run
0 3 * * 0 cd /opt/Erp_core && python3 scripts/plan_migration_cli.py migrate-all --dry-run >> /var/log/plan-migration.log 2>&1
```

---

## 📈 Lógica de Recomendación

El sistema busca el **plan más pequeño** que pueda acomodar:
- **Uso actual + 25% de buffer**

Ejemplo:
- Tenant usa **400 MB**
- Capacidad requerida: **500 MB** (400 * 1.25)
- Plan recomendado: **Basic (512 MB)** ✅
- Si no hay plan que lo acomode → **Recomendar ilimitado**

---

## 🔐 Seguridad

- ✅ Todos los endpoints requieren `X-API-Key: <PROVISIONING_API_KEY>`
- ✅ Migraciones reales requieren confirmación explícita
- ✅ Dry-run por defecto para testing
- ✅ Auditoría completa en logs

---

## 📝 Archivos Clave

```
/opt/Erp_core/
├── app/
│   ├── services/
│   │   └── plan_migration_service.py    # Servicio principal
│   └── routes/
│       └── plan_migration.py            # Endpoints REST
├── scripts/
│   └── plan_migration_cli.py            # CLI de administración
└── requirements.txt                     # Dependencias (tabulate)
```

---

## 🧪 Testing

### 1. Configurar planes de prueba

```python
# Configurar límites pequeños para testing
from app.models.database import SessionLocal, Plan

db = SessionLocal()
basic = db.query(Plan).filter(Plan.name == "basic").first()
basic.max_storage_mb = 100  # 100 MB para testing
db.commit()
```

### 2. Evaluar tenant

```bash
python3 scripts/plan_migration_cli.py evaluate --tenant sattra
```

### 3. Simular migración

```bash
python3 scripts/plan_migration_cli.py migrate --tenant sattra --dry-run
```

### 4. Ejecutar migración real

```bash
python3 scripts/plan_migration_cli.py migrate --tenant sattra
```

---

## 🚨 Solución de Problemas

### Error: "No se pudo determinar la BD del tenant"

**Causa:** El tenant no tiene deployment o subdomain configurado.

**Solución:**
```bash
# Verificar que el tenant existe en TenantDeployment
SELECT * FROM tenant_deployments WHERE subdomain = 'sattra';
```

### Error: "Plan 'X' no encontrado"

**Causa:** El plan no existe o está inactivo.

**Solución:**
```bash
# Listar planes activos
python3 scripts/plan_migration_cli.py plans

# Activar plan si es necesario
UPDATE plans SET is_active = true WHERE name = 'basic';
```

### Tamaño de BD no se calcula correctamente

**Causa:** PostgreSQL en PCT diferente o credenciales incorrectas.

**Solución:**
```bash
# Verificar configuración en .env.production
ODOO_DB_HOST=10.10.10.137
ODOO_FILESTORE_PCT_ID=105
```

---

## 📊 Ejemplo de Salida CLI

```
python3 scripts/plan_migration_cli.py summary

======================================================================
📊 RESUMEN EJECUTIVO DE PLANES
======================================================================
Total Tenants: 7
  ✅ OK: 5
  🟡 Warning: 1
  🔴 Critical: 1
  ⚠️  Exceeded: 0
  💡 Requieren migración: 1
======================================================================

CRITICAL:
  • Techeels (techeels) - 95.2%
    → Recomendar: Professional

WARNING:
  • Booking (boocking) - 82.1%
    → Recomendar: Professional
```

---

## 🎯 Roadmap Futuro

- [ ] **Notificaciones automáticas** por email/Slack cuando se alcancen umbrales
- [ ] **Dashboard visual** en frontend para monitoreo en tiempo real
- [ ] **Predicción de crecimiento** con ML para alertas proactivas
- [ ] **Integración con Stripe** para actualizar suscripciones automáticamente
- [ ] **Políticas de migración** configurables por cliente
- [ ] **Historial de migraciones** con auditoría completa

---

## 📞 Soporte

- **Documentación:** `/opt/Erp_core/docs/PLAN_MIGRATION.md`
- **Logs:** `/var/log/plan-migration.log`
- **Contacto:** admin@sajet.us
