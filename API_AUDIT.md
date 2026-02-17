# API Audit: Backend ↔ Frontend Connectivity

**Fecha:** 2026-02-17  
**Estado:** Merge completado de `affectionate-maxwell` → `feature/phase3-partner-led-onboarding`  
**Objetivo:** Auditar endpoints backend contra consumo frontend y detectar brecha de datos/APIs faltantes.

---

## 🔗 Resumen de Conectividad

| Dominio | Backend (FastAPI) | Frontend (Svelte) | Estado | Gap |
|---------|---|---|---|---|
| **Autenticación** | `/api/auth/*`, `/api/secure_auth/*`, `/api/roles/*` | `auth.ts`, `stores/auth.ts` | ✅ Conectado | Ninguno |
| **Dashboard** | `/api/dashboard/metrics` | `dashboard.ts` | ✅ Conectado | Falta endpoint `all` consolidado |
| **Tenants** | `/api/tenants/*` | `tenants.ts` | ✅ Conectado | Status handlers incompletos |
| **Billing** | `/api/billing/*` | `billing.ts` | ✅ Conectado | Comparación MoM missing |
| **Infrastructure** | `/api/nodes/*`, `/api/proxmox/*` | `infrastructure.ts` | ⚠️ Parcial | Mapeo de recursos incompleto |
| **Settings** | `/api/settings/*` | `settings.ts` | ✅ Conectado | Validación de permisos |
| **Logs** | `/api/logs/*` | `logs.ts` | ✅ Conectado | Filtros avanzados |
| **Tunnels** | `/api/tunnels/*` | `tunnels.ts` | ✅ Conectado | Sincronización Cloudflare |
| **Roles** | `/api/roles/*` | `roles.ts` | ✅ Conectado | RBAC matrix completa |
| **Portal Tenant** | `/tenant/api/info`, `/tenant/api/billing` | `portal.ts` | ⚠️ Parcial | Implementar endpoints |

---

## 📋 Endpoints Backend Disponibles (Completo)

### 1. Autenticación y Roles
```
POST   /api/auth/login                  → LoginRequest → LoginResponse (JWT)
POST   /api/secure_auth/register         → UserRegister → RegisterResponse
POST   /api/secure_auth/login            → LoginRequest + TOTP → LoginResponse
POST   /api/secure_auth/refresh-token    → RefreshRequest → RefreshResponse
POST   /api/secure_auth/logout           → (revoke token)
POST   /api/roles/login                  → RoleLoginRequest → RoleLoginResponse
GET    /api/roles/list                   → → List[Role]
```

### 2. Dashboard
```
GET    /api/dashboard/metrics            → → DashboardMetrics
  (retorna: tenants, mrr, churn, cluster load) ← MÍNIMO
GET    /api/dashboard/all                → → CompleteSnapshot  ← FALTA implementar
```

### 3. Tenants
```
GET    /api/tenants                      → [?limit, ?page] → List[Tenant]
POST   /api/tenants                      → TenantCreate → Tenant (provisiona)
GET    /api/tenants/{id}                 → → Tenant
PUT    /api/tenants/{id}                 → TenantUpdate → Tenant
DELETE /api/tenants/{id}                 → → { success: true }
PUT    /api/tenants/{id}/suspend         → → Tenant (status=suspended)
PUT    /api/tenants/{id}/reactivate      → → Tenant (status=active)
GET    /api/tenants/servers              → → ServerStatus[] (capacidad Odoo)
```

### 4. Billing
```
GET    /api/billing/metrics              → → BillingMetrics (MRR, revenue, churn)
GET    /api/billing/invoices             → [?limit] → List[Invoice]
GET    /api/billing/comparison           → → MoMComparison (mes actual vs anterior)
```

### 5. Infrastructure (Nodes/Proxmox)
```
GET    /api/nodes                        → → List[ProxmoxNode]
GET    /api/nodes/{id}/resources         → → NodeResources (CPU, RAM, Disk)
GET    /api/proxmox/containers           → → List[LXCContainer]
GET    /api/proxmox/metrics/{vmid}       → → ContainerMetrics (histórico)
```

### 6. Settings
```
GET    /api/settings/odoo/current        → → OdooConfig
POST   /api/settings/odoo/update         → OdooConfigUpdate → OdooConfig
GET    /api/settings/system              → → SystemSettings
POST   /api/settings/system/update       → SystemSettingsUpdate → SystemSettings
```

### 7. Logs
```
GET    /api/logs/provisioning            → [?limit, ?filter] → List[ProvisioningLog]
GET    /api/logs/status                  → → ServiceHealth
GET    /api/logs/audit                   → [?limit] → List[AuditLog]
```

### 8. Tunnels (Cloudflare)
```
GET    /api/tunnels                      → → List[CloudflareTunnel]
POST   /api/tunnels                      → TunnelCreate → CloudflareTunnel
DELETE /api/tunnels/{id}                 → → { success: true }
GET    /api/tunnels/{id}/dns             → → DNSRecords[]
```

### 9. Portal Tenant (sin autenticación admin)
```
GET    /tenant/api/info                  → → TenantPortalInfo
GET    /tenant/api/billing               → → TenantPortalBilling
POST   /tenant/api/update-payment        → → { checkout_url, message }
POST   /tenant/api/cancel-subscription   → → { message }
```

---

## 🎨 Frontend API Calls (Svelte)

| Archivo | Métodos Implementados | Status |
|---------|---|---|
| `lib/api/client.ts` | GET, POST, PUT, DELETE, PATCH | ✅ Completo |
| `lib/api/auth.ts` | login, register, logout, refresh | ✅ Completo |
| `lib/api/dashboard.ts` | getMetrics | ⚠️ Falta `getAll` |
| `lib/api/tenants.ts` | list, create, update, delete, suspend, reactivate | ✅ Completo |
| `lib/api/billing.ts` | getMetrics, getInvoices, getComparison | ✅ Completo |
| `lib/api/infrastructure.ts` | getNodes, getContainers, getMetrics | ⚠️ Incompleto |
| `lib/api/settings.ts` | get, update (odoo, system) | ✅ Completo |
| `lib/api/logs.ts` | getProvisioning, getStatus, getAudit | ✅ Completo |
| `lib/api/tunnels.ts` | list, create, delete, getDns | ✅ Completo |
| `lib/api/roles.ts` | login, list | ✅ Completo |
| `lib/api/portal.ts` | getInfo, getBilling, updatePayment, cancel | ✅ Completo |

---

## ⚠️ Brechas Detectadas

### Critical (Bloquean funcionalidad)
1. **`/api/dashboard/all`** → Frontend `Dashboard.svelte` necesita endpoint consolidado para cargar métricas + tenants + cluster en 1 call
   - **Solución:** Implementar endpoint que agrupe dashboard/metrics + tenants/list + infrastructure/nodes
   - **Prioridad:** Alta (Performance)

2. **Infrastructure metrics** → `infrastructure.ts` incompleto vs `/api/nodes/` y `/api/proxmox/containers`
   - **Gap:** Falta mapeo detallado de CPU/RAM/Disk por container
   - **Solución:** Completar `infrastructure.ts` con métodos para cada tipo de recurso

### Medium (Mejoras funcionales)
3. **Billing comparison MoM** → Implementado en backend pero frontend no consume
   - **Solución:** Conectar `Billing.svelte` a `billingApi.getComparison()`

4. **Audit logs** → Backend `GET /api/logs/audit` existe pero frontend no lo usa aún
   - **Solución:** Crear página de Audit Log o integrar en Settings

5. **Tenant status handlers** → Suspend/Reactivate implementados pero sin feedback visual
   - **Solución:** Agregar toast notifications y polling de estado

### Low (Nice-to-have)
6. **Proxy/cache de Odoo** → No hay endpoint para verificar estado de instancia Odoo después de provisión
   - **Solución:** Agregar `/api/tenants/{id}/odoo-status` para health check

---

## ✅ To-Do por Orden de Prioridad

### Sprint 1 (Esta semana)
- [ ] Implementar `GET /api/dashboard/all` en backend (`dashboard.py`)
- [ ] Actualizar `Dashboard.svelte` para usar nuevo endpoint consolidado
- [ ] Completar `infrastructure.ts` con métodos faltantes

### Sprint 2
- [ ] Conectar `Billing.svelte` a `billingApi.getComparison()`
- [ ] Agregar toast notifications en `tenants.ts` para suspend/reactivate
- [ ] Crear página de Audit Log (`pages/Audit.svelte`)

### Sprint 3
- [ ] Implementar health check Odoo en backend
- [ ] Mejorar error handling y retry logic en `client.ts`
- [ ] Agregar validación de permisos (RBAC) en todas las llamadas

---

## 📊 Matriz de Verificación

Usar esta matriz para QA antes de cada release:

```
[ ] Todas las páginas frontend cargan sin errores 404 a APIs
[ ] Autenticación JWT + TOTP funciona end-to-end
[ ] Dashboard carga métricas reales dentro de 2 seg
[ ] Crear tenant provisiona Odoo y registra progreso
[ ] Suspend/reactivate actualiza estado inmediatamente
[ ] Billing muestra MRR y comparación MoM correcta
[ ] Logs muestran eventos ordenados por timestamp
[ ] Tunnels Cloudflare sincroniza sin pérdida de datos
[ ] Portal tenant carga sin permisos admin
[ ] Roles RBAC respetan restricciones por rol
```

---

## 🔧 Próximos Pasos

1. **Revisar checklist crítico** (dashboard/all endpoint)
2. **Crear sprint board** en GitHub/Jira con tareas por prioridad
3. **Ejecutar QA integración** antes de desplegar a staging
4. **Documentar datos mock** necesarios para desarrollo local
