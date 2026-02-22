# Flujos funcionales detallados

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core` (PCT160 + PCT105)

Este indice organiza los flujos operativos principales del producto en formato ejecutable para soporte, QA y desarrollo.

## Mapa de flujos

1. [01-auth-login-jwt](01-auth-login-jwt/README.md)
2. [02-tenants-listado-y-gestion](02-tenants-listado-y-gestion/README.md)
3. [03-provisioning-template-pct105](03-provisioning-template-pct105/README.md)
4. [04-billing-stripe](04-billing-stripe/README.md)
5. [04-joficreditosrd-loan-module](04-joficreditosrd-loan-module/README.md)
6. [05-dominios-cloudflare](05-dominios-cloudflare/README.md)
7. [06-infraestructura-proxmox](06-infraestructura-proxmox/README.md)
8. [07-tenant-portal](07-tenant-portal/README.md)
9. [08-clientes-stripe-email](08-clientes-stripe-email/README.md)
10. [09-ecosistema-partners](09-ecosistema-partners/README.md)
11. [10-deploy-operacion-pct160](10-deploy-operacion-pct160/README.md)

## Convenciones

Cada flujo debe documentar:

- objetivo funcional
- disparadores frontend/backend
- endpoints implicados
- modelos o servicios impactados
- secuencia de ejecucion
- errores comunes y diagnostico rapido

## Fuente de verdad

- Arquitectura general: `README.md`
- Indice documental: `docs/INDICE.md`
