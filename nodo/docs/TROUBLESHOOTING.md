# Troubleshooting - Nodo Odoo Multi-Tenant

Estado: vigente  
Validado: 2026-02-22

## 1) API local no responde (`:8070`)

Verificar servicio:

```bash
sudo systemctl status odoo-local-api
sudo journalctl -u odoo-local-api -f
```

Validar puerto:

```bash
ss -tulpen | grep 8070
curl -sS http://127.0.0.1:8070/health
```

## 2) Error de API key en provisioning

Confirmar que `PROVISIONING_API_KEY` coincide entre:

- Nodo: `/opt/nodo/config/.env`
- ERP Core: `.env` / `.env.production`

Reiniciar servicios despues de cambiar variables:

```bash
sudo systemctl restart odoo-local-api
sudo systemctl restart odoo-db-watcher
```

## 3) No se crea DNS en Cloudflare

Revisar credenciales y permisos de token.

```bash
sudo journalctl -u odoo-db-watcher -f
cat /opt/nodo/cloudflare/domains.json
```

Permisos minimos del token:

- Zone DNS Edit
- Account Tunnel (si aplica al flujo)

## 4) Tenant creado pero Odoo no abre

Checklist:

1. Base de datos existe en PostgreSQL
2. Odoo esta activo
3. Nginx/ingress apunta al tenant correcto
4. DNS o tunnel resuelve

Comandos utiles:

```bash
sudo systemctl status odoo
sudo -u postgres psql -c "\l" | grep <subdomain>
curl -I https://<subdomain>.sajet.us/web/login
```

## 5) Suspension/reactivacion no impacta usuarios

Verificar ejecucion del endpoint desde ERP Core y logs de worker local.

```bash
curl -X PUT http://127.0.0.1:4443/api/provisioning/tenant/suspend \
  -H "X-API-KEY: <api-key>" \
  -H "Content-Type: application/json" \
  -d '{"subdomain":"demo","suspend":true}'
```

## Referencias

- `nodo/docs/README.md`
- `nodo/docs/API.md`
- `nodo/docs/TENANT_MANAGEMENT.md`
