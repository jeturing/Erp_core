# Automatización de dominios (BD + aplicación) con fallback `*.sajet.us`

## Objetivo
Automatizar el ciclo completo de dominios personalizados desde la base de datos de ERP Core y garantizar un **fallback estable** por subdominio `sajet.us`.

- Dominio externo principal (ej. `evolucionamujer.com`)
- Fallback interno (ej. `evolucionamujer.sajet.us`)

Si falla DNS externo, el tenant sigue disponible por `*.sajet.us`.

---

## Componentes

1. Servicio de aplicación: [app/services/domain_manager.py](app/services/domain_manager.py)
2. Endpoints API: [app/routes/domains.py](app/routes/domains.py)
3. Sincronizador operativo: [scripts/domain_sync.sh](scripts/domain_sync.sh)
4. Túnel Cloudflare en PCT 105:
   - Config: `/etc/cloudflared/tcs-sajet-tunnel.yml`
   - Servicio: `cloudflared-tcs-sajet-tunnel`

---

## Flujo automatizado

1. Admin crea dominio en API (`POST /api/domains`).
2. Se guarda en `custom_domains` (estado `pending`).
3. `domain_sync.sh` (timer cada 2 min):
   - crea CNAME en Cloudflare para `subdominio.sajet.us`
   - agrega ingress en tunnel para fallback `subdominio.sajet.us`
   - si `external_domain` está `verified` + `is_active=true`, agrega también ingress del externo
4. Se recarga cloudflared con validación previa.
5. Tenant queda accesible por externo y por fallback `*.sajet.us`.

---

## Comportamiento de fallback

- **Siempre** se mantiene ruta por `subdominio.sajet.us`.
- El externo se publica cuando está verificado.
- Si externo cae, se usa el fallback interno sin afectar operación.

---

## Instalación del scheduler (PCT 105)

Se instaló:
- `/opt/scripts/domain_sync.sh`
- `/etc/systemd/system/domain-sync.service`
- `/etc/systemd/system/domain-sync.timer`

Frecuencia:
- `OnUnitActiveSec=2min`

Comandos de operación:

- Estado timer:
  - `systemctl status domain-sync.timer`
- Ejecutar manual:
  - `systemctl start domain-sync.service`
- Ver logs:
  - `tail -f /var/log/domain_sync.log`
  - `journalctl -u domain-sync.service -f`

---

## DNS requerido en dominios externos

Cada dominio externo debe apuntar al túnel:

- Target:
  - `da2bc763-a93b-41f5-9a22-1731403127e3.cfargotunnel.com`

Registros recomendados por zona:
- `@` CNAME -> target del tunnel (proxied)
- `www` CNAME -> `@` (o al mismo target)

---

## Nginx / routing

Nginx en PCT 105 ya mapea dominios externos a tenant `techeels` y redirige a:

- `https://<dominio>/web?db=techeels`

Archivo operativo:
- `/etc/nginx/sites-enabled/odoo`

---

## CORS (ERP Core)

Se ampliaron orígenes permitidos en [app/main.py](app/main.py) para:
- `sajet.us` y subdominios
- `techeels.io`, `evolucionamujer.com`, `impulse-max.com` (incluyendo `www`)

Variables sugeridas:
- `ALLOWED_ORIGINS`
- `ALLOWED_ORIGIN_REGEX`

---

## Validaciones de salud

Checklist rápido:

1. Odoo
   - `systemctl is-active odoo`
2. Tunnel
   - `systemctl is-active cloudflared-tcs-sajet-tunnel`
3. Sync timer
   - `systemctl is-active domain-sync.timer`
4. Pruebas internas por Host header
   - `curl -H "Host: techeels.sajet.us" http://127.0.0.1:8080/web`
5. Pruebas externas HTTPS
   - `curl -I https://techeels.sajet.us/web/login`

---

## Notas operativas

- `custom_domains.external_domain` debe ser único y válido.
- Mantener `cloudflare_configured` y `tunnel_ingress_configured` como fuente de verdad de despliegue.
- No desactivar fallback `*.sajet.us`; es la ruta de continuidad de negocio.
