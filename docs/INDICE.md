# INDICE DOCUMENTAL VIGENTE

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core` (PCT160 + PCT105)
Auditoria documental: 2026-02-22 (sin enlaces internos rotos)

Este documento es la entrada oficial para navegar la documentacion de `Erp_core`.

## 1) Documentos troncales

- `README.md` - vision global, arquitectura, setup, deploy y comandos base
- `DEPLOYMENT_NOTES.md` - notas operativas de despliegue y verificacion
- `PR_TRACKER.md` - seguimiento de epicas y estado operativo del producto

## 2) Documentacion por dominio (`docs/`)

### 2.1 Base (`docs/00-base/`)

- `docs/00-base/ARQUITECTURA_OPERATIVA_MAESTRA.md`
- `docs/00-base/COMBINACIONES_PAQUETES_INDUSTRIA_MERCADOS_ODOO_17.md`
- `docs/00-base/IMPLEMENTATION_PLAN.md`
- `docs/00-base/IMPLEMENTATION_SUMMARY.md`
- `docs/00-base/INTEGRATION_SUMMARY.md`
- `docs/00-base/MODULAR_ARCHITECTURE.md`
- `docs/00-base/MODULOS_DISPONIBLES_ODOO_17.md`

### 2.2 Frontend (`docs/01-frontend/`)

- `docs/01-frontend/ADMIN_DASHBOARD.md`
- `docs/01-frontend/DELIVERABLES.md`
- `docs/01-frontend/INTEGRATION_ROADMAP.md`

### 2.3 Seguridad y Auth (`docs/02-security-auth/`)

- `docs/02-security-auth/API_AUDIT.md`
- `docs/02-security-auth/JWT_AUTHENTICATION.md`
- `docs/02-security-auth/JWT_COMPLETE.md`
- `docs/02-security-auth/JWT_IMPLEMENTATION_SUMMARY.md`
- `docs/02-security-auth/JWT_QUICKSTART.md`
- `docs/02-security-auth/PARAMETER_VALIDATION.md`
- `docs/02-security-auth/ROLES_PERMISOS_MATRIZ.md`
- `docs/02-security-auth/SECURITY.md`
- `docs/02-security-auth/SECURITY_REMEDIATION_COMPLETE.md`

### 2.4 Tenants y Provisioning (`docs/03-tenants-provisioning/`)

- `docs/03-tenants-provisioning/EJEMPLOS_USO.md`
- `docs/03-tenants-provisioning/ONBOARDING_PUBLICO_SIN_PRECIOS.md`
- `docs/03-tenants-provisioning/PROVISIONER_REFACTOR.md`
- `docs/03-tenants-provisioning/PR_TEMPLATE_ONBOARDING_PARTNER.md`
- `docs/03-tenants-provisioning/TENANT_MANAGEMENT_README.md`
- `docs/03-tenants-provisioning/TENANT_MANAGEMENT_SETUP.md`

### 2.5 Dominios y Cloudflare (`docs/04-domains-cloudflare/`)

- `docs/04-domains-cloudflare/CLOUDFLARE_AUTH_PENDING.md`
- `docs/04-domains-cloudflare/CLOUDFLARE_INTEGRATION.md`
- `docs/04-domains-cloudflare/CLOUDFLARE_QUICKREF.md`
- `docs/04-domains-cloudflare/CLOUDFLARE_SETUP.md`
- `docs/04-domains-cloudflare/CLOUDFLARE_SUMMARY.md`
- `docs/04-domains-cloudflare/CLOUDFLARE_TOKEN_SETUP.md`
- `docs/04-domains-cloudflare/CLOUDFLARE_TUNNEL_CONFIG_DEPLOYED.md`
- `docs/04-domains-cloudflare/CLOUDFLARE_TUNNEL_IMPLEMENTATION.md`
- `docs/04-domains-cloudflare/CUSTOM_DOMAINS_ARCHITECTURE.md`
- `docs/04-domains-cloudflare/CUSTOM_DOMAINS_HOWTO.md`
- `docs/04-domains-cloudflare/DNS_SETUP_GUIDE_CLIENTS.md`
- `docs/04-domains-cloudflare/DOMAIN_AUTOMATION_FALLBACK.md`

### 2.6 Deploy y operacion (`docs/05-deploy-operacion/`)

- `docs/05-deploy-operacion/DELIVERY_PCT160.md`
- `docs/05-deploy-operacion/DEPLOYMENT.md`
- `docs/05-deploy-operacion/DEPLOYMENT_RUNBOOK.md`
- `docs/05-deploy-operacion/VALIDACION_NO_REGRESION.md`

### 2.7 Migracion Odoo (`docs/06-migracion-odoo/`)

- `docs/06-migracion-odoo/BULK_MIGRATION_GUIDE.md`
- `docs/06-migracion-odoo/INSTALL_ODOO19_README.md`
- `docs/06-migracion-odoo/MIGRATION_COMPLETION_REPORT.md`
- `docs/06-migracion-odoo/ODOO_MIGRATION_SUMMARY.md`
- `docs/06-migracion-odoo/ODOO_MIGRATION_TOOL_README.md`
- `docs/06-migracion-odoo/ODOO_MIGRATION_V17_TO_V19.md`
- `docs/06-migracion-odoo/QUICK_START_MIGRATION.md`
- `docs/06-migracion-odoo/README_MIGRATION.md`
- `docs/06-migracion-odoo/SKILLS_OCA_SETUP.md`

### 2.8 Reportes de cierre (`docs/07-reportes-cierre/`)

- `docs/07-reportes-cierre/FINAL_SUMMARY.md`
- `docs/07-reportes-cierre/PHASE3_DELIVERY_SUMMARY.md`
- `docs/07-reportes-cierre/PROJECT_CLOSURE_PHASE3.md`
- `docs/07-reportes-cierre/RESUMEN_EJECUTIVO_PHASE_3.md`
- `docs/07-reportes-cierre/SPRINT_COMPLETION_SUMMARY.md`
- `docs/07-reportes-cierre/WHAT_WAS_COMPLETED.md`

### 2.9 Tooling interno (`docs/08-tooling-interno/`)

- `docs/08-tooling-interno/INSTALLAR_SKILLS_VSCODE.md`
- `docs/08-tooling-interno/TAILSCALE_ARCHITECTURE.md`
- `docs/08-tooling-interno/TODO.md`
- `docs/08-tooling-interno/TODO_fixed.md`

### 2.10 Historico (`docs/09-historico/`)

- `docs/09-historico/INDICE_PHASE3.md`

## 3) Flujos funcionales (`docs/flujos/`)

- `docs/flujos/README.md`
- `docs/flujos/01-auth-login-jwt/README.md`
- `docs/flujos/02-tenants-listado-y-gestion/README.md`
- `docs/flujos/03-provisioning-template-pct105/README.md`
- `docs/flujos/04-billing-stripe/README.md`
- `docs/flujos/04-joficreditosrd-loan-module/README.md`
- `docs/flujos/05-dominios-cloudflare/README.md`
- `docs/flujos/06-infraestructura-proxmox/README.md`
- `docs/flujos/07-tenant-portal/README.md`
- `docs/flujos/08-clientes-stripe-email/README.md`
- `docs/flujos/09-ecosistema-partners/README.md`
- `docs/flujos/10-deploy-operacion-pct160/README.md`

## 4) Otros repositorios internos de documentacion

- `Cloudflare/README.md`
- `frontend/README.md`
- `migration_reports/MASTER_MIGRATION_REPORT.md`
- `nodo/INDEX.md`
- `nodo/QUICKSTART.md`
- `nodo/REFERENCIA_RAPIDA.md`
- `nodo/RESUMEN_EJECUTIVO.md`
- `nodo/MANIFEST.md`
- `nodo/docs/README.md`
- `nodo/docs/API.md`
- `nodo/docs/TENANT_MANAGEMENT.md`

## Criterio de validez documental

Un documento se considera vigente cuando:

- apunta a rutas/archivos existentes en `/opt/Erp_core`
- describe endpoints o procesos implementados en codigo
- indica fecha de validacion coherente con el estado actual
