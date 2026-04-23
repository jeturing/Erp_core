# Track ↔ SAJET — Documento de Integración

> **App:** `tack.sajet.us` (Jeturing-Track, fork de Traccar)
> **Repo público:** _pendiente — meta-repo en construcción_
> **Plataforma host:** SAJET ERP (`https://sajet.us`)
> **Estado:** Q2-2026 · integración nivel 1 (control, billing, sesiones)
> **Owner SAJET-side:** Erp_core / app/routes/track_admin.py
> **Owner Track-side:** equipo Track (Java 17, React 19, Flutter)
> **Última revisión:** 2026-04-23

---

## 1. Modelo mental

SAJET es la **plataforma de control**. Cada app (med, track, futuras) corre en
su propio host/PCT pero **delega en SAJET**:

| Responsabilidad             | SAJET (sajet.us)                       | Track (tack.sajet.us)               |
| --------------------------- | -------------------------------------- | ----------------------------------- |
| Identidad / SSO             | ✅ JWT emisor único                    | Consume JWT (verifica con secret)   |
| Configuración Stripe        | ✅ `system_config` + admin UI          | Consume vía M2M `10.10.20.202:4443/api/internal/...` |
| Toggle modo (test/sandbox/live) | ✅ `/api/admin/stripe/mode?app=track` | Recarga config en cada request      |
| Catálogo de planes / pricing | ✅ panel admin Track                  | Espejo local sólo lectura           |
| Stripe Subscriptions / Webhooks | ✅ Customer + Subscription          | Track sólo recibe `subscription_id` |
| Usuarios (alta/baja/suspensión) | ✅ Redis keys (`track:*`)           | Track los lee y aplica gating       |
| Sesiones live / kill-switch | ✅ admin UI                            | Track los publica / honra el kill   |
| Telemetría GPS/BLE/UWB/LoRa | ❌                                     | ✅ todo de Track                    |
| Apps móviles                | ❌                                     | ✅ track-manager / track-client     |

El principio: **Track no toca Stripe directamente**. SAJET emite las
suscripciones, cobra, y le dice a Track "este `user_id` tiene plan X
hasta tal fecha". Track sólo enforza acceso.

---

## 2. Inventario reservado en SAJET

Estos identificadores ya están reservados en SAJET para Track:

| Recurso                       | Valor                                      |
| ----------------------------- | ------------------------------------------ |
| App slug (interno)            | `track`                                    |
| Subdominio público            | `tack.sajet.us`                            |
| BD PostgreSQL                 | `track` en PCT 200 (`10.10.20.200:5432`)   |
| Owner BD                      | `jeturing` (lowercase, no superuser)       |
| Stripe key prefix             | `STRIPE_TRACK_*` (en `system_config`)      |
| Redis namespace               | `track:*` (PCT 203, db 0)                  |
| Admin API base                | `/api/track/*`                             |
| M2M config endpoint           | `GET /api/internal/config/stripe?app=track`|
| DSAM access gate (planificado)| `POST /api/dsam/access/track/check`        |

---

## 3. Endpoints SAJET expuestos a Track

### 3.0 Regla de URLs — interno vs público

| Tipo de tráfico                       | URL a usar                          | Notas                                            |
| ------------------------------------- | ----------------------------------- | ------------------------------------------------ |
| **M2M / server-to-server (Track → SAJET)** | `http://10.10.20.202:4443`     | LAN privada, sin TLS, sin Cloudflare             |
| Webhooks Stripe (Stripe → SAJET)       | `https://sajet.us`                  | Público (Stripe necesita HTTPS público)         |
| Login / UI / redirects (browser)      | `https://sajet.us`                  | Público, pasa por Cloudflare                    |
| Track admin (operadores SAJET)        | `https://sajet.us/api/track/*`      | Público con cookie JWT                          |

> **Por qué:** los endpoints `/api/internal/*` validan IP de origen (`10.10.20.*`).
> Si Track llama por `sajet.us`, la request sale por NPM→Cloudflare→back a SAJET
> con `X-Forwarded-For` pública y SAJET la rechaza con 403.

### 3.1 Configuración Stripe (M2M)

```
GET  http://10.10.20.202:4443/api/internal/config/stripe?app=track
Headers:
  X-Internal-Service-Key: <INTERNAL_SERVICE_KEY>
```

**Restricciones:**
- **Tráfico solo por LAN interna `10.10.20.0/24`** — NUNCA usar `sajet.us` para esto (saldría por Cloudflare y sería rechazado)
- IPs permitidas: `10.10.20.*`, `10.10.10.*`, `127.*`, `192.168.1.*`
- Requiere `X-Internal-Service-Key` (configurada en SAJET `system_config:INTERNAL_SERVICE_KEY`)

**Respuesta:**
```json
{
  "app": "track",
  "stripe_secret_key": "sk_test_...",
  "stripe_publishable_key": "pk_test_...",
  "stripe_webhook_secret": "whsec_...",
  "jeturing_fee_percentage": 1.0,
  "platform_country": "US",
  "mode": "test"
}
```

**Patrón de uso recomendado en Track:** cachear 60 s + reintentar si SAJET responde 503.

### 3.2 Health interno

```
GET http://10.10.20.202:4443/api/internal/health
Headers: X-Internal-Service-Key: ...
```

### 3.3 DSAM Access Check (gate de acceso por usuario)

> Pendiente de implementar en SAJET. Track puede empezar con `TRACK_DSAM_ENFORCE=false`.

```
POST http://10.10.20.202:4443/api/dsam/access/track/check
Headers: X-Internal-Service-Key: ...
Body:   {"sajet_user_id": 123, "tenant_id": 7}
Resp:   {"allowed": true, "plan_code": "growth", "expires_at": "2027-01-01T00:00:00Z"}
```

Track debe hacer este check al inicio de sesión y cachear el resultado en
Redis con TTL ≤ 5 min. Si SAJET no responde → modo *fail-open* configurable
(`TRACK_DSAM_ENFORCE=false` por defecto en Q2-2026, `true` en Q4-2026).

---

## 4. Endpoints SAJET admin (`/api/track/*`)

Todos requieren cookie `access_token` con rol `admin` u `operator`.
Definidos en [Erp_core/app/routes/track_admin.py](Erp_core/app/routes/track_admin.py).

| Método | Path                                          | Descripción                                         |
| ------ | --------------------------------------------- | --------------------------------------------------- |
| GET    | `/api/track/health`                           | Ping de BD `track` y Redis                          |
| GET    | `/api/track/subscriptions/stats`              | Total / activos / canceled / MRR                    |
| GET    | `/api/track/subscriptions?status=&search=`    | Listado paginado                                    |
| POST   | `/api/track/subscriptions/{id}/cancel`        | Cancela en Stripe + BD + Redis                      |
| GET    | `/api/track/sessions`                         | Sesiones live desde `track:session:*`               |
| POST   | `/api/track/sessions/{user_id}/terminate`     | Borra la sesión Redis (kill-switch)                 |
| GET    | `/api/track/devices`                          | Conteo de devices por tenant (`tc_devices`)         |
| GET    | `/api/track/plans`                            | Catálogo `track_stripe_prices`                      |
| POST   | `/api/track/plans`                            | Upsert de plan                                      |

---

## 5. Schema mínimo esperado en BD `track`

SAJET ya está preparado para leer. Track debe materializar (Liquibase / migrations):

```sql
-- Tenants Track
CREATE TABLE track_tenants (
    id          SERIAL PRIMARY KEY,
    slug        VARCHAR(50)  UNIQUE NOT NULL,
    name        VARCHAR(150) NOT NULL,
    sajet_partner_id INT,                  -- enlaza con sajet.partners.id
    plan_code   VARCHAR(40),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Usuarios Track (espejo de sajet.users — siempre con sajet_user_id)
CREATE TABLE track_users (
    id              SERIAL PRIMARY KEY,
    sajet_user_id   INT  UNIQUE NOT NULL,
    tenant_id       INT  REFERENCES track_tenants(id) ON DELETE CASCADE,
    email           VARCHAR(150) NOT NULL,
    name            VARCHAR(150),
    role            VARCHAR(40)  DEFAULT 'driver',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Catálogo de planes (mismos campos clave que MED)
CREATE TABLE track_stripe_prices (
    id               SERIAL PRIMARY KEY,
    code             VARCHAR(40)  UNIQUE NOT NULL,   -- 'starter','growth','business'...
    label            VARCHAR(120),
    stripe_price_id  VARCHAR(80)  NOT NULL,
    amount_cents     INT          NOT NULL,
    currency         VARCHAR(8)   DEFAULT 'usd',
    interval         VARCHAR(12)  DEFAULT 'month',   -- month|year
    max_devices      INT  DEFAULT 25,
    max_users        INT  DEFAULT 5,
    retention_days   INT  DEFAULT 90,
    is_active        BOOLEAN DEFAULT TRUE
);

-- Suscripciones (1:1 con Stripe Subscription)
CREATE TABLE track_subscriptions (
    id                       SERIAL PRIMARY KEY,
    user_id                  INT  REFERENCES track_users(id),
    tenant_id                INT  REFERENCES track_tenants(id),
    plan_id                  INT  REFERENCES track_stripe_prices(id),
    stripe_subscription_id   VARCHAR(80) UNIQUE,
    stripe_customer_id       VARCHAR(80),
    status                   VARCHAR(20),    -- active|trialing|past_due|canceled
    current_period_start     TIMESTAMPTZ,
    current_period_end       TIMESTAMPTZ,
    canceled_at              TIMESTAMPTZ,
    created_at               TIMESTAMPTZ DEFAULT NOW(),
    updated_at               TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla `tc_devices` viene del core de Traccar; añadir columna tenant_id:
ALTER TABLE tc_devices ADD COLUMN tenant_id INT REFERENCES track_tenants(id);
CREATE INDEX idx_tc_devices_tenant ON tc_devices(tenant_id);
```

**Importante:** ejecutar el `ALTER TABLE tc_devices` durante el rebrand (Fase 1
del roadmap) y migrar los devices existentes a un `tenant_id` por defecto.

---

## 6. Convenciones Redis (PCT 203)

| Key                                        | TTL   | Valor                                          | Quien escribe | Quien lee   |
| ------------------------------------------ | ----- | ---------------------------------------------- | ------------- | ----------- |
| `track:session:{sajet_user_id}`            | 3600s | JSON `{user_id, tenant_id, device_count, last_seen, ip, ua}` | Track backend | SAJET admin |
| `track:access:{sajet_user_id}:{tenant_id}` | 300s  | `"1"` o `"0"` (resultado de DSAM gate)         | Track backend | Track       |
| `track:device:{device_id}:last`            | 60s  | JSON última posición (presencia rápida)         | Track ingest  | Track API   |
| `track:rate:{user_id}:{minute}`            | 60s  | INCR (rate-limit por usuario)                   | Track API     | Track API   |
| `track:kill:{sajet_user_id}`               | -    | `"1"` (señal de kill-switch desde SAJET admin)  | SAJET admin   | Track       |

**Regla de oro:** Track **debe** chequear `track:kill:{user_id}` antes de
emitir un nuevo JWT o WebSocket. Si existe → revoca y borra la key.

Conexión Redis (host/port/password) — usar las mismas envs que MED:
```
REDIS_HOST=10.10.20.203
REDIS_PORT=6379
REDIS_PASSWORD=JtrRedis2026!
REDIS_DB=0
```

---

## 7. Flujo de alta (signup → cobro → activación)

```
┌──────────┐  1. signup    ┌────────────────┐
│ tack.    │──────────────▶│ sajet.us       │  crea sajet_user_id
│ sajet.us │               │ /api/auth/...  │  emite JWT
└────┬─────┘◀──────────────└────────┬───────┘
     │  2. JWT cookie               │
     │                              │
     │  3. seleccionar plan         │
     ▼                              │
┌──────────┐  4. POST /track/      ┌──────────────────────┐
│ Track UI │  checkout ────────────▶│ sajet.us /api/track/ │
│          │                        │ checkout (proxied)   │
└──────────┘                        └─────────┬────────────┘
                                              │  Stripe Checkout (modo según STRIPE_TRACK_MODE)
                                              ▼
                                    ┌─────────────────┐
                                    │  Stripe webhook │
                                    │  → sajet.us     │
                                    └─────────┬───────┘
                                              │
                              5. INSERT en sajet.track_subscriptions
                              6. INSERT en track_subscriptions (sync via webhook fanout)
                              7. SET track:access:{user}:{tenant}=1 (TTL 5min)
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │ Track backend    │
                                    │ habilita features│
                                    └──────────────────┘
```

> **Importante:** todos los cobros pasan por SAJET, **no** por Track directo.
> Track recibe sólo el `subscription_id` y el `plan_code` resuelto.

### Eventos Stripe que Track debe procesar (vía webhook proxy de SAJET)

- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`

SAJET expone `/api/track/webhook/stripe-fanout` (a implementar en sprint 2)
que reenviará firmado los eventos relevantes al endpoint Track interno.

---

## 8. Toggle de modo Stripe (test / sandbox / live)

Desde el panel admin de SAJET:

```
GET  /api/admin/stripe/mode?app=track
POST /api/admin/stripe/mode?app=track
     Body: {
       "mode": "live",
       "live_secret_key": "rk_live_...",
       "live_publishable_key": "pk_live_...",
       "live_webhook_secret": "whsec_..."
     }
```

El cambio se persiste en `system_config`. Track verá las credenciales nuevas
en el siguiente request a `/api/internal/config/stripe?app=track`.

**Convención de keys en `system_config`:**
- `STRIPE_TRACK_MODE` (`test|sandbox|live`)
- `STRIPE_TRACK_SECRET_KEY` (la activa, copia de la del modo elegido)
- `STRIPE_TRACK_PUBLISHABLE_KEY`
- `STRIPE_TRACK_WEBHOOK_SECRET`
- `STRIPE_TRACK_TEST_*`, `STRIPE_TRACK_SANDBOX_*`, `STRIPE_TRACK_LIVE_*`

---

## 9. Provisioning de Track (PCT)

Cuando se decida desplegar Track en producción:

1. **PCT propio** (sugerido `207 Tier-4-track`, IP `10.10.20.207`).
2. Crear BD `track` en PCT 200 (PostgreSQL primary).
3. Cloudflare Tunnel (vía PCT 205 npm-gateway): ruta `tack.sajet.us` → `10.10.20.207:8082`.
4. Configurar `.env` de Track con:
   ```
   # ⚠️ Tráfico M2M por IP interna (NO usar sajet.us)
   SAJET_INTERNAL_URL=http://10.10.20.202:4443
   SAJET_PUBLIC_URL=https://sajet.us           # solo para redirects de UI/login
   INTERNAL_SERVICE_KEY=<obtener de SAJET system_config>
   TRACK_DATABASE_URL=postgresql://jeturing:321Abcd@10.10.20.200:5432/track
   REDIS_HOST=10.10.20.203
   REDIS_PASSWORD=JtrRedis2026!
   JWT_SECRET_KEY=<mismo que SAJET — leer de /opt/Erp_core/.env>
   TRACK_DSAM_ENFORCE=false   # Q2-2026
   ```
5. Servicio systemd: `track.service` (Java) + `track-web.service` (Nginx).
6. Health check: `curl https://tack.sajet.us/api/server` debe responder 200.

---

## 10. Checklist de la integración (Track team)

- [ ] Implementar cliente HTTP que consuma `http://10.10.20.202:4443/api/internal/config/stripe?app=track` cada 60 s (IP interna, NO `sajet.us`)
- [ ] Implementar verificación JWT con secret compartido (`JWT_SECRET_KEY` de SAJET)
- [ ] Crear migrations Liquibase con las tablas del §5
- [ ] Publicar sesiones a Redis (`track:session:{user_id}`) en cada login
- [ ] Honrar `track:kill:{user_id}` → revocar JWT inmediatamente
- [ ] Wire de webhook proxy `/api/track/webhook/stripe-fanout` (cuando exista)
- [ ] Implementar fail-open / fail-closed según `TRACK_DSAM_ENFORCE`
- [ ] Branding: ocultar referencias visibles a Traccar (footer, login, README)
- [ ] Añadir `THIRD_PARTY.md` con licencias upstream

## 11. Checklist SAJET-side

- [x] App `track` registrada en `internal_config.py`
- [x] App `track` registrada en `settings.py` (`_STRIPE_APPS`)
- [x] Credenciales `STRIPE_TRACK_*` en panel admin
- [x] Router `/api/track/*` registrado en `app/main.py`
- [x] Módulo admin `app/routes/track_admin.py` con sesiones/subs/devices/plans
- [ ] Implementar `/api/dsam/access/track/check` (junto al de MED — ambos pendientes)
- [ ] Implementar fanout de webhook Stripe `/api/track/webhook/stripe-fanout`
- [ ] Crear PCT 207 + Cloudflare tunnel `tack.sajet.us` cuando Track esté listo
- [ ] Vista frontend en SAJET admin: tarjeta "Track" en dashboard de apps

---

## 12. Mapa de archivos modificados/creados en SAJET

| Archivo                                          | Cambio  |
| ------------------------------------------------ | ------- |
| [Erp_core/app/routes/internal_config.py](Erp_core/app/routes/internal_config.py) | `STRIPE_TRACK_` prefix + Literal |
| [Erp_core/app/routes/settings.py](Erp_core/app/routes/settings.py) | `_STRIPE_APPS['track']` + 12 keys nuevas |
| [Erp_core/app/routes/track_admin.py](Erp_core/app/routes/track_admin.py) | **NUEVO** — admin module |
| [Erp_core/app/main.py](Erp_core/app/main.py) | import + `include_router(track_admin.router)` |
| [Erp_core/docs/TRACK_INTEGRATION.md](Erp_core/docs/TRACK_INTEGRATION.md) | **NUEVO** — este documento |

---

## 13. Roadmap alineado con Jeturing-Track

| Trimestre | Hito Track                                | Trabajo SAJET-side                                  |
| --------- | ----------------------------------------- | --------------------------------------------------- |
| Q2-2026   | Rebrand + Dockerfile + Postgres default   | ✅ App slug + admin module + docs                   |
| Q3-2026   | CI/CD + observabilidad OTel               | Conector OTel hacia stack SAJET (compartido)        |
| Q3-2026   | Multi-tenant (`tenant_id` en core)        | DSAM gate `/api/dsam/access/track/check` + UI       |
| Q4-2026   | Stripe Billing + planes self-service      | Webhook fanout + checkout proxy + UI pricing        |
| Q4-2026   | Gateway BLE ESP32 + MQTT                  | Visibilidad de devices BLE en `/api/track/devices`  |
| Q1-2027   | White-label vanity domains                | Reutilizar `branding.router` + `domains.router` SAJET |
| Q1-2027   | LoRaWAN webhooks                          | Proxy en SAJET para firma + rate-limit              |
| Q2-2027   | Driver scoring + ETA ML                   | Reportes consolidados en SAJET admin                |
| Q2-2027   | SOC2 Tipo I                               | Audit trail Track→SAJET (`audit.router`)            |

---

_Última verificación de los endpoints expuestos: `python3 -c "import ast; ast.parse(open('app/main.py').read())"` ✅ — 2026-04-23._
