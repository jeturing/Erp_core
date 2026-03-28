# Contratos SAJET — Tenants, Provisioning e Infra

Estado: vigente  
Validado: 2026-03-27  
Fuente de verdad: `app.main`, routers FastAPI en `app/routes/` y OpenAPI runtime.

Contratos de infraestructura operativa: tenants, provisioning, dominios, túneles, nodos y portal de tenant.

## Cobertura

- Contratos unicos documentados en este archivo: **111**
- Registros duplicados detectados en runtime dentro de este dominio: **0**
- Los duplicados se marcan en la columna `estado` para no inflar el inventario.

## Entradas y salidas

### `/api/provisioning/tenant`

Request body:

```json
{
  "subdomain": "techeels",
  "admin_password": "admin",
  "domain": "sajet.us",
  "server": "primary",
  "template_db": "template_tenant",
  "language": "es_DO"
}
```

Response esperada:

```json
{
  "success": true,
  "subdomain": "techeels",
  "url": "https://techeels.sajet.us",
  "message": "Tenant provisionado",
  "database": "techeels",
  "dns_created": true,
  "server": "primary"
}
```

### `/api/domains`

Request body:

```json
{
  "external_domain": "portal.techeels.com",
  "customer_id": 10,
  "tenant_deployment_id": 22
}
```

### `/tenant/api/*`

- Entrada: cookie `access_token` de tenant.
- Salida: datos del portal de tenant, facturación, usuarios, túnel, dominios y actualización de método de pago.

## Inventario /api/domains

Contratos unicos en este grupo: **21**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/domains | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| POST | /api/domains | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| POST | /api/domains/bulk/sync-cloudflare | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| POST | /api/domains/bulk/sync-nginx | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| GET | /api/domains/customers-with-plans | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| POST | /api/domains/early-verify | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| GET | /api/domains/export/tunnel-config | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| GET | /api/domains/linked-domains/{customer_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| GET | /api/domains/my-domains | cookie JWT tenant | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| GET | /api/domains/quota/{customer_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| DELETE | /api/domains/{domain_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| GET | /api/domains/{domain_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| PUT | /api/domains/{domain_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| POST | /api/domains/{domain_id}/activate | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| POST | /api/domains/{domain_id}/configure-cloudflare | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| POST | /api/domains/{domain_id}/configure-nginx | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| POST | /api/domains/{domain_id}/configure-odoo-website | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| POST | /api/domains/{domain_id}/deactivate | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| GET | /api/domains/{domain_id}/nginx-status | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| GET | /api/domains/{domain_id}/odoo-websites | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |
| POST | /api/domains/{domain_id}/verify | cookie JWT / rol aplicado | frontend/admin | FastAPI → domains.py | app/routes/domains.py | admin | activo |

## Inventario /api/env

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/env | cookie JWT / rol aplicado | frontend/admin | FastAPI → main.py | app/main.py | admin | activo |

## Inventario /api/logs

Contratos unicos en este grupo: **5**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/logs/app | cookie JWT / rol aplicado | frontend/admin | FastAPI → logs.py | app/routes/logs.py | admin | activo |
| GET | /api/logs/provisioning | cookie JWT / rol aplicado | frontend/admin | FastAPI → logs.py | app/routes/logs.py | admin | activo |
| GET | /api/logs/status | cookie JWT / rol aplicado | frontend/admin | FastAPI → logs.py | app/routes/logs.py | admin | activo |
| GET | /api/logs/system | cookie JWT / rol aplicado | frontend/admin | FastAPI → logs.py | app/routes/logs.py | admin | activo |
| POST | /api/logs/write | cookie JWT / rol aplicado | frontend/admin | FastAPI → logs.py | app/routes/logs.py | admin | activo |

## Inventario /api/monitoring

Contratos unicos en este grupo: **2**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/monitoring/dashboard | X-API-KEY | automation/ops | FastAPI → monitoring_dashboard.py | app/routes/monitoring_dashboard.py | admin | activo |
| POST | /api/monitoring/evaluate-and-alert | X-API-KEY | automation/ops | FastAPI → monitoring_dashboard.py | app/routes/monitoring_dashboard.py | admin | activo |

## Inventario /api/nodes

Contratos unicos en este grupo: **16**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/nodes | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| POST | /api/nodes | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| GET | /api/nodes/containers/all | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| POST | /api/nodes/health-check | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| POST | /api/nodes/health-check-all | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| GET | /api/nodes/metrics/history | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| GET | /api/nodes/metrics/scan | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| GET | /api/nodes/metrics/summary | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| POST | /api/nodes/provision | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| GET | /api/nodes/status | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| DELETE | /api/nodes/{node_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| GET | /api/nodes/{node_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| PUT | /api/nodes/{node_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| GET | /api/nodes/{node_id}/domains | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| GET | /api/nodes/{node_id}/live-stats | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |
| POST | /api/nodes/{node_id}/maintenance | cookie JWT / rol aplicado | frontend/admin | FastAPI → nodes.py | app/routes/nodes.py | admin | activo |

## Inventario /api/provisioning

Contratos unicos en este grupo: **15**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/provisioning/deployment-status | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| POST | /api/provisioning/dns | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| GET | /api/provisioning/domains | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| POST | /api/provisioning/repair-deployments | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| GET | /api/provisioning/servers | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| DELETE | /api/provisioning/tenant | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| POST | /api/provisioning/tenant | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| PUT | /api/provisioning/tenant/account/credentials | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| GET | /api/provisioning/tenant/accounts | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| POST | /api/provisioning/tenant/accounts/sync-seat-count | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| PUT | /api/provisioning/tenant/email | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| PUT | /api/provisioning/tenant/password | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| PUT | /api/provisioning/tenant/suspend | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| GET | /api/provisioning/tenants | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |
| POST | /api/provisioning/tenants/maintenance | X-API-KEY | automation/ops | FastAPI → provisioning.py | app/routes/provisioning.py | admin | activo |

## Inventario /api/storage-alerts

Contratos unicos en este grupo: **5**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/storage-alerts/active | X-API-KEY | automation/ops | FastAPI → storage_alerts.py | app/routes/storage_alerts.py | admin | activo |
| GET | /api/storage-alerts/customer/{customer_id} | X-API-KEY | automation/ops | FastAPI → storage_alerts.py | app/routes/storage_alerts.py | admin | activo |
| GET | /api/storage-alerts/evaluate | X-API-KEY | automation/ops | FastAPI → storage_alerts.py | app/routes/storage_alerts.py | admin | activo |
| GET | /api/storage-alerts/evaluate-all | X-API-KEY | automation/ops | FastAPI → storage_alerts.py | app/routes/storage_alerts.py | admin | activo |
| GET | /api/storage-alerts/summary | X-API-KEY | automation/ops | FastAPI → storage_alerts.py | app/routes/storage_alerts.py | admin | activo |

## Inventario /api/tenant-status

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/tenant-status/{subdomain} | cookie JWT / rol aplicado | frontend/admin | FastAPI → suspension.py | app/routes/suspension.py | admin | activo |

## Inventario /api/tenant-suspension

Contratos unicos en este grupo: **2**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| DELETE | /api/tenant-suspension/{subdomain} | cookie JWT / rol aplicado | frontend/admin | FastAPI → suspension.py | app/routes/suspension.py | admin | activo |
| POST | /api/tenant-suspension/{subdomain} | cookie JWT / rol aplicado | frontend/admin | FastAPI → suspension.py | app/routes/suspension.py | admin | activo |

## Inventario /api/tenant-suspensions

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/tenant-suspensions | cookie JWT / rol aplicado | frontend/admin | FastAPI → suspension.py | app/routes/suspension.py | admin | activo |

## Inventario /api/tenants

Contratos unicos en este grupo: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/tenants | cookie JWT / rol aplicado | frontend/admin | FastAPI → tenants.py | app/routes/tenants.py | admin | activo |
| POST | /api/tenants | cookie JWT / rol aplicado | frontend/admin | FastAPI → tenants.py | app/routes/tenants.py | admin | activo |
| GET | /api/tenants/servers | cookie JWT / rol aplicado | frontend/admin | FastAPI → tenants.py | app/routes/tenants.py | admin | activo |
| GET | /api/tenants/servers/{server_id}/databases | cookie JWT / rol aplicado | frontend/admin | FastAPI → tenants.py | app/routes/tenants.py | admin | activo |
| DELETE | /api/tenants/{subdomain} | cookie JWT / rol aplicado | frontend/admin | FastAPI → tenants.py | app/routes/tenants.py | admin | activo |
| GET | /api/tenants/{subdomain} | cookie JWT / rol aplicado | frontend/admin | FastAPI → tenants.py | app/routes/tenants.py | admin | activo |

## Inventario /api/tunnels

Contratos unicos en este grupo: **22**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/tunnels | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| POST | /api/tunnels | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/customer-map | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/customer/{customer_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/deployments/available | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/dns/records | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/domains/available | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| POST | /api/tunnels/provision-for-customer | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/subscription/{subscription_id}/tunnel | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| POST | /api/tunnels/sync-all | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| POST | /api/tunnels/sync-lifecycle/{subscription_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/verify/api-token | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| DELETE | /api/tunnels/{tunnel_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/{tunnel_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/{tunnel_id}/config | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| DELETE | /api/tunnels/{tunnel_id}/link | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| POST | /api/tunnels/{tunnel_id}/link | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| POST | /api/tunnels/{tunnel_id}/link-customer | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| POST | /api/tunnels/{tunnel_id}/link-stripe | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| POST | /api/tunnels/{tunnel_id}/restart | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/{tunnel_id}/status | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |
| GET | /api/tunnels/{tunnel_id}/token | cookie JWT / rol aplicado | frontend/admin | FastAPI → tunnels.py | app/routes/tunnels.py | admin | activo |

## Inventario /suspended

Contratos unicos en este grupo: **2**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /suspended/client | cookie JWT / rol aplicado | frontend/admin | FastAPI → suspension.py | app/routes/suspension.py | admin | activo |
| GET | /suspended/owner | cookie JWT / rol aplicado | frontend/admin | FastAPI → suspension.py | app/routes/suspension.py | admin | activo |

## Inventario /tenant/api

Contratos unicos en este grupo: **11**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /tenant/api/billing | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |
| POST | /tenant/api/cancel-subscription | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |
| POST | /tenant/api/change-password | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |
| GET | /tenant/api/info | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |
| GET | /tenant/api/invoices | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |
| POST | /tenant/api/invoices/{invoice_id}/pay | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |
| GET | /tenant/api/my-domains | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |
| POST | /tenant/api/request-domain | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |
| GET | /tenant/api/tunnel | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |
| POST | /tenant/api/update-payment | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |
| GET | /tenant/api/users | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | tenant, portal | activo |

## Inventario /tenant/portal

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /tenant/portal | cookie JWT tenant | portal tenant | FastAPI → tenant_portal.py | app/routes/tenant_portal.py | admin | activo |

## Puntos de quiebre

- `provisioning.py`: rompe si falla `X-API-KEY`, la API local Odoo, la BD Odoo, Cloudflare o la resolución del servidor (`primary`/nodos extra).
- `domains.py` y `domain_manager.py`: puntos de falla por cuota de plan, CNAME incorrecto, Cloudflare, Nginx, tunnel y asociación con `TenantDeployment`.
- `tunnels.py`, `nodes.py`, `tenants.py`: cualquier drift entre deployment real, subdomain, node IP y estado de suscripción desincroniza el tenant operativo.
- `tenant_portal.py`: el portal depende de que `Customer`, `Subscription`, `CustomDomain` y `Tunnel` estén consistentes.

## Observabilidad

- Logs y estado de sistema: `/api/logs/*`, `/api/monitoring/*`, `/api/nodes/status`, `/api/tunnels/*`.
- Dominios: `/api/domains/{id}/verify`, `/api/domains/{id}/nginx-status`, `/api/domains/export/tunnel-config`.
- Provisioning: `/api/provisioning/deployment-status`, `/api/provisioning/tenants`, `/api/tenants/{subdomain}`.
- La validación del sincronizador Odoo se cruza con este dominio porque `CustomDomain` y `TenantDeployment` son artefactos compartidos.
