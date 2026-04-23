"""
MedPrep Admin Routes — Visibilidad y gestión de estudiantes/suscripciones
desde el panel DSM de SAJET.

Endpoints:
  GET  /api/medprep/subscriptions          → listado de suscripciones con filtros
  GET  /api/medprep/subscriptions/stats    → métricas: total, activos, MRR
  GET  /api/medprep/sessions               → sesiones activas en Redis
  POST /api/medprep/subscriptions/{id}/cancel  → cancelar suscripción manual
  GET  /api/medprep/banks                  → bancos disponibles con conteo
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ..models.database import get_db
from ..routes.roles import _require_admin
from ..config import get_runtime_setting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/medprep", tags=["MedPrep Admin"])


def _get_med_stripe_secret_key() -> str:
    """Obtiene la clave Stripe para MedPrep desde runtime config (BD > env)."""
    return (
        get_runtime_setting("STRIPE_MED_SECRET_KEY", "")
        or get_runtime_setting("STRIPE_SECRET_KEY", "")
        or ""
    )

# ─── Conexión a la BD med (separada de erp_core_db) ───────────
import os

_MED_DB_URL = os.getenv(
    "MED_DATABASE_URL",
    "postgresql+psycopg2://jeturing:321Abcd@10.10.20.200:5432/med",
)
_med_engine = None
_MedSession = None


def _get_med_db():
    global _med_engine, _MedSession
    if _MedSession is None:
        _med_engine = create_engine(_MED_DB_URL, pool_size=3, max_overflow=5, pool_pre_ping=True)
        _MedSession = sessionmaker(bind=_med_engine)
    db = _MedSession()
    try:
        yield db
    finally:
        db.close()


# ─── Helper de autenticación admin ────────────────────────────

def _require_admin_dep(request: Request, access_token: str = Cookie(None)):
    return _require_admin(request, access_token)


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

@router.get("/subscriptions/stats")
def subscriptions_stats(
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_med_db),
):
    """Métricas de suscripciones MedPrep: total, activos, ingresos proyectados."""
    now = datetime.now(timezone.utc)
    rows = db.execute(text("""
        SELECT
            COUNT(*)                                                    AS total,
            COUNT(*) FILTER (WHERE status = 'active'
                AND (current_period_end IS NULL OR current_period_end > :now)) AS active,
            COUNT(*) FILTER (WHERE status = 'canceled')                AS canceled,
            COUNT(*) FILTER (WHERE status = 'past_due')                AS past_due,
            COUNT(DISTINCT user_id) FILTER (WHERE status = 'active'
                AND (current_period_end IS NULL OR current_period_end > :now)) AS active_students,
            COUNT(DISTINCT bank_id) FILTER (WHERE status = 'active')   AS banks_with_subs
        FROM user_subscriptions
    """), {"now": now}).fetchone()

    # Ingresos proyectados (ARR): activos × $100
    arr = (rows[1] or 0) * 100

    # Nuevas suscripciones últimas 30 días
    new_30d = db.execute(text("""
        SELECT COUNT(*) FROM user_subscriptions
        WHERE created_at > NOW() - INTERVAL '30 days' AND status = 'active'
    """)).scalar() or 0

    # Distribución por banco
    by_bank = db.execute(text("""
        SELECT b.name, b.slug, b.color,
               COUNT(*) FILTER (WHERE s.status = 'active') AS active_subs,
               COUNT(*) AS total_subs
        FROM banks b
        LEFT JOIN user_subscriptions s ON s.bank_id = b.id
        WHERE b.is_active = TRUE
        GROUP BY b.id, b.name, b.slug, b.color
        ORDER BY active_subs DESC
    """)).fetchall()

    return {
        "success": True,
        "data": {
            "total": rows[0] or 0,
            "active": rows[1] or 0,
            "canceled": rows[2] or 0,
            "past_due": rows[3] or 0,
            "active_students": rows[4] or 0,
            "banks_with_subs": rows[5] or 0,
            "arr_usd": arr,
            "new_last_30d": new_30d,
            "by_bank": [
                {"name": r[0], "slug": r[1], "color": r[2], "active": r[3], "total": r[4]}
                for r in by_bank
            ],
        },
    }


@router.get("/subscriptions")
def list_subscriptions(
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_med_db),
    status: Optional[str] = Query(None, description="active|canceled|past_due|all"),
    bank_slug: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="buscar por email"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Lista paginada de suscripciones con datos de usuario y banco."""
    offset = (page - 1) * limit
    now = datetime.now(timezone.utc)

    conditions = []
    params: dict = {"limit": limit, "offset": offset, "now": now}

    if status and status != "all":
        conditions.append("s.status = :status")
        params["status"] = status
    if bank_slug:
        conditions.append("b.slug = :bank_slug")
        params["bank_slug"] = bank_slug
    if search:
        conditions.append("u.display_name ILIKE :search OR CAST(u.sajet_user_id AS TEXT) ILIKE :search")
        params["search"] = f"%{search}%"

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    rows = db.execute(text(f"""
        SELECT
            s.id, s.status, s.stripe_subscription_id, s.stripe_customer_id,
            s.current_period_start, s.current_period_end, s.canceled_at,
            s.created_at,
            u.id AS med_user_id, u.sajet_user_id, u.display_name, u.role,
            b.id AS bank_id, b.slug, b.name, b.color,
            p.amount_cents, p.currency,
            (s.status = 'active' AND (s.current_period_end IS NULL OR s.current_period_end > :now)) AS is_active
        FROM user_subscriptions s
        JOIN med_users u  ON u.id = s.user_id
        JOIN banks b      ON b.id = s.bank_id
        LEFT JOIN bank_stripe_prices p ON p.bank_id = b.id
        {where}
        ORDER BY s.created_at DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    total = db.execute(text(f"""
        SELECT COUNT(*) FROM user_subscriptions s
        JOIN med_users u ON u.id = s.user_id
        JOIN banks b     ON b.id = s.bank_id
        {where}
    """), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0

    return {
        "success": True,
        "data": [
            {
                "id": r[0],
                "status": r[1],
                "stripe_subscription_id": r[2],
                "stripe_customer_id": r[3],
                "period_start": r[4].isoformat() if r[4] else None,
                "period_end":   r[5].isoformat() if r[5] else None,
                "canceled_at":  r[6].isoformat() if r[6] else None,
                "created_at":   r[7].isoformat() if r[7] else None,
                "is_active": bool(r[18]),
                "user": {
                    "med_user_id": r[8],
                    "sajet_user_id": r[9],
                    "display_name": r[10],
                    "role": r[11],
                },
                "bank": {"id": r[12], "slug": r[13], "name": r[14], "color": r[15]},
                "price": {"amount": (r[16] or 10000) / 100, "currency": r[17] or "usd"},
            }
            for r in rows
        ],
        "meta": {"total": total, "page": page, "limit": limit, "pages": -(-total // limit)},
    }


@router.get("/sessions")
def live_sessions(
    _admin=Depends(_require_admin_dep),
):
    """Sesiones MedPrep activas en Redis (live)."""
    try:
        from ..services.medprep_sessions import get_med_sessions
        sessions = get_med_sessions()
    except Exception:
        # Leer directamente desde Redis si el servicio no existe
        import redis as _redis, os as _os, json as _json
        try:
            r = _redis.Redis(
                host=_os.getenv("REDIS_HOST", "10.10.20.203"),
                port=int(_os.getenv("REDIS_PORT", "6379")),
                password=_os.getenv("REDIS_PASSWORD", "JtrRedis2026!"),
                db=0,
                socket_timeout=2,
                decode_responses=True,
            )
            keys = r.keys("medprep:session:*")
            sessions = []
            if keys:
                pipe = r.pipeline()
                for k in keys:
                    pipe.get(k)
                for raw in pipe.execute():
                    if raw:
                        try:
                            sessions.append(_json.loads(raw))
                        except Exception:
                            pass
        except Exception as e:
            logger.warning("Redis no disponible: %s", e)
            sessions = []

    return {"success": True, "data": sessions, "total": len(sessions)}


@router.post("/subscriptions/{sub_id}/cancel")
def cancel_subscription(
    sub_id: int,
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_med_db),
):
    """Cancela manualmente una suscripción (admin override)."""
    import stripe as _stripe
    _stripe.api_key = _get_med_stripe_secret_key()

    row = db.execute(text(
        "SELECT stripe_subscription_id, user_id, bank_id FROM user_subscriptions WHERE id=:id"
    ), {"id": sub_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")

    stripe_sub_id, user_id, bank_id = row

    # Cancelar en Stripe si existe
    if stripe_sub_id and _stripe.api_key:
        try:
            _stripe.Subscription.cancel(stripe_sub_id)
        except Exception as e:
            logger.warning("Stripe cancel error: %s", e)

    # Actualizar en BD
    db.execute(text("""
        UPDATE user_subscriptions
           SET status = 'canceled', canceled_at = NOW(), updated_at = NOW()
         WHERE id = :id
    """), {"id": sub_id})
    db.commit()

    # Invalidar cache
    try:
        import sys
        sys.path.insert(0, "/opt/prepmed/med_app")
        from backend.redis_cache import cache_invalidate_access, cache_invalidate_catalog
        cache_invalidate_access(user_id, bank_id)
        cache_invalidate_catalog(user_id)
    except Exception:
        pass

    return {"success": True, "message": f"Suscripción {sub_id} cancelada"}


@router.get("/banks")
def list_banks(
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_med_db),
):
    """Bancos disponibles con todos los precios y estadísticas."""
    bank_rows = db.execute(text("""
        SELECT b.id, b.slug, b.name, b.color, b.icon,
               b.question_count, b.flashcard_count,
               COUNT(s.id) FILTER (WHERE s.status = 'active') AS active_subs
        FROM banks b
        LEFT JOIN user_subscriptions s ON s.bank_id = b.id
        WHERE b.is_active = TRUE
        GROUP BY b.id, b.slug, b.name, b.color, b.icon,
                 b.question_count, b.flashcard_count
        ORDER BY b.sort_order
    """)).fetchall()

    price_rows = db.execute(text("""
        SELECT id, bank_id, stripe_price_id, amount_cents, currency,
               interval, is_active, max_seats, label
        FROM bank_stripe_prices
        ORDER BY bank_id, interval
    """)).fetchall()

    prices_by_bank: dict = {}
    for p in price_rows:
        bid = p[1]
        if bid not in prices_by_bank:
            prices_by_bank[bid] = []
        prices_by_bank[bid].append({
            "id": p[0], "stripe_price_id": p[2],
            "amount": (p[3] or 0) / 100, "currency": p[4] or "usd",
            "interval": p[5] or "year", "is_active": p[6],
            "max_seats": p[7] or 1, "label": p[8],
        })

    return {
        "success": True,
        "data": [
            {
                "id": r[0], "slug": r[1], "name": r[2], "color": r[3], "icon": r[4],
                "question_count": r[5], "flashcard_count": r[6],
                "active_subscriptions": r[7] or 0,
                "prices": prices_by_bank.get(r[0], []),
            }
            for r in bank_rows
        ],
    }


@router.post("/prices")
async def manage_price(
    request: Request,
    _admin=Depends(_require_admin_dep),
    db: Session = Depends(_get_med_db),
):
    """
    Crear o actualizar un precio de MedPrep.
    Body: { id?, bank_id, amount, currency, interval, max_seats, label, is_active, stripe_price_id }
    """
    body = await request.json()
    price_id = body.get("id")

    if price_id:
        sets = []
        params: dict = {"pid": price_id}
        if "amount" in body:
            sets.append("amount_cents = :amt")
            params["amt"] = int(float(body["amount"]) * 100)
        if "max_seats" in body:
            sets.append("max_seats = :seats")
            params["seats"] = int(body["max_seats"])
        if "label" in body:
            sets.append("label = :lbl")
            params["lbl"] = body["label"]
        if "is_active" in body:
            sets.append("is_active = :active")
            params["active"] = bool(body["is_active"])
        if not sets:
            raise HTTPException(status_code=400, detail="Nada que actualizar")
        db.execute(text(f"UPDATE bank_stripe_prices SET {', '.join(sets)} WHERE id = :pid"), params)
        db.commit()
        return {"success": True, "message": f"Precio {price_id} actualizado"}
    else:
        for field in ("bank_id", "amount", "interval", "stripe_price_id"):
            if field not in body:
                raise HTTPException(status_code=422, detail=f"Campo requerido: {field}")
        db.execute(text("""
            INSERT INTO bank_stripe_prices (bank_id, stripe_price_id, amount_cents, currency, interval, is_active, max_seats, label)
            VALUES (:bid, :spid, :amt, :cur, :iv, :active, :seats, :lbl)
        """), {
            "bid": int(body["bank_id"]),
            "spid": body["stripe_price_id"],
            "amt": int(float(body["amount"]) * 100),
            "cur": body.get("currency", "usd"),
            "iv": body["interval"],
            "active": body.get("is_active", True),
            "seats": int(body.get("max_seats", 1)),
            "lbl": body.get("label"),
        })
        db.commit()
        return {"success": True, "message": "Precio creado"}


@router.post("/send-email")
async def send_medprep_email(request: Request):
    """
    Internal endpoint for MedPrep to send transactional emails.
    No admin auth required — called server-to-server from localhost.
    Templates: medprep_welcome, medprep_reengagement
    """
    from ..services.email_service import send_email, _base_template

    body = await request.json()
    to = body.get("to")
    template = body.get("template", "")
    data = body.get("data", {})

    if not to:
        raise HTTPException(status_code=422, detail="Campo 'to' requerido")

    name = data.get("display_name", "Estudiante")

    if template == "medprep_welcome":
        content = f"""
        <h2 style="color: #00FF9F; margin-top: 0;">¡Bienvenido/a a MedPrep! 🎓</h2>
        <p>Hola <strong>{name}</strong>,</p>
        <p>Tu cuenta ha sido creada exitosamente. MedPrep es la plataforma de preparación médica
        más completa para el ENURM y especialidades.</p>

        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin: 24px 0;
                    border: 1px solid #00FF9F33;">
          <h3 style="color: #fff; margin-top: 0;">Lo que te espera:</h3>
          <ul style="color: #ccc; padding-left: 20px;">
            <li>📝 Miles de preguntas tipo ENURM</li>
            <li>🃏 Flashcards con repetición espaciada</li>
            <li>⚔️ Desafíos competitivos contra otros estudiantes</li>
            <li>📊 Estadísticas detalladas de tu progreso</li>
          </ul>
        </div>

        <div style="text-align: center; margin: 32px 0;">
          <a href="https://med.sajet.us/pricing"
             style="display: inline-block; background: #00FF9F; color: #0a0a1a; padding: 14px 32px;
                    border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 16px;">
            Elegir mi plan →
          </a>
        </div>

        <p style="color: #999; font-size: 13px;">
          ¿Preguntas? Escríbenos a <a href="mailto:soporte@sajet.us" style="color: #00FF9F;">soporte@sajet.us</a>
        </p>
        """
        subject = f"🎓 ¡Bienvenido/a a MedPrep, {name}!"

    elif template == "medprep_reengagement":
        content = f"""
        <h2 style="color: #00FF9F; margin-top: 0;">¡Te extrañamos, {name}! 🏆</h2>
        <p>Han pasado unos días desde tu última sesión de estudio.</p>

        <div style="background: #1a1a2e; border-radius: 12px; padding: 24px; margin: 24px 0;
                    border: 1px solid #f39c1233;">
          <p style="color: #f39c12; font-size: 15px; margin: 0;">
            ⚔️ <strong>¿Te atreves a un duelo?</strong><br>
            Tus compañeros están practicando. Inicia un desafío rápido y gana XP.
          </p>
        </div>

        <div style="text-align: center; margin: 32px 0;">
          <a href="https://med.sajet.us/challenge"
             style="display: inline-block; background: #00FF9F; color: #0a0a1a; padding: 14px 32px;
                    border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 16px;">
            Iniciar un duelo ⚔️
          </a>
        </div>

        <p style="color: #999; font-size: 13px;">
          La constancia es la clave del éxito en el ENURM. ¡Vuelve a la acción!
        </p>
        """
        subject = f"⚔️ {name}, tus compañeros te retan a un duelo — MedPrep"
    else:
        raise HTTPException(status_code=400, detail=f"Template desconocido: {template}")

    result = send_email(
        to_email=to,
        subject=subject,
        html_body=_base_template(content),
        text_body=f"Hola {name}, visita https://med.sajet.us",
        email_type=template,
    )

    return {"success": result.get("success", False), "message_id": result.get("message_id")}
