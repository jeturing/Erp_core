"""
Odoo Webhooks — Recibe notificaciones desde Odoo cuando se crean/modifican
contactos, usuarios o configuración del tenant.

Dirección: Odoo → ERP Core (sajet.us)
Módulo Odoo: jeturing_erp_sync (envía webhooks aquí)

Eventos soportados:
- user.created: Se creó un usuario en el tenant Odoo
- user.updated: Se actualizó un usuario (email, active, etc.)
- user.deleted: Se desactivó/eliminó un usuario
- partner.created: Se creó un res.partner (contacto/cliente) en Odoo
- tenant.config_changed: Cambió configuración del tenant (company name, etc.)
- tenant.snapshot: Snapshot completo del tenant para reconciliación
"""
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from ..models.database import (
    AuditEventRecord,
    BillingMode,
    Customer,
    CustomDomain,
    DomainVerificationStatus,
    Plan,
    SessionLocal,
    Subscription,
    SubscriptionStatus,
    TenantDeployment,
    SeatEventType,
)
from ..config import PROVISIONING_API_KEY, get_runtime_setting
from ..services.pricing import recalculate_subscription_monthly_amount
from ..services.seat_events import (
    is_billable_user,
    record_hwm_snapshot,
    record_seat_event,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/odoo", tags=["Odoo Webhooks"])

def _provisioning_api_key() -> str:
    return get_runtime_setting("PROVISIONING_API_KEY", PROVISIONING_API_KEY)


def _odoo_webhook_secret() -> str:
    return get_runtime_setting("ODOO_WEBHOOK_SECRET", _provisioning_api_key())


def _verify_webhook(x_api_key: Optional[str], x_webhook_signature: Optional[str], body: bytes) -> bool:
    """
    Verifica autenticidad del webhook.
    Acepta API key directa O firma HMAC del body.
    """
    provisioning_api_key = _provisioning_api_key()
    webhook_secret = _odoo_webhook_secret()

    # Method 1: Direct API key
    if x_api_key and x_api_key == provisioning_api_key:
        return True

    # Method 2: HMAC signature
    if x_webhook_signature and webhook_secret:
        expected = hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, x_webhook_signature)

    return False


class OdooWebhookEvent(BaseModel):
    """Evento genérico desde Odoo."""
    event: str  # user.created, user.updated, user.deleted, partner.created, tenant.config_changed, tenant.snapshot
    tenant_db: str  # nombre de la BD Odoo (= subdomain del customer)
    data: Dict[str, Any] = {}
    timestamp: Optional[str] = None


class OdooWebhookBatchEvent(BaseModel):
    """Batch de eventos (para sincronización bulk)."""
    events: List[OdooWebhookEvent]


@router.post("")
async def receive_odoo_webhook(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_webhook_signature: Optional[str] = Header(None),
):
    """
    Recibe webhook de Odoo y procesa el evento.

    Headers requeridos:
    - X-API-KEY: API key de provisioning, O
    - X-Webhook-Signature: HMAC-SHA256 del body con ODOO_WEBHOOK_SECRET

    Body JSON:
    {
        "event": "user.created",
        "tenant_db": "smarttoolsrd",
        "data": {
            "user_id": 10,
            "login": "nuevo@empresa.com",
            "name": "Nuevo Usuario",
            "active": true,
            "share": false,
            "groups": ["base.group_user"]
        }
    }
    """
    body = await request.body()
    if not _verify_webhook(x_api_key, x_webhook_signature, body):
        raise HTTPException(status_code=401, detail="Webhook no autorizado")

    payload = await request.json()

    # Single event or batch
    if "events" in payload:
        batch = OdooWebhookBatchEvent(**payload)
        results = []
        for evt in batch.events:
            result = await _process_event(evt)
            results.append(result)
        return {"success": True, "processed": len(results), "results": results}
    else:
        event = OdooWebhookEvent(**payload)
        result = await _process_event(event)
        return {"success": True, **result}


async def _process_event(event: OdooWebhookEvent) -> Dict[str, Any]:
    """Procesa un evento individual de Odoo."""
    handler = EVENT_HANDLERS.get(event.event)
    if not handler:
        logger.warning(f"Evento Odoo desconocido: {event.event} (tenant={event.tenant_db})")
        return {"event": event.event, "status": "ignored", "reason": "unknown_event"}

    try:
        result = await handler(event.tenant_db, event.data)
        _log_webhook_event(event, "success", result)
        return {"event": event.event, "status": "processed", **result}
    except Exception as e:
        logger.error(f"Error procesando evento {event.event} de {event.tenant_db}: {e}")
        _log_webhook_event(event, "error", {"error": str(e)})
        return {"event": event.event, "status": "error", "error": str(e)}


def _log_webhook_event(event: OdooWebhookEvent, status: str, details: dict):
    """Registra evento webhook en auditoría."""
    db = SessionLocal()
    try:
        audit = AuditEventRecord(
            event_type=f"ODOO_WEBHOOK_{event.event.upper().replace('.', '_')}",
            actor_username="odoo_webhook",
            actor_role="system",
            resource=f"tenant:{event.tenant_db}",
            action=event.event,
            status=status,
            details={
                "tenant_db": event.tenant_db,
                "event_data": event.data,
                "result": details,
            },
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Error logging webhook audit: {e}")
    finally:
        db.close()


def _extract_domain_host(raw_value: Any) -> Optional[str]:
    """Normaliza URLs o dominios planos a hostname."""
    if not raw_value:
        return None

    value = str(raw_value).strip().lower().strip(".")
    if not value:
        return None

    candidate = value if "://" in value else f"//{value}"
    parsed = urlparse(candidate)
    host = (parsed.netloc or parsed.path or "").strip().lower().strip(".")
    host = host.split("/")[0].split(":")[0]
    if not host or "." not in host:
        return None

    return host


def _coerce_positive_int(raw_value: Any) -> Optional[int]:
    """Convierte un valor a entero positivo si aplica."""
    if raw_value is None or raw_value == "":
        return None

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None

    return value if value > 0 else None


def _resolve_plan_name(db, data: Dict[str, Any]) -> str:
    """Resuelve un plan válido para la suscripción espejo."""
    requested = (data.get("plan_name") or data.get("plan") or "basic" or "").strip().lower()
    if not requested:
        requested = "basic"

    plan = db.query(Plan).filter(Plan.name == requested, Plan.is_active == True).first()
    if plan:
        return plan.name

    fallback = db.query(Plan).filter(Plan.name == "basic", Plan.is_active == True).first()
    if fallback:
        return fallback.name

    any_plan = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.id.asc()).first()
    return any_plan.name if any_plan else requested


def _resolve_billing_mode(raw_value: Any) -> BillingMode:
    """Billing mode para suscripciones importadas desde Odoo."""
    if raw_value:
        try:
            return BillingMode(str(raw_value))
        except ValueError:
            pass
    return BillingMode.LEGACY_IMPORTED


def _normalize_snapshot_domains(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Consolida dominios externos reportados por Odoo."""
    items: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _append(raw_value: Any, source: str = "odoo", is_primary: bool = False):
        host = _extract_domain_host(raw_value)
        if not host or host.endswith(".sajet.us") or host in seen:
            return
        seen.add(host)
        items.append({
            "domain": host,
            "source": source,
            "is_primary": bool(is_primary),
        })

    base_url = data.get("base_url")
    base_host = _extract_domain_host(base_url)
    if base_host and not base_host.endswith(".sajet.us"):
        _append(base_host, source="base_url", is_primary=True)

    raw_domains = data.get("domains") or []
    if isinstance(raw_domains, (str, dict)):
        raw_domains = [raw_domains]

    for raw_item in raw_domains:
        if isinstance(raw_item, dict):
            _append(
                raw_item.get("domain") or raw_item.get("host") or raw_item.get("name") or raw_item.get("url"),
                source=raw_item.get("source", "odoo"),
                is_primary=bool(raw_item.get("is_primary")),
            )
        else:
            _append(raw_item)

    return items


def _upsert_customer_from_snapshot(db, tenant_db: str, data: Dict[str, Any]) -> tuple[Customer, bool]:
    """Crea o actualiza el customer local a partir del snapshot Odoo."""
    customer = db.query(Customer).filter(Customer.subdomain == tenant_db).first()
    customer_created = customer is None

    company_name = (
        data.get("company_name")
        or (customer.company_name if customer else None)
        or tenant_db.replace("_", " ").title()
    )
    email = (
        data.get("admin_email")
        or data.get("company_email")
        or (customer.email if customer else None)
        or f"{tenant_db}@sajet.us"
    )
    full_name = (
        data.get("full_name")
        or data.get("company_name")
        or (customer.full_name if customer else None)
        or company_name
    )
    user_count_raw = data.get("user_count") or data.get("billable_user_count") or data.get("seat_count") or 1
    try:
        user_count = max(1, int(user_count_raw))
    except (TypeError, ValueError):
        user_count = max(1, customer.user_count or 1) if customer else 1

    if customer is None:
        customer = Customer(
            email=email,
            full_name=full_name,
            company_name=company_name,
            subdomain=tenant_db,
            phone=data.get("company_phone") or data.get("phone"),
            country=data.get("country"),
            user_count=user_count,
            fair_use_enabled=False,
        )
        db.add(customer)
        db.flush()
    else:
        customer.email = email
        customer.full_name = full_name
        customer.company_name = company_name
        customer.user_count = user_count
        if data.get("company_phone") or data.get("phone"):
            customer.phone = data.get("company_phone") or data.get("phone")
        if data.get("country"):
            customer.country = data.get("country")

    stock_sku_raw = data.get("stock_sku_count") or 0
    try:
        customer.stock_sku_count = max(0, int(stock_sku_raw))
    except (TypeError, ValueError):
        customer.stock_sku_count = max(0, customer.stock_sku_count or 0)
    customer.last_usage_sync_at = datetime.now(timezone.utc).replace(tzinfo=None)

    owner_partner_id = _coerce_positive_int(data.get("owner_partner_id") or data.get("partner_id"))
    if owner_partner_id:
        customer.partner_id = owner_partner_id

    return customer, customer_created


def _upsert_subscription_from_snapshot(db, customer: Customer, data: Dict[str, Any]) -> tuple[Subscription, bool]:
    """Crea o ajusta la suscripción espejo local del tenant sincronizado."""
    subscription = db.query(Subscription).filter(
        Subscription.customer_id == customer.id
    ).order_by(Subscription.id.desc()).first()
    subscription_created = subscription is None

    plan_name = _resolve_plan_name(db, data)
    owner_partner_id = _coerce_positive_int(data.get("owner_partner_id") or data.get("partner_id")) or customer.partner_id

    if subscription is None:
        subscription = Subscription(
            customer_id=customer.id,
            plan_name=plan_name,
            status=SubscriptionStatus.active,
            tenant_provisioned=True,
            user_count=max(1, customer.user_count or 1),
            monthly_amount=0,
            billing_mode=_resolve_billing_mode(data.get("billing_mode")),
            owner_partner_id=owner_partner_id,
        )
        db.add(subscription)
        db.flush()
        recalculate_subscription_monthly_amount(
            db,
            subscription,
            customer=customer,
            user_count=subscription.user_count,
        )
        return subscription, subscription_created

    subscription.user_count = max(1, customer.user_count or subscription.user_count or 1)
    subscription.tenant_provisioned = True
    if owner_partner_id and not subscription.owner_partner_id:
        subscription.owner_partner_id = owner_partner_id
    if subscription.billing_mode is None and not subscription.stripe_subscription_id:
        subscription.billing_mode = _resolve_billing_mode(data.get("billing_mode"))
    if subscription.billing_mode in (None, BillingMode.LEGACY_IMPORTED) and data.get("plan_name"):
        subscription.plan_name = plan_name
    if not subscription.plan_name:
        subscription.plan_name = plan_name
    recalculate_subscription_monthly_amount(
        db,
        subscription,
        customer=customer,
        user_count=subscription.user_count,
    )

    return subscription, subscription_created


def _resolve_latest_tenant_deployment(db, customer: Customer) -> Optional[TenantDeployment]:
    """Busca el deployment más reciente del tenant para asociar dominios."""
    deployment = db.query(TenantDeployment).filter(
        TenantDeployment.customer_id == customer.id
    ).order_by(TenantDeployment.id.desc()).first()
    if deployment:
        return deployment

    return db.query(TenantDeployment).filter(
        TenantDeployment.subdomain == customer.subdomain
    ).order_by(TenantDeployment.id.desc()).first()


def _extract_target_from_deployment(deployment: Optional[TenantDeployment]) -> tuple[str, int]:
    """Obtiene IP/puerto del deployment si existe."""
    from ..config import ODOO_PRIMARY_IP

    target_node_ip = ODOO_PRIMARY_IP
    target_port = 8069

    if not deployment or not deployment.direct_url:
        return target_node_ip, target_port

    direct_url = deployment.direct_url.replace("http://", "").replace("https://", "")
    host = direct_url.split("/")[0]
    parts = host.split(":")
    if parts and parts[0]:
        target_node_ip = parts[0]
    if len(parts) > 1:
        try:
            target_port = int(parts[1])
        except ValueError:
            pass

    return target_node_ip, target_port


def _sync_domains_from_snapshot(db, customer: Customer, data: Dict[str, Any]) -> Dict[str, Any]:
    """Sincroniza dominios públicos reportados por Odoo con custom_domains."""
    domain_entries = _normalize_snapshot_domains(data)
    if not domain_entries:
        return {"created": 0, "updated": 0, "conflicts": [], "domains": []}

    deployment = _resolve_latest_tenant_deployment(db, customer)
    target_node_ip, target_port = _extract_target_from_deployment(deployment)
    primary_domain = next((item["domain"] for item in domain_entries if item.get("is_primary")), None)

    existing_customer_domains = {
        row.external_domain: row
        for row in db.query(CustomDomain).filter(CustomDomain.customer_id == customer.id).all()
    }

    if primary_domain:
        for row in existing_customer_domains.values():
            if row.external_domain != primary_domain and row.is_primary:
                row.is_primary = False

    created = 0
    updated = 0
    conflicts: List[str] = []

    for item in domain_entries:
        host = item["domain"]
        domain = db.query(CustomDomain).filter(CustomDomain.external_domain == host).first()
        if domain and domain.customer_id != customer.id:
            conflicts.append(host)
            continue

        if domain is None:
            domain = CustomDomain(
                customer_id=customer.id,
                tenant_deployment_id=deployment.id if deployment else None,
                external_domain=host,
                sajet_subdomain=customer.subdomain,
                verification_status=DomainVerificationStatus.verified,
                verified_at=datetime.now(timezone.utc).replace(tzinfo=None),
                is_active=True,
                is_primary=bool(item.get("is_primary")),
                target_node_ip=target_node_ip,
                target_port=target_port,
                ssl_status="active",
                created_by="odoo_sync",
            )
            db.add(domain)
            created += 1
            continue

        if deployment and not domain.tenant_deployment_id:
            domain.tenant_deployment_id = deployment.id
        domain.sajet_subdomain = customer.subdomain
        domain.target_node_ip = target_node_ip or domain.target_node_ip
        domain.target_port = target_port or domain.target_port
        domain.is_active = True
        domain.verification_status = DomainVerificationStatus.verified
        if not domain.verified_at:
            domain.verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if primary_domain:
            domain.is_primary = (host == primary_domain)
        elif item.get("is_primary"):
            domain.is_primary = True
        if not domain.ssl_status or domain.ssl_status == "pending":
            domain.ssl_status = "active"
        if not domain.created_by:
            domain.created_by = "odoo_sync"
        updated += 1

    return {
        "created": created,
        "updated": updated,
        "conflicts": conflicts,
        "domains": [item["domain"] for item in domain_entries],
    }


async def _sync_tenant_snapshot(tenant_db: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Reconciliación completa de tenant desde Odoo hacia SAJET."""
    db = SessionLocal()
    try:
        customer, customer_created = _upsert_customer_from_snapshot(db, tenant_db, data)
        subscription, subscription_created = _upsert_subscription_from_snapshot(db, customer, data)
        domain_sync = _sync_domains_from_snapshot(db, customer, data)
        record_hwm_snapshot(
            db,
            subscription,
            user_count_after=max(1, customer.user_count or subscription.user_count or 1),
            source="odoo_snapshot",
            metadata={"tenant_db": tenant_db, "origin_event": "tenant.snapshot"},
        )
        db.commit()

        return {
            "synced": True,
            "customer_created": customer_created,
            "subscription_created": subscription_created,
            "customer_id": customer.id,
            "subscription_id": subscription.id,
            "plan_name": subscription.plan_name,
            "billing_mode": subscription.billing_mode.value if subscription.billing_mode else None,
            "user_count": customer.user_count,
            "domains_created": domain_sync["created"],
            "domains_updated": domain_sync["updated"],
            "domain_conflicts": domain_sync["conflicts"],
            "domains_seen": domain_sync["domains"],
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ═══════════════════════════════════════════════════
# EVENT HANDLERS
# ═══════════════════════════════════════════════════

async def _handle_user_created(tenant_db: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Un usuario fue creado en el tenant Odoo.
    Sincroniza el conteo de usuarios facturables con la suscripción.
    """
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.subdomain == tenant_db).first()
        if not customer:
            return {"synced": False, "reason": "customer_not_found"}

        is_share = data.get("share", False)
        is_active = data.get("active", True)
        if not is_billable_user(
            tenant_db,
            login=data.get("login"),
            share=is_share,
            active=is_active,
            customer=customer,
            admin_email=customer.email,
        ):
            return {
                "synced": False,
                "reason": "non_billable_user",
                "user_login": data.get("login"),
            }

        # Incrementar user_count
        old_count = customer.user_count or 1
        customer.user_count = old_count + 1

        # Recalcular suscripción
        sub = db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
            Subscription.status == SubscriptionStatus.active,
        ).first()

        new_amount = None
        if sub:
            new_amount = recalculate_subscription_monthly_amount(
                db,
                sub,
                customer=customer,
                user_count=customer.user_count,
            )
            record_seat_event(
                db,
                sub,
                event_type=SeatEventType.USER_CREATED,
                user_count_after=customer.user_count,
                odoo_user_id=data.get("user_id"),
                odoo_login=data.get("login"),
                source="odoo_webhook",
                metadata={"tenant_db": tenant_db, "origin_event": "user.created"},
            )

        db.commit()

        logger.info(
            f"Odoo→Portal: user.created en {tenant_db}, "
            f"users {old_count}→{customer.user_count}, "
            f"amount=${new_amount}"
        )

        return {
            "synced": True,
            "user_login": data.get("login"),
            "old_user_count": old_count,
            "new_user_count": customer.user_count,
            "recalculated": bool(sub),
            "new_monthly_amount": new_amount,
        }
    finally:
        db.close()


async def _handle_user_updated(tenant_db: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Un usuario fue actualizado en Odoo (email, active status, etc.).
    Si cambió active status, sincronizar user_count.
    """
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.subdomain == tenant_db).first()
        if not customer:
            return {"synced": False, "reason": "customer_not_found"}

        changes = data.get("changes", {})

        # Si cambió el email del admin, sincronizar con customer.email
        if "login" in changes and data.get("is_admin"):
            customer.email = changes["login"]
            db.commit()
            return {"synced": True, "email_updated": changes["login"]}

        if "active" in changes:
            current_active = bool(data.get("active", False))
            if current_active:
                return await _handle_user_created(tenant_db, data)
            return await _handle_user_deleted(tenant_db, data)

        return {"synced": False, "reason": "no_relevant_changes"}
    finally:
        db.close()


async def _handle_user_deleted(tenant_db: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Un usuario fue desactivado/eliminado en Odoo.
    Decrementar user_count y recalcular.
    """
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.subdomain == tenant_db).first()
        if not customer:
            return {"synced": False, "reason": "customer_not_found"}

        is_share = data.get("share", False)
        if not is_billable_user(
            tenant_db,
            login=data.get("login"),
            share=is_share,
            active=True,
            customer=customer,
            admin_email=customer.email,
        ):
            return {"synced": False, "reason": "non_billable_user"}

        old_count = customer.user_count or 1
        customer.user_count = max(1, old_count - 1)

        sub = db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
            Subscription.status == SubscriptionStatus.active,
        ).first()

        new_amount = None
        if sub:
            new_amount = recalculate_subscription_monthly_amount(
                db,
                sub,
                customer=customer,
                user_count=customer.user_count,
            )
            record_seat_event(
                db,
                sub,
                event_type=SeatEventType.USER_DEACTIVATED,
                user_count_after=customer.user_count,
                odoo_user_id=data.get("user_id"),
                odoo_login=data.get("login"),
                source="odoo_webhook",
                metadata={"tenant_db": tenant_db, "origin_event": "user.deleted"},
            )

        db.commit()

        logger.info(
            f"Odoo→Portal: user.deleted en {tenant_db}, "
            f"users {old_count}→{customer.user_count}"
        )

        return {
            "synced": True,
            "user_login": data.get("login"),
            "old_user_count": old_count,
            "new_user_count": customer.user_count,
            "new_monthly_amount": new_amount,
        }
    finally:
        db.close()


async def _handle_partner_created(tenant_db: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Un res.partner (contacto/cliente) fue creado en Odoo.
    Esto es informativo — no cambia facturación directamente.
    Puede usarse para lead tracking futuro.
    """
    return {
        "synced": True,
        "action": "logged",
        "partner_name": data.get("name"),
        "partner_email": data.get("email"),
        "note": "Partner creation logged for future lead tracking",
    }


async def _handle_tenant_config_changed(tenant_db: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Configuración del tenant cambió en Odoo (nombre empresa, etc.).
    Sincronizar snapshot local del tenant en ERP Core.
    """
    return await _sync_tenant_snapshot(tenant_db, data)


async def _handle_tenant_snapshot(tenant_db: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Snapshot periódico/completo del tenant."""
    return await _sync_tenant_snapshot(tenant_db, data)


# Event handler registry
EVENT_HANDLERS = {
    "user.created": _handle_user_created,
    "user.updated": _handle_user_updated,
    "user.deleted": _handle_user_deleted,
    "partner.created": _handle_partner_created,
    "tenant.config_changed": _handle_tenant_config_changed,
    "tenant.snapshot": _handle_tenant_snapshot,
}


# ═══════════════════════════════════════════════════
# HEALTH CHECK para que Odoo valide la conexión
# ═══════════════════════════════════════════════════

@router.get("/health")
async def webhook_health():
    """Health check para que el módulo Odoo valide la conexión."""
    return {
        "status": "ok",
        "service": "erp_core_odoo_webhooks",
        "supported_events": list(EVENT_HANDLERS.keys()),
    }
