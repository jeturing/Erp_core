# ARQUITECTURA OPERATIVA MAESTRA

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: PCT160 (10.10.10.20) + PCT105 (10.10.10.100)

## Diagrama maestro (mapa operativo)

```text
┌──────────────────────────────┐
│ 01) AUTH / LOGIN (JWT)       │
│ - POST /api/auth/login       │
│ - access + refresh token     │
└──────────────┬───────────────┘
               v
┌──────────────────────────────┐
│ 02) TENANTS LIST / MANAGE    │
│ - GET/POST/DELETE /api/tenants
│ - suspend/password ops       │
└──────────────┬───────────────┘
               v
┌──────────────────────────────┐         ┌──────────────────────────────┐
│ 03) PROVISIONING PCT105      │<------->│ PostgreSQL/Odoo (PCT105)     │
│ - clone template_tenant      │         │ - CREATE DB FROM TEMPLATE     │
│ - post-config tenant         │         │ - config company/base_url     │
└──────────────┬───────────────┘         └──────────────────────────────┘
               v
┌──────────────────────────────┐         ┌──────────────────────────────┐
│ 04) BILLING + STRIPE         │<------->│ Stripe                        │
│ - métricas/facturas/eventos  │         │ - checkout/webhooks/invoices  │
└──────────────┬───────────────┘         └──────────────────────────────┘
               v
┌──────────────────────────────┐         ┌──────────────────────────────┐
│ 05) DOMAINS + CLOUDFLARE     │<------->│ Cloudflare                    │
│ - DNS/tunnel/nginx           │         │ - edge + propagación          │
└──────────────┬───────────────┘         └──────────────────────────────┘
               v
┌──────────────────────────────┐         ┌──────────────────────────────┐
│ 06) INFRAESTRUCTURA PROXMOX  │<------->│ Proxmox Cluster               │
│ - nodos/containers/status    │         │ - recursos lifecycle          │
└──────────────┬───────────────┘         └──────────────────────────────┘
               v
┌──────────────────────────────┐
│ 07) TENANT PORTAL            │
│ - /tenant/portal + /tenant/api/*
└──────────────┬───────────────┘
               v
┌──────────────────────────────┐         ┌──────────────────────────────┐
│ 08) CLIENTES + STRIPE + MAIL │<------->│ SMTP + Stripe Customer        │
│ - create customer / reset    │         │ - notificaciones y cobro      │
└──────────────┬───────────────┘         └──────────────────────────────┘
               v
┌──────────────────────────────┐         ┌──────────────────────────────┐
│ 09) ECOSISTEMA PARTNERS      │<------->│ Stripe Connect (opcional)     │
│ - leads/comisiones/quotes    │         │ - onboarding/payout/split     │
└──────────────┬───────────────┘         └──────────────────────────────┘
               v
┌──────────────────────────────┐         ┌──────────────────────────────┐
│ 10) DEPLOY OPS PCT160        │<------->│ Runtime PCT160                │
│ - build/copy/restart/smoke   │         │ - erp-core.service + SPA      │
└──────────────────────────────┘         └──────────────────────────────┘