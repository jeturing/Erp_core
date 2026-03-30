"""
Postal Mail Service — Integración con el relay interno (CT 200 / 10.10.10.151)

Responsabilidades:
  1. Recibir webhooks de delivery de Postal → actualizar postal_email_usage
  2. Sync periódico de métricas via API de Postal
  3. Calcular costo por envío para billing de tenants
  4. Exponer stats de uso por tenant / período
"""
import logging
import os
import re
from datetime import datetime, date
from typing import Optional, Dict, Any, List

import httpx

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Configuración de Postal (desde env)
# ──────────────────────────────────────────────
POSTAL_BASE_URL    = os.getenv("POSTAL_BASE_URL",    "https://mail.sajet.us")
POSTAL_API_KEY     = os.getenv("POSTAL_API_KEY",     "")          # API key del servidor "Sajet Relay"
POSTAL_SERVER_TOKEN = os.getenv("POSTAL_SERVER_TOKEN", "ymxm3g")  # Token del servidor Sajet Relay
POSTAL_SMTP_KEY    = os.getenv("POSTAL_SMTP_KEY",    "IkTvoLe4S8M2wNx3AqAVXsQH")
COST_PER_EMAIL     = float(os.getenv("POSTAL_COST_PER_EMAIL", "0.00020"))


# ──────────────────────────────────────────────
# Helpers BD
# ──────────────────────────────────────────────

def _get_or_create_usage(db, tenant_subdomain: str, year: int, month: int,
                          customer_id: Optional[int] = None):
    """
    Obtiene o crea el registro mensual de uso para el tenant.
    """
    from ..models.database import PostalEmailUsage
    rec = db.query(PostalEmailUsage).filter(
        PostalEmailUsage.tenant_subdomain == tenant_subdomain,
        PostalEmailUsage.period_year  == year,
        PostalEmailUsage.period_month == month,
    ).first()
    if not rec:
        rec = PostalEmailUsage(
            tenant_subdomain=tenant_subdomain,
            customer_id=customer_id,
            period_year=year,
            period_month=month,
            cost_per_email=COST_PER_EMAIL,
        )
        db.add(rec)
    return rec


def _extract_tenant(from_addr: str, to_addr: str) -> Optional[str]:
    """
    Intenta extraer el subdomain del tenant a partir del remitente o destinatario.
    Regla: el from suele ser algo como info@<subdomain>.sajet.us
    """
    for addr in [from_addr, to_addr]:
        if not addr:
            continue
        m = re.search(r'@([a-z0-9_-]+)\.sajet\.us', addr.lower())
        if m:
            sub = m.group(1)
            if sub not in ("mail", "sajet", "no-reply", "api"):
                return sub
    return None


# ──────────────────────────────────────────────
# Webhook handler  (llamado desde la ruta API)
# ──────────────────────────────────────────────

EMAIL_PACKAGE_SERVICE_CODE = "postal_email_package"


def _get_tenant_email_quota(db, tenant_subdomain: str) -> Optional[int]:
    """
    Retorna la cuota mensual del tenant si tiene un paquete de email activo,
    o None si no tiene suscripción activa.
    """
    from ..models.database import CustomerAddonSubscription, Customer, ServiceCatalogItem
    # Buscar customer por subdomain
    customer = db.query(Customer).filter(
        Customer.subdomain == tenant_subdomain
    ).first()
    if not customer:
        return None

    # Buscar suscripción activa al paquete de email
    sub = (
        db.query(CustomerAddonSubscription)
        .filter(
            CustomerAddonSubscription.customer_id == customer.id,
            CustomerAddonSubscription.service_code == EMAIL_PACKAGE_SERVICE_CODE,
            CustomerAddonSubscription.status == "active",
        )
        .order_by(CustomerAddonSubscription.id.desc())
        .first()
    )
    if not sub:
        return None

    # La cuota está en el catalog_item.metadata_json
    if sub.catalog_item_id:
        cat_item = db.query(ServiceCatalogItem).filter(
            ServiceCatalogItem.id == sub.catalog_item_id
        ).first()
        if cat_item and cat_item.metadata_json:
            return cat_item.metadata_json.get("email_quota_monthly")

    # Fallback: buscarlo en la metadata de la propia suscripción
    if sub.metadata_json:
        return sub.metadata_json.get("email_quota_monthly")

    return None


async def _suspend_postal_server(server_token: str) -> bool:
    """
    Suspende el servidor de mail en Postal vía API REST.
    Esto detiene la aceptación de nuevos mensajes del tenant.
    """
    if not POSTAL_API_KEY:
        logger.warning("POSTAL_API_KEY no configurada — suspensión omitida")
        return False
    try:
        async with httpx.AsyncClient(timeout=10, verify=False) as client:
            resp = await client.put(
                f"{POSTAL_BASE_URL}/api/v1/servers/{server_token}",
                headers={"X-Server-API-Key": POSTAL_API_KEY, "Content-Type": "application/json"},
                json={"mode": "suspended"},
            )
            if resp.status_code in (200, 201):
                logger.warning(f"📴 Postal server {server_token} suspendido por cuota excedida")
                return True
            else:
                logger.error(f"Error suspendiendo servidor Postal {server_token}: {resp.status_code} {resp.text[:200]}")
                return False
    except Exception as e:
        logger.error(f"Error en _suspend_postal_server: {e}")
        return False


def _check_and_enforce_quota(db, tenant_subdomain: str, current_sent: int) -> None:
    """
    Verifica si el tenant superó su cuota mensual de correos.
    Si se superó, lanza la suspensión del servidor Postal en background
    y registra el evento en el log.
    Esta función es síncrona — la suspensión asíncrona se delega a un hilo.
    """
    try:
        quota = _get_tenant_email_quota(db, tenant_subdomain)
        if quota is None:
            return  # Sin suscripción activa — no hay cuota que enforcer

        if current_sent >= quota:
            logger.warning(
                f"⚠️  Tenant {tenant_subdomain} superó cuota: "
                f"{current_sent}/{quota} correos este mes"
            )
            # Lanzar suspensión async sin bloquear el webhook (best-effort)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Contexto async (FastAPI) — crear tarea
                    asyncio.ensure_future(
                        _suspend_postal_server(POSTAL_SERVER_TOKEN)
                    )
                else:
                    loop.run_until_complete(
                        _suspend_postal_server(POSTAL_SERVER_TOKEN)
                    )
            except RuntimeError:
                # No hay loop disponible — loguear y continuar
                logger.error(
                    f"No se pudo suspender el servidor Postal para {tenant_subdomain}: "
                    "no hay event loop disponible"
                )
    except Exception as e:
        logger.error(f"Error en _check_and_enforce_quota para {tenant_subdomain}: {e}")

def handle_postal_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa un webhook de Postal (evento de mensaje: delivered, bounced, failed).

    Payload esperado (Postal webhook format):
    {
      "event":   "MessageDelivered" | "MessageBounced" | "MessageFailed",
      "payload": {
        "message": {
          "id": 1234,
          "from": "remitente@tenant.sajet.us",
          "to": "destino@example.com",
          "subject": "...",
          "timestamp": "2026-03-27T10:00:00Z"
        }
      }
    }
    """
    try:
        from ..models.database import PostalEmailUsage, SessionLocal
        event   = payload.get("event", "")
        message = payload.get("payload", {}).get("message", {})
        from_   = message.get("from", "")
        to_     = message.get("to", "")
        ts_str  = message.get("timestamp") or datetime.utcnow().isoformat()

        # Parsear timestamp
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            ts = datetime.utcnow()

        year, month = ts.year, ts.month

        # Determinar tenant
        tenant = _extract_tenant(from_, to_) or "__unknown__"

        db = SessionLocal()
        try:
            rec = _get_or_create_usage(db, tenant, year, month)
            if "Delivered" in event:
                rec.emails_sent      += 1
                rec.emails_delivered += 1
            elif "Bounced" in event:
                rec.emails_sent    += 1
                rec.emails_bounced += 1
            elif "Failed" in event:
                rec.emails_sent   += 1
                rec.emails_failed += 1
            else:
                # Evento genérico / desconocido — contabilizar como sent
                rec.emails_sent += 1

            rec.total_cost_usd   = rec.emails_sent * rec.cost_per_email
            rec.last_synced_at   = datetime.utcnow()
            rec.postal_server_token = POSTAL_SERVER_TOKEN
            db.commit()
            logger.info(f"📧 Postal webhook: tenant={tenant} event={event} "
                        f"sent={rec.emails_sent} cost=${rec.total_cost_usd:.4f}")

            # ── Quota enforcement ──────────────────────────────────────
            # Si el tenant tiene un paquete de email activo, verificar si superó la cuota.
            # En caso de superarla, suspender el servidor de mail en Postal via API.
            if tenant != "__unknown__":
                _check_and_enforce_quota(db, tenant, rec.emails_sent)

        except Exception as e:
            db.rollback()
            logger.error(f"Error procesando webhook Postal: {e}")
        finally:
            db.close()

        return {"success": True, "tenant": tenant, "event": event}

    except Exception as e:
        logger.error(f"Error en handle_postal_webhook: {e}")
        return {"success": False, "error": str(e)}


# ──────────────────────────────────────────────
# API de Postal — Sync de estadísticas
# ──────────────────────────────────────────────

async def sync_postal_stats(year: Optional[int] = None, month: Optional[int] = None) -> Dict[str, Any]:
    """
    Consulta la API REST de Postal para sincronizar estadísticas de mensajes
    del período indicado (default: mes actual).

    Endpoint Postal: GET /api/v1/messages/deliveries
    Requiere: X-Server-API-Key header con POSTAL_API_KEY
    """
    if not POSTAL_API_KEY:
        logger.warning("POSTAL_API_KEY no configurada — sync omitido")
        return {"success": False, "error": "POSTAL_API_KEY not set"}

    now = datetime.utcnow()
    year  = year  or now.year
    month = month or now.month

    # Fechas del período
    from_dt = datetime(year, month, 1)
    if month == 12:
        to_dt = datetime(year + 1, 1, 1)
    else:
        to_dt = datetime(year, month + 1, 1)

    headers = {"X-Server-API-Key": POSTAL_API_KEY, "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            resp = await client.post(
                f"{POSTAL_BASE_URL}/api/v1/messages/search",
                headers=headers,
                json={
                    "criteria": {
                        "status": ["delivered", "bounced", "failed"],
                        "from_date": from_dt.strftime("%Y-%m-%d"),
                        "to_date": to_dt.strftime("%Y-%m-%d"),
                    },
                    "pagination": {"page": 1, "per_page": 1000},
                },
            )
            if resp.status_code != 200:
                logger.warning(f"Postal API error {resp.status_code}: {resp.text[:200]}")
                return {"success": False, "error": f"HTTP {resp.status_code}"}

            data = resp.json()
            messages = data.get("data", {}).get("messages", [])

    except Exception as e:
        logger.error(f"Error conectando con Postal API: {e}")
        return {"success": False, "error": str(e)}

    # Agrupar por tenant
    stats: Dict[str, Dict] = {}
    for msg in messages:
        from_  = msg.get("from", "")
        to_    = msg.get("to", "")
        status = msg.get("status", "delivered")
        tenant = _extract_tenant(from_, to_) or "__unknown__"

        if tenant not in stats:
            stats[tenant] = {"sent": 0, "delivered": 0, "bounced": 0, "failed": 0}
        stats[tenant]["sent"] += 1
        if status == "delivered":
            stats[tenant]["delivered"] += 1
        elif status == "bounced":
            stats[tenant]["bounced"] += 1
        elif status == "failed":
            stats[tenant]["failed"] += 1

    # Persistir en BD
    from ..models.database import PostalEmailUsage, SessionLocal
    db = SessionLocal()
    updated = []
    try:
        for tenant, s in stats.items():
            rec = _get_or_create_usage(db, tenant, year, month)
            rec.emails_sent      = s["sent"]
            rec.emails_delivered = s["delivered"]
            rec.emails_bounced   = s["bounced"]
            rec.emails_failed    = s["failed"]
            rec.total_cost_usd   = s["sent"] * rec.cost_per_email
            rec.last_synced_at   = datetime.utcnow()
            rec.postal_server_token = POSTAL_SERVER_TOKEN
            updated.append({"tenant": tenant, **s, "cost": s["sent"] * COST_PER_EMAIL})
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error sincronizando stats Postal: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

    logger.info(f"✅ Postal sync: {len(updated)} tenants actualizados para {year}-{month:02d}")
    return {"success": True, "period": f"{year}-{month:02d}", "tenants_updated": updated}


# ──────────────────────────────────────────────
# Consultas de uso
# ──────────────────────────────────────────────

def get_tenant_email_usage(
    tenant_subdomain: str,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Retorna el uso de email del tenant en el período dado.
    Si no se pasa año/mes, devuelve el mes actual.
    """
    from ..models.database import PostalEmailUsage, SessionLocal
    now   = datetime.utcnow()
    year  = year  or now.year
    month = month or now.month

    db = SessionLocal()
    try:
        rec = db.query(PostalEmailUsage).filter(
            PostalEmailUsage.tenant_subdomain == tenant_subdomain,
            PostalEmailUsage.period_year  == year,
            PostalEmailUsage.period_month == month,
        ).first()
        if not rec:
            return {
                "tenant": tenant_subdomain, "period": f"{year}-{month:02d}",
                "emails_sent": 0, "emails_delivered": 0,
                "emails_bounced": 0, "emails_failed": 0,
                "cost_per_email": COST_PER_EMAIL,
                "total_cost_usd": 0.0, "is_billed": False,
            }
        return {
            "tenant": rec.tenant_subdomain,
            "period": f"{rec.period_year}-{rec.period_month:02d}",
            "emails_sent": rec.emails_sent,
            "emails_delivered": rec.emails_delivered,
            "emails_bounced": rec.emails_bounced,
            "emails_failed": rec.emails_failed,
            "cost_per_email": rec.cost_per_email,
            "total_cost_usd": round(rec.total_cost_usd, 6),
            "is_billed": rec.is_billed,
            "last_synced_at": rec.last_synced_at.isoformat() if rec.last_synced_at else None,
        }
    finally:
        db.close()


def get_all_tenants_email_usage_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Resumen de uso de correo de todos los tenants para el período dado.
    Útil para el panel de administración y generación de facturas.
    """
    from ..models.database import PostalEmailUsage, SessionLocal
    now   = datetime.utcnow()
    year  = year  or now.year
    month = month or now.month

    db = SessionLocal()
    try:
        rows = db.query(PostalEmailUsage).filter(
            PostalEmailUsage.period_year  == year,
            PostalEmailUsage.period_month == month,
        ).order_by(PostalEmailUsage.total_cost_usd.desc()).all()

        return [
            {
                "tenant": r.tenant_subdomain,
                "emails_sent": r.emails_sent,
                "emails_delivered": r.emails_delivered,
                "emails_bounced": r.emails_bounced,
                "total_cost_usd": round(r.total_cost_usd, 6),
                "is_billed": r.is_billed,
            }
            for r in rows
        ]
    finally:
        db.close()
