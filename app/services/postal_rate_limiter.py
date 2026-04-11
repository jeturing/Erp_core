"""
postal_rate_limiter.py — Sliding-window rate limiter para Postal SMTP

Implementa límites de envío por tenant equivalentes a O365/Gmail para
proteger la reputación de la IP del servidor Postal Sajet.

Ventanas soportadas:
  - minute : email_rate_per_minute  (default: 20)
  - hour   : email_rate_per_hour    (default: 500)
  - day    : email_rate_per_day     (default: 2000)

Cuota mensual:
  - max_emails_monthly  (default: 5000, 0 = ilimitado)

Uso típico en postal_service.py:
    from app.services.postal_rate_limiter import check_rate_limit, record_email_sent

    allowed, reason = check_rate_limit(db, tenant_subdomain, plan)
    if not allowed:
        raise HTTPException(status_code=429, detail=reason)
    record_email_sent(db, tenant_subdomain)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.database import (
    Customer,
    CustomerAddonSubscription,
    EmailRateLimitWindow,
    Partner,
    PartnerPricingOverride,
    Plan,
    PostalEmailUsage,
    RateLimitWindowType,
    ServiceCatalogItem,
)

logger = logging.getLogger(__name__)

EMAIL_PACKAGE_SERVICE_CODE = "postal_email_package"

# ── Helpers de ventanas ────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _window_start_end(window_type: RateLimitWindowType, now: datetime) -> tuple[datetime, datetime]:
    """Devuelve (window_start, window_end) truncando al tipo de ventana."""
    if window_type == RateLimitWindowType.minute:
        start = now.replace(second=0, microsecond=0)
        return start, start + timedelta(minutes=1)
    elif window_type == RateLimitWindowType.hour:
        start = now.replace(minute=0, second=0, microsecond=0)
        return start, start + timedelta(hours=1)
    else:  # day
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)


# ── Resolución de límites en cascada ───────────────────────────────────────
#
#   Prioridad (el primero no-NULL gana):
#     1. Per-tenant addon  → CustomerAddonSubscription.metadata_json
#     2. Per-partner        → PartnerPricingOverride.*_override
#     3. Plan defaults      → Plan.max_emails_monthly / email_rate_per_*
#
#   0 = ilimitado en cualquier nivel.
# ──────────────────────────────────────────────────────────────────────────

_LIMIT_FIELDS = [
    "max_emails_monthly",
    "email_rate_per_minute",
    "email_rate_per_hour",
    "email_rate_per_day",
]

_PLAN_DEFAULTS = {
    "max_emails_monthly":    5000,
    "email_rate_per_minute": 20,
    "email_rate_per_hour":   500,
    "email_rate_per_day":    2000,
}


def resolve_email_limits(
    db: Session,
    tenant_subdomain: str,
) -> dict[str, int]:
    """
    Resuelve los límites de email efectivos para un tenant usando cascada:
      addon > partner override > plan defaults.

    Retorna dict con las 4 claves de _LIMIT_FIELDS.
    """
    limits: dict[str, Optional[int]] = {k: None for k in _LIMIT_FIELDS}

    # ── Buscar customer ──────────────────────────────────────────────────
    customer = (
        db.query(Customer)
        .filter(Customer.subdomain == tenant_subdomain)
        .first()
    )

    # ── 1. Per-tenant addon (postal_email_package) ───────────────────────
    if customer:
        addon_sub = (
            db.query(CustomerAddonSubscription)
            .filter(
                CustomerAddonSubscription.customer_id == customer.id,
                CustomerAddonSubscription.service_code == EMAIL_PACKAGE_SERVICE_CODE,
                CustomerAddonSubscription.status == "active",
            )
            .order_by(CustomerAddonSubscription.id.desc())
            .first()
        )
        if addon_sub:
            base_meta: dict = {}
            if addon_sub.catalog_item_id:
                cat = db.query(ServiceCatalogItem).get(addon_sub.catalog_item_id)
                if cat and cat.metadata_json:
                    base_meta = cat.metadata_json if isinstance(cat.metadata_json, dict) else {}

            sub_meta = addon_sub.metadata_json if isinstance(addon_sub.metadata_json, dict) else {}
            # Orden de precedencia: catálogo base + overrides puntuales en la suscripción del tenant.
            meta = {**base_meta, **sub_meta}

            if meta:
                for field in _LIMIT_FIELDS:
                    val = meta.get(field)
                    # Compatibilidad con metadata legacy del catálogo
                    if val is None:
                        if field == "max_emails_monthly":
                            val = meta.get("email_quota_monthly")
                        elif field == "email_rate_per_hour":
                            val = meta.get("email_burst_limit_60m")
                        elif field == "email_rate_per_minute":
                            burst = meta.get("email_burst_limit_60m")
                            if burst is not None:
                                try:
                                    val = max(1, int(burst) // 60)
                                except Exception:
                                    val = None
                        elif field == "email_rate_per_day":
                            quota = meta.get("email_quota_monthly")
                            burst = meta.get("email_burst_limit_60m")
                            try:
                                q = int(quota) if quota is not None else None
                                b = int(burst) if burst is not None else None
                                if q is not None and b is not None:
                                    val = min(q, b * 24)
                                elif q is not None:
                                    val = q
                                elif b is not None:
                                    val = b * 24
                            except Exception:
                                val = None
                    if val is not None:
                        limits[field] = int(val)

    # ── 2. Per-partner override ──────────────────────────────────────────
    if customer and customer.partner_id:
        # Obtener el plan_name del customer para buscar el override correcto
        plan_name = getattr(customer, "plan", None)
        if plan_name:
            if hasattr(plan_name, "value"):  # Si es Enum
                plan_name = plan_name.value
            override = (
                db.query(PartnerPricingOverride)
                .filter(
                    PartnerPricingOverride.partner_id == customer.partner_id,
                    PartnerPricingOverride.plan_name == plan_name,
                    PartnerPricingOverride.is_active == True,
                )
                .first()
            )
            if override:
                for field in _LIMIT_FIELDS:
                    if limits[field] is not None:
                        continue  # Addon ya definió este campo
                    val = getattr(override, f"{field}_override", None)
                    if val is not None:
                        limits[field] = val

    # ── 3. Plan defaults ─────────────────────────────────────────────────
    plan_obj = _get_plan_for_customer(db, customer) if customer else None
    for field in _LIMIT_FIELDS:
        if limits[field] is not None:
            continue
        if plan_obj:
            val = getattr(plan_obj, field, None)
            if val is not None:
                limits[field] = val
                continue
        limits[field] = _PLAN_DEFAULTS[field]

    return limits  # type: ignore[return-value]


def _get_plan_for_customer(db: Session, customer: Customer) -> Optional[Plan]:
    """Busca el Plan del customer por nombre (customer.plan es un Enum string)."""
    plan_name = getattr(customer, "plan", None)
    if not plan_name:
        return None
    if hasattr(plan_name, "value"):
        plan_name = plan_name.value
    return db.query(Plan).filter(Plan.name == plan_name).first()


# ── Core API pública ───────────────────────────────────────────────────────

def check_rate_limit(
    db: Session,
    tenant_subdomain: str,
    plan: Optional[Plan] = None,
    n_emails: int = 1,
) -> tuple[bool, str]:
    """
    Verifica si el tenant puede enviar `n_emails` más.

    Resuelve límites usando cascada: addon > partner > plan.
    Si se pasa `plan` explícitamente, se usa como fallback final.

    Retorna (allowed: bool, reason: str).
    """
    now = _utcnow()
    limits = resolve_email_limits(db, tenant_subdomain)

    # ── 1. Cuota mensual ──────────────────────────────────────────────────
    monthly_limit = limits["max_emails_monthly"]
    if monthly_limit > 0:
        monthly_sent = _get_monthly_sent(db, tenant_subdomain, now)
        if monthly_sent + n_emails > monthly_limit:
            msg = (
                f"Cuota mensual agotada para '{tenant_subdomain}': "
                f"{monthly_sent}/{monthly_limit} emails este mes."
            )
            logger.warning(msg)
            return False, msg

    # ── 2. Rate limiting por ventana ──────────────────────────────────────
    window_checks = [
        (RateLimitWindowType.minute, limits["email_rate_per_minute"]),
        (RateLimitWindowType.hour,   limits["email_rate_per_hour"]),
        (RateLimitWindowType.day,    limits["email_rate_per_day"]),
    ]

    for window_type, limit in window_checks:
        if limit == 0:
            continue  # 0 = ilimitado para esta ventana
        w_start, _ = _window_start_end(window_type, now)
        current_count = _get_window_count(db, tenant_subdomain, window_type, w_start)
        if current_count + n_emails > limit:
            msg = (
                f"Rate limit alcanzado para '{tenant_subdomain}' "
                f"[{window_type.value}]: {current_count}/{limit} emails."
            )
            logger.warning(msg)
            return False, msg

    return True, "ok"


def record_email_sent(
    db: Session,
    tenant_subdomain: str,
    n_emails: int = 1,
) -> None:
    """
    Incrementa los contadores de ventana para `tenant_subdomain`.
    Usa INSERT … ON CONFLICT DO UPDATE para atomicidad sin race conditions.
    """
    now = _utcnow()

    for window_type in RateLimitWindowType:
        w_start, w_end = _window_start_end(window_type, now)
        _upsert_window(db, tenant_subdomain, window_type, w_start, w_end, n_emails)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Error al registrar email en rate limit windows")
        raise


def get_rate_limit_status(
    db: Session,
    tenant_subdomain: str,
    plan: Optional[Plan] = None,
) -> dict:
    """
    Devuelve el estado actual de uso vs. límites para el tenant.
    Usa resolución en cascada: addon > partner > plan.
    Útil para endpoint de monitoreo o panel admin.
    """
    now = _utcnow()
    limits = resolve_email_limits(db, tenant_subdomain)
    monthly_limit = limits["max_emails_monthly"]

    status = {
        "tenant": tenant_subdomain,
        "monthly": {
            "limit": monthly_limit,
            "used": _get_monthly_sent(db, tenant_subdomain, now),
            "unlimited": monthly_limit == 0,
        },
        "windows": {},
    }

    for window_type in RateLimitWindowType:
        limit_key = f"email_rate_per_{window_type.value}"
        limit = limits[limit_key]
        w_start, _ = _window_start_end(window_type, now)
        count = _get_window_count(db, tenant_subdomain, window_type, w_start)
        status["windows"][window_type.value] = {
            "limit": limit,
            "used": count,
            "unlimited": limit == 0,
            "window_start": w_start.isoformat(),
        }

    return status


def cleanup_old_windows(db: Session, older_than_hours: int = 48) -> int:
    """
    Elimina ventanas más antiguas de `older_than_hours` horas.
    Llamar desde un cron/background task diario.
    Retorna el número de filas eliminadas.
    """
    cutoff = _utcnow() - timedelta(hours=older_than_hours)
    result = db.execute(
        text(
            "DELETE FROM email_rate_limit_windows WHERE window_end < :cutoff"
        ),
        {"cutoff": cutoff},
    )
    db.commit()
    deleted = result.rowcount
    if deleted:
        logger.info("cleanup_old_windows: eliminadas %d ventanas antiguas", deleted)
    return deleted


# ── Helpers internos ───────────────────────────────────────────────────────

def _get_monthly_sent(db: Session, tenant_subdomain: str, now: datetime) -> int:
    """Total de emails enviados este mes (desde PostalEmailUsage)."""
    row = (
        db.query(PostalEmailUsage)
        .filter(
            PostalEmailUsage.tenant_subdomain == tenant_subdomain,
            PostalEmailUsage.period_year == now.year,
            PostalEmailUsage.period_month == now.month,
        )
        .first()
    )
    if row is None:
        return 0
    return row.emails_sent or 0


def _get_window_count(
    db: Session,
    tenant_subdomain: str,
    window_type: RateLimitWindowType,
    window_start: datetime,
) -> int:
    """Obtiene el contador actual de la ventana, o 0 si no existe."""
    row = (
        db.query(EmailRateLimitWindow)
        .filter(
            EmailRateLimitWindow.tenant_subdomain == tenant_subdomain,
            EmailRateLimitWindow.window_type == window_type,
            EmailRateLimitWindow.window_start == window_start,
        )
        .first()
    )
    return row.emails_count if row else 0


def _upsert_window(
    db: Session,
    tenant_subdomain: str,
    window_type: RateLimitWindowType,
    window_start: datetime,
    window_end: datetime,
    n_emails: int,
) -> None:
    """
    INSERT ... ON CONFLICT DO UPDATE para incrementar el contador de forma atómica.
    Usa SQL nativo para garantizar atomicidad en concurrencia.
    """
    db.execute(
        text(
            """
            INSERT INTO email_rate_limit_windows
                (tenant_subdomain, window_type, window_start, window_end, emails_count, created_at, updated_at)
            VALUES
                (:tenant, :wtype, :wstart, :wend, :n, NOW(), NOW())
            ON CONFLICT (tenant_subdomain, window_type, window_start)
            DO UPDATE SET
                emails_count = email_rate_limit_windows.emails_count + EXCLUDED.emails_count,
                updated_at   = NOW()
            """
        ),
        {
            "tenant": tenant_subdomain,
            "wtype":  window_type.value,
            "wstart": window_start,
            "wend":   window_end,
            "n":      n_emails,
        },
    )
