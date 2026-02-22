# Cloudflare - Operacion de dominios y tunnels

Estado: vigente  
Validado: 2026-02-22

Este directorio contiene utilidades para operar DNS/tunnels de tenants Odoo.

## Archivos del directorio

- `Cloudflare/cf_manager.sh` - CLI interactiva para operaciones de tunnel
- `Cloudflare/create_tenant.sh` - script base de creacion de tenant
- `Cloudflare/create_tenant_enhanced.sh` - variante extendida para provisioning integrado
- `Cloudflare/cc.sh` - utilidades operativas adicionales
- `Cloudflare/dominios.json` - catalogo de dominios/zonas
- `Cloudflare/.cf_credentials` - credenciales locales (no usar en repositorio publico)

## Integracion con ERP Core

Capas implicadas:

- Servicio backend: `app/services/cloudflare_manager.py`
- Gestion de dominios: `app/services/domain_manager.py`
- Endpoints API: `app/routes/domains.py` y `app/routes/tunnels.py`
- Provisioning: `app/services/odoo_provisioner.py`

## Flujo operativo resumido

1. Se crea o actualiza dominio desde API (`/api/domains`)
2. El backend sincroniza estado en base de datos
3. Scripts de sincronizacion aplican DNS/tunnel ingress
4. El tenant queda accesible por dominio externo y fallback `*.sajet.us`

## Validaciones recomendadas

```bash
# Estado de tunnels
cloudflared tunnel list

# Validar endpoint backend
curl -sS http://127.0.0.1:4443/api/tunnels

# Verificar sync de dominios
bash scripts/domain_sync.sh
```

## Referencias

- `docs/04-domains-cloudflare/CLOUDFLARE_INTEGRATION.md`
- `docs/04-domains-cloudflare/CUSTOM_DOMAINS_ARCHITECTURE.md`
- `docs/04-domains-cloudflare/DOMAIN_AUTOMATION_FALLBACK.md`
- `docs/INDICE.md`
