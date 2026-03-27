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
"""
import hmac
import hashlib
import logging
import os
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from ..models.database import (
    Customer, Subscription, SubscriptionStatus, Plan,
    SessionLocal, AuditEventRecord,
)
from ..config import PROVISIONING_API_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/odoo", tags=["Odoo Webhooks"])

# Shared secret for webhook HMAC validation
ODOO_WEBHOOK_SECRET = os.getenv("ODOO_WEBHOOK_SECRET", PROVISIONING_API_KEY)


def _verify_webhook(x_api_key: Optional[str], x_webhook_signature: Optional[str], body: bytes) -> bool:
    """
    Verifica autenticidad del webhook.
    Acepta API key directa O firma HMAC del body.
    """
    # Method 1: Direct API key
    if x_api_key and x_api_key == PROVISIONING_API_KEY:
        return True

    # Method 2: HMAC signature
    if x_webhook_signature and ODOO_WEBHOOK_SECRET:
        expected = hmac.new(
            ODOO_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, x_webhook_signature)

    return False


class OdooWebhookEvent(BaseModel):
    """Evento genérico desde Odoo."""
    event: str  # user.created, user.updated, user.deleted, partner.created, tenant.config_changed
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
        is_admin = data.get("login", "").lower() in ("admin", f"{tenant_db}@sajet.us")
        is_active = data.get("active", True)

        # Solo contar usuarios facturables (activos, no share, no admin)
        if is_share or is_admin or not is_active:
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

        recalculated = False
        new_amount = None
        if sub:
            sub.user_count = customer.user_count
            plan = db.query(Plan).filter(Plan.name == sub.plan_name).first()
            if plan:
                effective_pid = sub.owner_partner_id or customer.partner_id
                new_amount = plan.calculate_monthly(customer.user_count, partner_id=effective_pid)
                sub.monthly_amount = new_amount
                recalculated = True

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
            "recalculated": recalculated,
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

        # Si cambió active status, necesitamos recalcular seat count
        # Para esto necesitamos un full sync — mejor hacerlo vía el endpoint de sync
        if "active" in changes:
            return {
                "synced": False,
                "reason": "active_change_needs_full_sync",
                "hint": "Call POST /api/provisioning/tenant/accounts/sync-seat-count",
            }

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
        is_admin = data.get("login", "").lower() in ("admin", f"{tenant_db}@sajet.us")

        if is_share or is_admin:
            return {"synced": False, "reason": "non_billable_user"}

        old_count = customer.user_count or 1
        customer.user_count = max(1, old_count - 1)

        sub = db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
            Subscription.status == SubscriptionStatus.active,
        ).first()

        new_amount = None
        if sub:
            sub.user_count = customer.user_count
            plan = db.query(Plan).filter(Plan.name == sub.plan_name).first()
            if plan:
                effective_pid = sub.owner_partner_id or customer.partner_id
                new_amount = plan.calculate_monthly(customer.user_count, partner_id=effective_pid)
                sub.monthly_amount = new_amount

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
    Sincronizar con Customer en ERP Core.
    """
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.subdomain == tenant_db).first()
        if not customer:
            return {"synced": False, "reason": "customer_not_found"}

        changes = []
        if "company_name" in data and data["company_name"]:
            customer.company_name = data["company_name"]
            changes.append(f"company_name={data['company_name']}")

        if changes:
            db.commit()
            return {"synced": True, "changes": changes}

        return {"synced": False, "reason": "no_changes"}
    finally:
        db.close()


# Event handler registry
EVENT_HANDLERS = {
    "user.created": _handle_user_created,
    "user.updated": _handle_user_updated,
    "user.deleted": _handle_user_deleted,
    "partner.created": _handle_partner_created,
    "tenant.config_changed": _handle_tenant_config_changed,
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
