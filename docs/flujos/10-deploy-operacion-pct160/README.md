# 10 - Deploy y operación en PCT160

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


## Objetivo
Describir flujo de despliegue seguro de backend/frontend y validaciones mínimas operativas.

## Secuencia ASCII

```text
[Dev repo /opt/Erp_core]
   |
   +--> build frontend (vite)
   +--> copiar static/spa a 10.10.10.20
   +--> copiar rutas/servicios backend cambiados
   +--> restart erp-core.service
   v
[PCT160 online]
   |
   +--> smoke: /health
   +--> smoke: /api/tenants
   +--> smoke: / (SPA shell)
   v
[sajet.us actualizado]
```

## Checklist post-deploy
1. `systemctl is-active erp-core.service` = active.
2. `/api/tenants` responde con `items`.
3. `static/spa/index.html` referencia bundle hash actual.
4. revisar `journalctl -u erp-core.service -n 100`.

## Alertas comunes
- caché browser/CDN con bundle viejo
- dependencia npm opcional faltante (Rollup)
- acceso DB bloqueado por `pg_hba.conf`
