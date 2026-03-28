# 05 - Dominios y Cloudflare

Estado: vigente  
Validado: 2026-03-28  
Entorno objetivo: `/opt/Erp_core`


## Objetivo
Registrar y activar dominios personalizados para tenants, configurando DNS/tunnel/nginx.

## Regla DNS vigente
- Subdominio interno SAJET del tenant: `*.sajet.us`, gestionado con Cloudflare/tunnel según el stack interno.
- Dominio externo del cliente: debe resolver hacia el frontend público de SAJET en `208.115.125.29`.
- Para apex/root domains usar `A` proxied a `208.115.125.29`.
- No usar `CNAME` externo a `*.sajet.us`.
- No usar `CNAME` externo a `*.cfargotunnel.com`.

## Disparador
- Frontend: `#/domains`
- API: `/api/domains/*`

## Secuencia ASCII

```text
[SPA Domains]
   |
   | POST /api/domains
   v
[domains.py]
   |
   +--> valida tenant/customer
   +--> valida límite de dominios por plan (max_domains)
   +--> crea registro custom_domains
   v
[Activación]
   |
   +--> ensure sajet internal hostname/tunnel
   +--> validate external DNS -> 208.115.125.29
   +--> configure nginx route
   v
[domain verified + active]
```

## Endpoints frecuentes
- `GET /api/domains`
- `POST /api/domains`
- `POST /api/domains/{id}/verify`
- `POST /api/domains/{id}/configure-cloudflare`
- `POST /api/domains/{id}/configure-nginx`
- `POST /api/domains/{id}/activate`

## Errores típicos
- `403 límite de dominios alcanzado`
- DNS no propagado
- token Cloudflare sin permisos
- dominio externo publicado como `CNAME -> tenant.sajet.us`
- dominio externo publicado como `CNAME -> <tunnel>.cfargotunnel.com`

## Runtime config
- `cloudflare_manager.py`, `domain_manager.py` y `provisioning.py` ya usan lectura runtime DB-first para Cloudflare y provisioning críticos.
- Claves migradas: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_ZONE_ID`, `CLOUDFLARE_ZONES`, `CLOUDFLARE_TUNNEL_ID`, `PROVISIONING_API_KEY`, `ODOO_PRIMARY_IP`, `ERP_CORE_PUBLIC_IP`.
