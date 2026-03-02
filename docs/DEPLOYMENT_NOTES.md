# Notas de Despliegue - ERP Core

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core` (perfil PCT160)

## Topologia objetivo

- Aplicacion FastAPI escuchando en puerto `4443`
- SPA compilada en `static/spa/` y servida por el backend
- Base de datos PostgreSQL configurada desde `.env.production`
- Servicio principal esperado: `erp-core` (systemd)

## Estructura recomendada en servidor

```text
/opt/Erp_core/
├── app/
├── frontend/
├── static/spa/
├── scripts/
├── docs/
├── requirements.txt
└── .env.production
```

## Flujo de deploy recomendado

Desde el repositorio local:

```bash
cd /opt/Erp_core
./scripts/deploy_to_server.sh --profile pct160
```

Opciones utiles:

- Simular sin cambios remotos:

```bash
./scripts/deploy_to_server.sh --profile pct160 --dry-run
```

- Omitir build local de SPA:

```bash
./scripts/deploy_to_server.sh --profile pct160 --skip-build
```

## Variables de entorno usadas por el deploy

- `SERVER_USER`
- `SERVER_HOST`
- `SERVER_PATH` (default: `/opt/Erp_core`)
- `SSH_PORT` (default: `22`)
- `SSH_KEY` (opcional)
- `APP_SERVICE` (ej. `erp-core`)
- `APP_BASE_URL` (default: `http://127.0.0.1:4443`)

Con `--profile pct160` se aplican defaults:

- `SERVER_USER=root`
- `SERVER_HOST=${PCT160_HOST:-pct160}`
- `SERVER_PATH=/opt/Erp_core`
- `APP_SERVICE=erp-core`

## Verificacion post-deploy

Smoke tests:

```bash
cd /opt/Erp_core
APP_BASE_URL=http://127.0.0.1:4443 ./scripts/smoke_pct160.sh
```

Validaciones manuales:

```bash
curl -sS http://127.0.0.1:4443/health
curl -sS http://127.0.0.1:4443/api/env
```

## Operacion del servicio

```bash
sudo systemctl status erp-core
sudo systemctl restart erp-core
sudo journalctl -u erp-core -f
```

## Errores frecuentes

1. `npm run check` falla durante build  
   Revisar tipos en `frontend/src/` antes de desplegar.

2. `smoke_pct160.sh` falla en login  
   Confirmar `ADMIN_USERNAME` y `ADMIN_PASSWORD` del entorno activo.

3. Fallo de conexion DB  
   Verificar `DATABASE_URL` o `DB_*` en `.env.production`.

4. CORS bloquea peticiones del frontend  
   Ajustar `ALLOWED_ORIGINS` o `ALLOWED_ORIGIN_REGEX`.

## Referencias

- `README.md`
- `scripts/deploy_to_server.sh`
- `scripts/build_static.sh`
- `scripts/smoke_pct160.sh`
- `docs/05-deploy-operacion/DEPLOYMENT_RUNBOOK.md`
