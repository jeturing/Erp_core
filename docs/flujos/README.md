# Flujos funcionales detallados

Estado: vigente  
Validado: 2026-02-18  
Entorno objetivo: PCT160 (`10.10.10.20`) + PCT105 (`10.10.10.100`)

Esta carpeta organiza la documentación por flujo, separada por elemento funcional.

## Mapa de flujos

1. [01-auth-login-jwt](01-auth-login-jwt/README.md)
2. [02-tenants-listado-y-gestion](02-tenants-listado-y-gestion/README.md)
3. [03-provisioning-template-pct105](03-provisioning-template-pct105/README.md)
4. [04-billing-stripe](04-billing-stripe/README.md)
5. [05-dominios-cloudflare](05-dominios-cloudflare/README.md)
6. [06-infraestructura-proxmox](06-infraestructura-proxmox/README.md)
7. [07-tenant-portal](07-tenant-portal/README.md)
8. [08-clientes-stripe-email](08-clientes-stripe-email/README.md)
9. [09-ecosistema-partners](09-ecosistema-partners/README.md)
10. [10-deploy-operacion-pct160](10-deploy-operacion-pct160/README.md)

## Convenciones

- Cada carpeta contiene un `README.md` con:
  - objetivo
  - disparador en frontend/backend
  - secuencia ASCII
  - endpoints
  - modelos impactados
  - errores típicos y diagnóstico
  - validación operativa
- Los flujos describen el comportamiento actual implementado en código en `/opt/Erp_core`.
