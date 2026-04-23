"""
Track Admin Routes — Visibilidad y gestión de la app `tack.sajet.us` (Jeturing-Track)
desde el panel administrativo de SAJET.

App: tack.sajet.us (fork de Traccar — telemetría GPS/BLE/UWB/LoRa multi-tenant)
DB:  track   (PostgreSQL en PCT 200, owner=jeturing)

Endpoints expuestos en `/api/track/*`:
  GET  /api/track/health              → ping + estado de la BD `track`
  GET  /api/track/subscriptions/stats → métricas (totales, activos, MRR, devices)
  GET  /api/track/subscriptions       → listado paginado de suscripciones
  POST /api/track/subscriptions/{id}/cancel
                                      → cancela suscripción (Stripe + BD + Redis)
  GET  /api/track/sessions            → sesiones live en Redis (`track:session:*`)
  GET  /api/track/devices             → conteo de dispositivos por tenant
  GET  /api/track/plans               → catálogo de planes Track (tabla
                                        `track_stripe_prices`, igual que MED)
  POST /api/track/plans               → upsert de planes Stripe

El módulo Track corre fuera de SAJET (PCT propio, fork de Traccar). SAJET sólo
provee:
  • Configuración Stripe vía `/api/internal/config/stripe?app=track`
  • Gate de acceso por usuario en `/api/dsam/access/track/check`
  • Visibilidad/cancelación administrativa para Customer Success

Requiere admin login (cookie `access_token`) — mismas reglas que medprep_admin.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session, sessionmaker

from ..config import get_runtime_setting
from ..routes.roles import _require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/track", tags=["Track Admin"])


# ─── Stripe key resolver (BD > env) ────────────────────────────
def _get_track_stripe_secret_key() -> str:
    """Devuelve la Secret Key Stripe de TRACK, con fallback a SAJET."""
    return (
        get_runtime_setting("STRIPE_TRACK_SECRET_KEY", "")
        or get_runtime_setting("STRIPE_SECRET_KEY", "")
        or ""
    )


# ─── Conexión a la BD `track` (separada de erp_core_db) ───────
_TRACK_DB_URL = os.getenv(
    "TRACK_DATABASE_URL",
    "postgresql+psycopg2://jeturing:321Abcd@10.10.20.200:5432/track",
)
_track_engine = None
_TrackSession = None


def _get_track_db():
    global _track_engine, _TrackSession
    if _TrackSession is None:
        _track_engine = create_engine(
            _TRACK_DB_URL,
            pool_size=3,
            max_overflow=5,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5},
        )
        _TrackSession = sessionmaker(bind=_track_engine)
    db = _TrackSession()
    try:
        yield db
    finally:
        db.close()


# ─── Auth helper ──────────────────────────────────────────────
def _require_admin_dep(request: Request, access_token: str = Cookie(None)):
    return _require_admin(request, access_token)


# ─── Redis lazy client ────────────────────────────────────────
_redis_client = None


def _get_redis():
    """Lazy singleton para Redis (PCT 203). No bloquea si está caído."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis as _redis
        _redis_client = _redis.Redis(
            host=os.getenv("REDIS_HOST", "10.10.20.203"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD", "JtrRedis2026!"),
            db=int(os.getenv("REDIS_DB", "0")),
            socket_timeout=2,
            socket_connect_timeout=2,
            decode_responses=True,
        )
        _redis_client.ping()
    except Exception as e:
        logger.warning("Track admin: Redis no disponible: %s", e)
        _redis_client = None
    return _redis_client


# ═════════════════════════════════════════════════════════════
#  ENDPOINTS
# ═════════════════════════════════════════════════════════════

@router.get("/health")
def health(_admin=Depends(_require_admin_dep)):
    """Ping rápido: verifica conexión BD `track` y Redis."""
    out = {"db": False, "redis": False, "tables": []}
    try:
        with _track_engine.connect() if _track_engine else create_engine(_TRACK_DB_URL).connect() as conn:
            tables = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY table_name LIMIT 20"
            )).fetchall()
            out["db"] = True
            out["tables"] = [t[0] for t in tables]
    except Exception as e:
        out["db_error"] = str(e)
    try:
        r = _get_redis()
        if r:
            r.ping()
            out["redis"] = True
            out["redis_track_keys"] = len(r.keys("track:*") or [])
    except Exception as e:
        out["redis_error"] = str(e)
    return {"success": True, "data": out}


# ─── Suscripciones ────────────────────────────────────────────

@router.get("/subscriptions/stats")
def subscriptions_stats(
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_track_db),
):
    """
    Métricas de suscripciones Track.
    Espera tabla `track_subscriptions(id, user_id, tenant_id, plan_id, status,
    stripe_subscription_id, stripe_customer_id, current_period_start,
    current_period_end, canceled_at, created_at, updated_at)`
    """
    now = datetime.now(timezone.utc)
    try:
        rows = db.execute(text("""
            SELECT
                COUNT(*)                                                     AS total,
                COUNT(*) FILTER (WHERE status = 'active'
                    AND (current_period_end IS NULL OR current_period_end > :now)) AS active,
                COUNT(*) FILTER (WHERE status = 'canceled')                  AS canceled,
                COUNT(*) FILTER (WHERE status = 'past_due')                  AS past_due,
                COUNT(*) FILTER (WHERE status = 'trialing')                  AS trialing,
                COUNT(DISTINCT user_id)   FILTER (WHERE status = 'active')   AS active_users,
                COUNT(DISTINCT tenant_id) FILTER (WHERE status = 'active')   AS active_tenants
            FROM track_subscriptions
        """), {"now": now}).fetchone()

        # MRR por suma de plan price_amount
        mrr_row = db.execute(text("""
            SELECT COALESCE(SUM(p.amount_cents), 0) / 100.0 AS mrr_usd
              FROM track_subscriptions s
              JOIN track_stripe_prices p ON p.id = s.plan_id
             WHERE s.status = 'active'
        """)).fetchone()

        new_30d = db.execute(text("""
            SELECT COUNT(*) FROM track_subscriptions
             WHERE created_at > NOW() - INTERVAL '30 days'
               AND status = 'active'
        """)).scalar() or 0

    except (ProgrammingError, OperationalError) as e:
        logger.warning("track_subscriptions schema not ready: %s", e)
        return {
            "success": True,
            "data": {
                "total": 0, "active": 0, "canceled": 0, "past_due": 0,
                "trialing": 0, "active_users": 0, "active_tenants": 0,
                "mrr_usd": 0, "new_last_30d": 0,
                "warning": "Schema track_subscriptions aún no creado en BD `track`",
            },
        }

    return {
        "success": True,
        "data": {
            "total": rows[0] or 0,
            "active": rows[1] or 0,
            "canceled": rows[2] or 0,
            "past_due": rows[3] or 0,
            "trialing": rows[4] or 0,
            "active_users": rows[5] or 0,
            "active_tenants": rows[6] or 0,
            "mrr_usd": float(mrr_row[0] or 0),
            "new_last_30d": new_30d,
        },
    }


@router.get("/subscriptions")
def list_subscriptions(
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_track_db),
    status: Optional[str] = Query(None, description="active|canceled|past_due|trialing|all"),
    tenant_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, description="email o stripe customer id"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Lista paginada de suscripciones Track con datos de plan y tenant."""
    offset = (page - 1) * limit
    now = datetime.now(timezone.utc)

    conditions = []
    params: dict = {"limit": limit, "offset": offset, "now": now}

    if status and status != "all":
        conditions.append("s.status = :status")
        params["status"] = status
    if tenant_id:
        conditions.append("s.tenant_id = :tenant_id")
        params["tenant_id"] = tenant_id
    if search:
        conditions.append("(u.email ILIKE :search OR s.stripe_customer_id ILIKE :search)")
        params["search"] = f"%{search}%"

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    try:
        rows = db.execute(text(f"""
            SELECT s.id, s.status, s.stripe_subscription_id, s.stripe_customer_id,
                   s.current_period_start, s.current_period_end, s.canceled_at,
                   s.created_at,
                   u.id, u.email, u.name,
                   t.id, t.slug, t.name,
                   p.amount_cents, p.currency, p.interval, p.label,
                   (s.status = 'active' AND (s.current_period_end IS NULL
                                             OR s.current_period_end > :now)) AS is_active
              FROM track_subscriptions s
              JOIN track_users   u ON u.id = s.user_id
              JOIN track_tenants t ON t.id = s.tenant_id
         LEFT JOIN track_stripe_prices p ON p.id = s.plan_id
              {where}
             ORDER BY s.created_at DESC
             LIMIT :limit OFFSET :offset
        """), params).fetchall()

        total = db.execute(text(f"""
            SELECT COUNT(*) FROM track_subscriptions s
              JOIN track_users   u ON u.id = s.user_id
              JOIN track_tenants t ON t.id = s.tenant_id
              {where}
        """), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    except (ProgrammingError, OperationalError) as e:
        logger.warning("track schema not ready: %s", e)
        return {"success": True, "data": [], "meta": {"total": 0, "page": page, "limit": limit, "pages": 0}}

    return {
        "success": True,
        "data": [
            {
                "id": r[0], "status": r[1],
                "stripe_subscription_id": r[2],
                "stripe_customer_id": r[3],
                "period_start": r[4].isoformat() if r[4] else None,
                "period_end":   r[5].isoformat() if r[5] else None,
                "canceled_at":  r[6].isoformat() if r[6] else None,
                "created_at":   r[7].isoformat() if r[7] else None,
                "is_active": bool(r[18]),
                "user":   {"id": r[8],  "email": r[9],  "name": r[10]},
                "tenant": {"id": r[11], "slug": r[12], "name": r[13]},
                "plan":   {
                    "amount": (r[14] or 0) / 100,
                    "currency": r[15] or "usd",
                    "interval": r[16] or "month",
                    "label": r[17],
                },
            }
            for r in rows
        ],
        "meta": {"total": total, "page": page, "limit": limit, "pages": -(-total // limit)},
    }


@router.post("/subscriptions/{sub_id}/cancel")
def cancel_subscription(
    sub_id: int,
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_track_db),
):
    """Cancela manualmente una suscripción Track (Stripe + BD + Redis)."""
    import stripe as _stripe
    _stripe.api_key = _get_track_stripe_secret_key()

    row = db.execute(text(
        "SELECT stripe_subscription_id, user_id, tenant_id "
        "  FROM track_subscriptions WHERE id=:id"
    ), {"id": sub_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")

    stripe_sub_id, user_id, tenant_id = row

    if stripe_sub_id and _stripe.api_key:
        try:
            _stripe.Subscription.cancel(stripe_sub_id)
        except Exception as e:
            logger.warning("Stripe cancel error (track sub %s): %s", sub_id, e)

    db.execute(text("""
        UPDATE track_subscriptions
           SET status='canceled', canceled_at=NOW(), updated_at=NOW()
         WHERE id=:id
    """), {"id": sub_id})
    db.commit()

    # Invalidar cache Redis
    r = _get_redis()
    if r:
        try:
            r.delete(
                f"track:access:{user_id}:{tenant_id}",
                f"track:session:{user_id}",
            )
        except Exception:
            pass

    return {"success": True, "message": f"Suscripción {sub_id} cancelada"}


# ─── Sesiones live (Redis) ────────────────────────────────────

@router.get("/sessions")
def live_sessions(_admin=Depends(_require_admin_dep)):
    """
    Sesiones Track activas en Redis.
    Keys: `track:session:{sajet_user_id}` → JSON {user_id, tenant_id, device_count, last_seen, ip, ua}
    """
    r = _get_redis()
    if not r:
        return {"success": True, "data": [], "total": 0, "warning": "Redis no disponible"}

    try:
        keys = r.keys("track:session:*") or []
        if not keys:
            return {"success": True, "data": [], "total": 0}
        pipe = r.pipeline()
        for k in keys:
            pipe.get(k)
        sessions = []
        for raw in pipe.execute():
            if raw:
                try:
                    sessions.append(json.loads(raw))
                except Exception:
                    pass
    except Exception as e:
        logger.warning("Redis read error: %s", e)
        return {"success": True, "data": [], "total": 0, "error": str(e)}

    return {"success": True, "data": sessions, "total": len(sessions)}


@router.post("/sessions/{user_id}/terminate")
def terminate_session(user_id: int, _admin=Depends(_require_admin_dep)):
    """Fuerza el cierre de sesión Track de un usuario (borra del Redis)."""
    r = _get_redis()
    if not r:
        raise HTTPException(status_code=503, detail="Redis no disponible")
    deleted = r.delete(f"track:session:{user_id}")
    return {"success": bool(deleted), "user_id": user_id}


# ─── Devices summary ──────────────────────────────────────────

@router.get("/devices")
def devices_summary(
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_track_db),
):
    """
    Conteo de dispositivos por tenant. Espera tabla `tc_devices` (Traccar core)
    con columna `attributes->>'tenant_id'` o `tenant_id` directa según el fork.
    """
    try:
        rows = db.execute(text("""
            SELECT t.id, t.slug, t.name,
                   COUNT(d.id) AS device_count,
                   COUNT(d.id) FILTER (WHERE d.disabled = FALSE) AS active_devices,
                   MAX(p.fixtime) AS last_position_at
              FROM track_tenants t
         LEFT JOIN tc_devices  d ON d.tenant_id = t.id
         LEFT JOIN tc_positions p ON p.deviceid  = d.id
         GROUP BY t.id, t.slug, t.name
         ORDER BY device_count DESC
        """)).fetchall()
    except (ProgrammingError, OperationalError) as e:
        return {"success": True, "data": [], "warning": f"Schema tc_devices no listo: {e}"}

    return {
        "success": True,
        "data": [
            {
                "tenant_id": r[0], "slug": r[1], "name": r[2],
                "devices_total": r[3] or 0,
                "devices_active": r[4] or 0,
                "last_position_at": r[5].isoformat() if r[5] else None,
            }
            for r in rows
        ],
    }


# ─── Catálogo de planes ───────────────────────────────────────

@router.get("/plans")
def list_plans(
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_track_db),
):
    """Catálogo de planes Track (tabla `track_stripe_prices`, mismo shape que MED)."""
    try:
        rows = db.execute(text("""
            SELECT id, code, label, stripe_price_id,
                   amount_cents, currency, interval,
                   max_devices, max_users, retention_days, is_active
              FROM track_stripe_prices
             ORDER BY amount_cents
        """)).fetchall()
    except (ProgrammingError, OperationalError) as e:
        return {"success": True, "data": [], "warning": f"Schema track_stripe_prices no listo: {e}"}

    return {
        "success": True,
        "data": [
            {
                "id": r[0], "code": r[1], "label": r[2],
                "stripe_price_id": r[3],
                "amount": (r[4] or 0) / 100,
                "currency": r[5] or "usd",
                "interval": r[6] or "month",
                "max_devices": r[7], "max_users": r[8],
                "retention_days": r[9], "is_active": r[10],
            }
            for r in rows
        ],
    }


@router.post("/plans")
async def upsert_plan(
    request: Request,
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_track_db),
):
    """
    Crear o actualizar un plan de Track.
    Body: {id?, code, label, stripe_price_id, amount, currency, interval,
           max_devices, max_users, retention_days, is_active}
    """
    body = await request.json()
    plan_id = body.get("id")

    if plan_id:
        sets, params = [], {"pid": plan_id}
        if "amount" in body:
            sets.append("amount_cents = :amt"); params["amt"] = int(float(body["amount"]) * 100)
        for fld, col in (
            ("label", "label"), ("max_devices", "max_devices"),
            ("max_users", "max_users"), ("retention_days", "retention_days"),
            ("is_active", "is_active"), ("stripe_price_id", "stripe_price_id"),
        ):
            if fld in body:
                sets.append(f"{col} = :{fld}"); params[fld] = body[fld]
        if not sets:
            raise HTTPException(status_code=400, detail="Nada que actualizar")
        db.execute(text(f"UPDATE track_stripe_prices SET {', '.join(sets)} WHERE id=:pid"), params)
        db.commit()
        return {"success": True, "message": f"Plan {plan_id} actualizado"}

    for field in ("code", "stripe_price_id", "amount", "interval"):
        if field not in body:
            raise HTTPException(status_code=422, detail=f"Campo requerido: {field}")
    db.execute(text("""
        INSERT INTO track_stripe_prices
            (code, label, stripe_price_id, amount_cents, currency, interval,
             max_devices, max_users, retention_days, is_active)
        VALUES (:code, :label, :spid, :amt, :cur, :iv,
                :maxd, :maxu, :ret, :active)
    """), {
        "code": body["code"],
        "label": body.get("label", body["code"]),
        "spid": body["stripe_price_id"],
        "amt": int(float(body["amount"]) * 100),
        "cur": body.get("currency", "usd"),
        "iv": body["interval"],
        "maxd": body.get("max_devices", 25),
        "maxu": body.get("max_users", 5),
        "ret": body.get("retention_days", 90),
        "active": body.get("is_active", True),
    })
    db.commit()
    return {"success": True, "message": "Plan creado"}
