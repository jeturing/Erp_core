# 05 - Dominios y Cloudflare

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


## Objetivo
Registrar y activar dominios personalizados para tenants, configurando DNS/tunnel/nginx.

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
   +--> configure cloudflare DNS
   +--> configure tunnel ingress
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
