# Admin Dashboard - Documentación Técnica

## Resumen

Dashboard administrativo en tiempo real para gestionar el sistema SaaS de onboarding multitenant. Proporciona métricas de negocio, listado de tenants con estado y acceso a funcionalidades de administración.

## URLs y Rutas

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/admin` | GET | Interfaz web del dashboard (HTML + Tailwind) |
| `/api/dashboard/metrics` | GET | Métricas agregadas (revenue, tenants, pending, CPU/RAM) |
| `/api/tenants` | GET | Listado de tenants con estado |
| `/api/tenants` | POST | Crear nuevo tenant (stub) |

## Endpoints Detallados

### GET /admin
**Descripción**: Sirve la interfaz web del dashboard administrativo.

**Response**: HTML (Tailwind CSS, Dark Mode).

**Auth**: Ninguna (abierto para desarrollo; agregar autenticación en producción).

**Ejemplo**:
```bash
curl https://localhost:4443/admin
```

---

### GET /api/dashboard/metrics
**Descripción**: Retorna métricas agregadas del sistema desde BD.

**Response** (200 OK):
```json
{
  "total_revenue": 197,
  "active_tenants": 2,
  "pending_setup": 1,
  "cluster_load": {
    "cpu": 42,
    "ram": 64
  }
}
```

**Campos**:
- `total_revenue` (int): Ingresos mensuales estimados en USD (suma de MRR).
- `active_tenants` (int): Suscripciones con status `active`.
- `pending_setup` (int): Suscripciones con status `pending`.
- `cluster_load` (object): CPU y RAM del cluster (placeholder; requiere integración con monitoreo real).

**Lógica**:
1. Cuenta filas en `subscriptions` con cada status.
2. Itera sobre suscripciones activas, obtiene el `plan` del cliente y suma precios fijos por plan.

**Precios de Referencia**:
- Basic: $29/mes
- Pro: $49/mes
- Enterprise: $99/mes

**Ejemplo**:
```bash
curl https://localhost:4443/api/dashboard/metrics
```

---

### GET /api/tenants
**Descripción**: Listado paginado de tenants ordenado por fecha de creación (más recientes primero).

**Query Parameters**: (próximas fases: `limit`, `offset`, `status_filter`).

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": 2,
      "company_name": "Global Logistics",
      "email": "it@globallog.com",
      "subdomain": "logistics.jeturing-saas.com",
      "plan": "standard",
      "status": "provisioning",
      "tunnel_active": false,
      "created_at": "2026-01-18T09:45:00Z"
    }
  ],
  "total": 1
}
```

**Campos**:
- `id` (int): ID de la suscripción (PK).
- `company_name` (string): Nombre de la empresa (de `customers.company_name`).
- `email` (string): Email del administrador.
- `subdomain` (string): Dominio asignado (ej: `acme.sajet.us`).
- `plan` (string): Plan contratado (`basic`, `pro`, `enterprise`).
- `status` (string): Estado de la suscripción (`active`, `provisioning`, `payment_failed`, `suspended`).
- `tunnel_active` (boolean): `true` si `status == active`.
- `created_at` (ISO 8601): Timestamp de creación de la suscripción.

**Mapeo de Status**:
| DB Status | UI Label |
|-----------|----------|
| `pending` | `provisioning` |
| `active` | `active` |
| `past_due` | `payment_failed` |
| `cancelled` | `suspended` |

**Ejemplo**:
```bash
curl https://localhost:4443/api/tenants
```

---

### POST /api/tenants
**Descripción**: Crear nuevo tenant (stub; la lógica real está en `/api/checkout`).

**Request Body** (Form/JSON):
```json
{
  "company_name": "Acme Corp",
  "admin_email": "admin@acme.com",
  "subdomain": "acme",
  "plan": "enterprise"
}
```

**Response** (201 Created):
```json
{
  "id": 999,
  "company_name": "Acme Corp",
  "admin_email": "admin@acme.com",
  "subdomain": "acme",
  "plan": "enterprise",
  "status": "provisioning",
  "tunnel_active": false,
  "created_at": "2026-01-18T12:30:45Z"
}
```

**Nota**: Endpoint stub sin persistencia. Usar `/api/checkout` + Stripe para creación real.

---

## Frontend - Integración JavaScript

El dashboard HTML (`templates/admin_dashboard.html`) incluye script que:

1. **Al cargar** (DOMContentLoaded):
   - Fetch a `/api/dashboard/metrics` y actualiza KPIs (revenue, tenants, pending, CPU/RAM).
   - Fetch a `/api/tenants` y renderiza tabla de tenants dinámicamente.

2. **Renderizado dinámico**:
   - Crea rows de tabla con badges de status coloreados.
   - Interpreta `tunnel_active` para mostrar icono de enlace.
   - Maneja casos sin datos (muestra "No tenants yet").

3. **Utilidades**:
   - `escapeHtml()`: Sanitiza strings contra XSS.
   - `formatDate()`: Convierte ISO 8601 a local time.
   - `numberFmt()`: Formatea números con separadores de miles.
   - `buildStatusBadge()`: Genera HTML del badge con clase Tailwind según status.

---

## Datos de Ejemplo

Para crear registros de prueba en la BD:

```sql
-- Crear cliente
INSERT INTO customers (email, full_name, company_name, subdomain, created_at)
VALUES ('admin@test.com', 'Test User', 'Test Corp', 'test-corp', NOW());

-- Crear suscripción activa
INSERT INTO subscriptions (customer_id, plan_name, status, created_at)
VALUES (1, 'enterprise', 'active', NOW());

-- Crear suscripción en provisioning
INSERT INTO subscriptions (customer_id, plan_name, status, created_at)
VALUES (1, 'pro', 'pending', NOW());
```

---

## Notas de Implementación

### Placeholder - Monitoreo de Cluster
El campo `cluster_load.cpu` y `.ram` actualmente devuelve valores fijos (42%, 64%). 

**Para producción**, integrar con:
- Prometheus / Grafana para métricas reales.
- O hacer query a `/proc/stat` en el servidor.
- O usar librerías como `psutil` si corres en Linux.

### Próximos Pasos (Fase 2-3)
1. **Autenticación**: Proteger `/admin` con JWT/sesión.
2. **Paginación**: Implementar `limit` y `offset` en `/api/tenants`.
3. **Filtros**: Query param `status=active&plan=enterprise`.
4. **Operaciones**: Endpoint `PATCH /api/tenants/{id}` para actualizar config/suspender.
5. **Reportes**: Integrar templates de Billing, Reports, Logs (de stitch templates).
6. **WebSocket Logs**: `/ws/logs/stream` para logs de provisioning en tiempo real.

---

## Testing

### Verificar endpoints con curl:

```bash
# Métricas
curl -k https://localhost:4443/api/dashboard/metrics | jq

# Tenants
curl -k https://localhost:4443/api/tenants | jq

# Dashboard HTML
curl -k https://localhost:4443/admin | head -20
```

### Desarrollo local (sin SSL):
```python
# En main.py, cambiar puerto temporalmente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

# Luego acceder a http://localhost:8000/admin
```

---

## Estructura de Archivos

```
/opt/onboarding-system/
├── app/
│   ├── main.py              # Endpoints /admin, /api/dashboard/metrics, /api/tenants
│   ├── models/
│   │   └── database.py      # ORM: Customer, Subscription, StripeEvent
│   └── services/
│       └── odoo_provisioner.py
├── templates/
│   └── admin_dashboard.html # UI + JS dinámico
├── docs/
│   └── ADMIN_DASHBOARD.md   # Este archivo
└── .github/
    └── copilot-instructions.md
```

---

## Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| 500 Internal Server Error en `/api/dashboard/metrics` | BD desconectada | Verificar `DATABASE_URL` en `.env` |
| Tabla vacía en dashboard | No hay registros en `subscriptions` | Crear clientes/suscripciones de prueba |
| CORS error en navegador | JS fetch rechazado | Agregar middleware CORS (si accedes desde otro dominio) |
| 404 en `/admin` | Template no existe | Verificar que `templates/admin_dashboard.html` existe |

---

## Autor & Versión

- **Versión**: 1.0.0 (MVP)
- **Fecha**: Enero 2026
- **Stack**: FastAPI + SQLAlchemy + Tailwind CSS + Vanilla JS
