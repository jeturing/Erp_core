# Copilot Instructions — SAJET ERP Core

> **OBLIGATORIO**: Antes de cualquier tarea, leer `/opt/AGENTE.md` y `/opt/CLAUDE.md`.
> Codename: **SAJET** · Repo: `Erp_core` · PCT: 160 · Dominio: `sajet.us`

## Arquitectura

```
FastAPI (:4443) ─── SQLAlchemy ORM ─── PostgreSQL (erp_core_db @ PCT 137, 10.10.10.137:5432)
     │                                        │
     ├── Security Layer (CORS dinámico, JWT httpOnly, TOTP, Email Verify)
     ├── 35+ routers (app/routes/*.py)
     └── Svelte 5 SPA (frontend/) → build a static/spa/
                                          │
                        Provisioning ──── PCT 105/161 (Odoo tenants)
                                          │
                        Stripe Connect ── Split 50/50 partners
```

- **Backend**: `app/main.py` → 35+ routers, `app/models/database.py` → 50+ modelos SQLAlchemy
- **Frontend**: Svelte 5 (runes mode) + TypeScript + Vite 7 + Tailwind CSS 3
- **Auth**: JWT cookies httpOnly → TOTP 2FA → Email Verify (Steam-style, configurable por rol)
- **Pagos**: Stripe Direct + Connect Express con split automático
- **i18n**: svelte-i18n (estático en/es) + CMS dinámico en BD (tablas `translations`, `landing_sections`)

## Reglas Específicas

### Base de datos
- `erp_core_db` **canónica/productiva** está en **PCT 137** (`10.10.10.137:5432`) — `DATABASE_URL` apunta ahí. PCT 160 tiene una instancia local (`127.0.0.1` only, 41 tablas) que es secundaria y NO se usa en producción. Confirmado 2026-03-27.
- Migraciones: Alembic (13+ versiones en `alembic/versions/`)
- Config centralizada: tabla `system_config` (34 registros, 6 categorías). Acceso: `get_config()` BD > .env > default

### Patrones de código backend
```python
# Async + type hints obligatorios
async def get_tenants(db: AsyncSession) -> list[Customer]:
    result = await db.execute(select(Customer))
    return result.scalars().all()

# Pydantic para validación
class TenantCreate(BaseModel):
    company_name: str
    email: EmailStr
    subdomain: str = Field(regex=r"^[a-z0-9-]+$")

# Response estándar
{"success": True, "data": {...}, "meta": {"total": 10, "page": 1}}
```

### Patrones de código frontend
```svelte
<!-- Svelte 5 runes mode + TypeScript + brand colors -->
<script lang="ts">
  import { t } from '$lib/i18n';
  let tenants = $state<Tenant[]>([]);
</script>
<div class="bg-[#0F1419] min-h-screen">
  <button class="bg-[#003B73] hover:bg-[#002952] text-white">{$t('actions.save')}</button>
</div>
```

- Imports tipados desde `lib/api/` (25+ módulos), stores en `lib/stores/`
- Interfaces en `lib/types/` (500+ líneas)
- i18n keys en `lib/i18n/{en.json, es.json}` (185 keys)

### CORS dinámico
- Orígenes desde BD (`custom_domains` + `tenant_deployments`) con caché TTL 60s
- Refresh manual: `POST /api/admin/cors/refresh`
- Código: `app/security/cors_dynamic.py`

### Provisioning de tenants
- SAJET (PCT 160) orquesta la creación → LXC en PCT 105/161
- Flujo: crear BD en 137 → clonar template Odoo → crear tunnel Cloudflare → configurar nginx
- Archivos: `app/routes/provisioning.py`, `app/services/odoo_manager.py`

## Workflows

```bash
# Backend dev
cd /opt/Erp_core && source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload

# Frontend dev
cd frontend && npm run dev  # → localhost:5173

# Build + Deploy
./scripts/build_static.sh                    # SPA → static/spa/
./scripts/deploy_to_server.sh --profile pct160  # rsync a producción

# Tests
pytest -q && bash tests/test_jwt.sh

# Migraciones
alembic upgrade head
alembic revision --autogenerate -m "feat: descripcion"
```

## Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `app/main.py` | Entry point, 35+ routers registrados |
| `app/models/database.py` | 50+ modelos SQLAlchemy + enums |
| `app/config.py` | Configuración centralizada (env vars) |
| `app/security/cors_dynamic.py` | CORS desde BD con caché |
| `app/security/tokens.py` | JWT access + refresh rotation |
| `app/routes/secure_auth.py` | Login multi-step |
| `app/routes/provisioning.py` | Provisioning tenants |
| `frontend/src/lib/i18n/` | Diccionarios i18n |
| `frontend/src/lib/types/` | Interfaces TypeScript |
| `.env.production` | Referencia maestra de secrets |

## Política de Mantenimiento de Instrucciones

> **Regla:** Estas instrucciones son documentación viva. Toda instrucción debe ser funcional y verificada.

### Criterio de validez

Una instrucción es **válida** si cumple **los tres**:
1. Fue ejecutada o verificada contra el sistema real (no inferida ni asumida)
2. Resolvió o previno un problema concreto
3. Sigue siendo cierta en el estado actual del sistema

Una instrucción es **inválida** si:
- Describe un comportamiento que ya no existe o fue refutado con evidencia
- Contradice datos verificados vía MCP, terminal o archivo real
- Es ambigua al punto de generar confusión operativa

### Protocolo de actualización

| Evento | Acción obligatoria |
|--------|--------------------|
| Se resuelve un problema con causa raíz en estas instrucciones | **ACTUALIZAR** la regla afectada con fecha y evidencia |
| Se verifica que una regla es correcta | Agregar `✅ Verificado YYYY-MM-DD` en línea |
| Se detecta que una regla es falsa o desactualizada | **REEMPLAZAR** inmediatamente — no dejar la versión incorrecta comentada |
| Se introduce un nuevo patrón estable (≥2 usos exitosos) | **AGREGAR** la regla al bloque correspondiente |
| Una regla no puede verificarse ni aprobarse | **ELIMINAR** — no mantener reglas especulativas |

### Formato de evidencia

Cuando se actualice una regla por resolución de problema, agregar al final de la línea:
```
— Confirmado YYYY-MM-DD [método: MCP|terminal|archivo]
```

Ejemplo aplicado en este archivo:
```
- `erp_core_db` canónica en PCT 137 (`10.10.10.137:5432`) — Confirmado 2026-03-27 [método: MCP]
```

### Estado actual de instrucciones verificadas

| Regla | Estado | Fecha |
|-------|--------|-------|
| `DATABASE_URL` → PCT 137 (`10.10.10.137:5432`) | ✅ Verificado | 2026-03-27 |
| PCT 160 PG local es secundaria, `127.0.0.1` only | ✅ Verificado | 2026-03-27 |
| MCP profile `99987A51` conecta a `erp_core_db` en PCT 137 | ✅ Verificado | 2026-03-27 |
| `system_config` en BD con 34 registros, 6 categorías | ✅ Verificado | 2025-07-10 |
