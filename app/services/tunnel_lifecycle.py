"""
Tunnel Lifecycle Manager — Vincula Cloudflare Tunnels a Clientes vía Stripe.

Flujo completo:
  1. Cliente se suscribe → Stripe checkout → Subscription.status = active
  2. Se asigna TenantDeployment + Tunnel al cliente
  3. Si Stripe reporta past_due / cancelled → tunnel se suspende (DNS removido o deployment desactivado)
  4. Si Stripe reactiva → tunnel se reactiva (DNS restaurado)
  5. Dashboard muestra: Cliente → Tunnel → Estado Stripe → Health

Acciones automáticas por estado de suscripción:
  - active          → tunnel_active=True,  DNS CNAME activo
  - past_due        → tunnel_active=False, DNS removido (gracia 3 días en Stripe)
  - suspended       → tunnel_active=False, DNS removido
  - cancelled       → tunnel_active=False, DNS removido, deployment marcado inactivo
  - pending         → tunnel_active=False  (aún no pagó)
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..models.database import (
    SessionLocal, TenantDeployment, Subscription, Customer,
    SubscriptionStatus,
)
from .cloudflare_manager import CloudflareManager

logger = logging.getLogger(__name__)

# Estados que permiten tunnel activo
ACTIVE_STATUSES = {SubscriptionStatus.active}

# Estados que requieren suspensión del tunnel
SUSPEND_STATUSES = {
    SubscriptionStatus.past_due,
    SubscriptionStatus.suspended,
    SubscriptionStatus.cancelled,
}


async def link_tunnel_to_customer(
    customer_id: int,
    tunnel_id: str,
    deployment_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Vincula un tunnel de Cloudflare a un cliente.
    
    1. Busca el TenantDeployment del cliente (por deployment_id o por subscription)
    2. Actualiza customer_id + tunnel_id en el deployment
    3. Verifica estado de suscripción Stripe
    4. Si activa → crea DNS CNAME, activa tunnel
    5. Si no activa → marca tunnel_active=False
    """
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return {"success": False, "error": "Cliente no encontrado"}

        # Verificar que el tunnel existe en Cloudflare
        cf_result = await CloudflareManager.get_tunnel(tunnel_id)
        if not cf_result.get("success"):
            return {"success": False, "error": "Tunnel no existe en Cloudflare"}

        tunnel_info = cf_result["tunnel"]
        tunnel_name = tunnel_info.get("name", tunnel_id)

        # Encontrar el deployment
        deployment = None
        if deployment_id:
            deployment = db.query(TenantDeployment).filter_by(id=deployment_id).first()
        else:
            # Buscar deployment por subscriptions del cliente
            subs = db.query(Subscription).filter_by(customer_id=customer_id).all()
            for sub in subs:
                dep = db.query(TenantDeployment).filter_by(subscription_id=sub.id).first()
                if dep:
                    deployment = dep
                    break

        if not deployment:
            return {
                "success": False,
                "error": "No hay deployment para este cliente. Primero provisione el tenant.",
            }

        # Desvincular otros deployments de este tunnel
        existing = db.query(TenantDeployment).filter(
            TenantDeployment.tunnel_id == tunnel_id,
            TenantDeployment.id != deployment.id,
        ).all()
        for ex in existing:
            ex.tunnel_id = None
            ex.tunnel_active = False

        # Vincular
        deployment.tunnel_id = tunnel_id
        deployment.customer_id = customer_id

        # Obtener suscripción para verificar estado
        subscription = db.query(Subscription).filter_by(id=deployment.subscription_id).first()

        # Determinar si activar el tunnel
        should_activate = False
        if subscription and subscription.status in ACTIVE_STATUSES:
            should_activate = True

        if should_activate:
            deployment.tunnel_active = True
            # Crear DNS CNAME si tiene subdomain
            subdomain = deployment.subdomain or customer.subdomain
            if subdomain:
                dns_result = await CloudflareManager.create_dns_record(
                    subdomain=subdomain,
                    tunnel_id=tunnel_id,
                )
                if dns_result.get("success"):
                    deployment.tunnel_url = f"{subdomain}.sajet.us"
                    logger.info(f"✅ DNS CNAME creado: {subdomain}.sajet.us → tunnel {tunnel_id}")
                else:
                    # Puede que ya exista el CNAME
                    logger.warning(f"DNS CNAME no creado (puede existir): {dns_result.get('error')}")
                    deployment.tunnel_url = f"{subdomain}.sajet.us"
        else:
            deployment.tunnel_active = False
            status_str = subscription.status.value if subscription else "sin suscripción"
            logger.info(f"⏸️ Tunnel vinculado pero inactivo (estado: {status_str})")

        db.commit()

        return {
            "success": True,
            "message": f"Tunnel '{tunnel_name}' vinculado a cliente '{customer.company_name}'",
            "customer_id": customer_id,
            "company_name": customer.company_name,
            "tunnel_id": tunnel_id,
            "tunnel_name": tunnel_name,
            "tunnel_active": deployment.tunnel_active,
            "tunnel_url": deployment.tunnel_url,
            "subscription_status": subscription.status.value if subscription else None,
            "stripe_subscription_id": subscription.stripe_subscription_id if subscription else None,
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Error vinculando tunnel a cliente: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


async def sync_tunnel_lifecycle(subscription_id: int) -> Dict[str, Any]:
    """
    Sincroniza el estado del tunnel con el estado de la suscripción.
    
    Llamado por:
      - Webhook de Stripe (subscription.updated, invoice.payment_failed)
      - Cron de reconciliación
      - Admin manual
      
    Lógica:
      - Si status = active → activar tunnel + restaurar DNS
      - Si status = past_due/suspended/cancelled → desactivar tunnel + remover DNS
    """
    db = SessionLocal()
    try:
        subscription = db.query(Subscription).filter_by(id=subscription_id).first()
        if not subscription:
            return {"success": False, "error": f"Subscription {subscription_id} no encontrada"}

        deployment = db.query(TenantDeployment).filter_by(subscription_id=subscription_id).first()
        if not deployment:
            return {
                "success": False,
                "error": f"No hay deployment para subscription {subscription_id}",
            }

        customer = None
        if deployment.customer_id:
            customer = db.query(Customer).filter_by(id=deployment.customer_id).first()
        elif subscription.customer_id:
            customer = db.query(Customer).filter_by(id=subscription.customer_id).first()

        tunnel_id = deployment.tunnel_id
        if not tunnel_id:
            return {
                "success": True,
                "message": "Deployment sin tunnel vinculado — nada que sincronizar",
                "action": "none",
            }

        action = "none"
        subdomain = deployment.subdomain or (customer.subdomain if customer else None)

        if subscription.status in ACTIVE_STATUSES:
            # ═══ ACTIVAR TUNNEL ═══
            if not deployment.tunnel_active:
                deployment.tunnel_active = True
                action = "activated"

                # Restaurar DNS si no existe
                if subdomain:
                    dns_result = await CloudflareManager.create_dns_record(
                        subdomain=subdomain,
                        tunnel_id=tunnel_id,
                    )
                    if dns_result.get("success"):
                        deployment.tunnel_url = f"{subdomain}.sajet.us"
                        logger.info(f"✅ DNS restaurado: {subdomain}.sajet.us")
                    else:
                        logger.info(f"DNS ya existente o error: {dns_result.get('error')}")
                        deployment.tunnel_url = f"{subdomain}.sajet.us"

                logger.info(
                    f"🟢 Tunnel {tunnel_id} ACTIVADO para "
                    f"{customer.company_name if customer else 'cliente'} "
                    f"(subscription {subscription_id})"
                )
            else:
                action = "already_active"

        elif subscription.status in SUSPEND_STATUSES:
            # ═══ SUSPENDER TUNNEL ═══
            if deployment.tunnel_active:
                deployment.tunnel_active = False
                action = "suspended"

                # Remover DNS CNAME
                if subdomain:
                    await _remove_dns_for_subdomain(subdomain)

                logger.info(
                    f"🔴 Tunnel {tunnel_id} SUSPENDIDO para "
                    f"{customer.company_name if customer else 'cliente'} "
                    f"(status: {subscription.status.value})"
                )
            else:
                action = "already_suspended"
        else:
            # pending u otro — mantener inactivo
            if deployment.tunnel_active:
                deployment.tunnel_active = False
                action = "deactivated_pending"

        db.commit()

        return {
            "success": True,
            "action": action,
            "subscription_id": subscription_id,
            "subscription_status": subscription.status.value,
            "tunnel_id": tunnel_id,
            "tunnel_active": deployment.tunnel_active,
            "tunnel_url": deployment.tunnel_url,
            "customer": customer.company_name if customer else None,
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Error sincronizando tunnel lifecycle: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


async def sync_all_tunnels() -> Dict[str, Any]:
    """
    Sincroniza TODOS los tunnels con el estado actual de sus suscripciones.
    Útil para reconciliación masiva (cron o admin manual).
    """
    db = SessionLocal()
    results = []
    try:
        deployments = db.query(TenantDeployment).filter(
            TenantDeployment.tunnel_id.isnot(None)
        ).all()

        for dep in deployments:
            result = await sync_tunnel_lifecycle(dep.subscription_id)
            results.append({
                "deployment_id": dep.id,
                "subdomain": dep.subdomain,
                **result,
            })

        activated = sum(1 for r in results if r.get("action") == "activated")
        suspended = sum(1 for r in results if r.get("action") == "suspended")

        return {
            "success": True,
            "total": len(results),
            "activated": activated,
            "suspended": suspended,
            "details": results,
        }
    except Exception as e:
        logger.exception(f"Error en sync_all_tunnels: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


async def get_customer_tunnel_info(customer_id: int) -> Dict[str, Any]:
    """
    Obtiene información completa del tunnel de un cliente.
    Retorna: estado tunnel, DNS, suscripción Stripe, URLs.
    """
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return {"success": False, "error": "Cliente no encontrado"}

        # Buscar deployment directo por customer_id
        deployment = db.query(TenantDeployment).filter_by(customer_id=customer_id).first()

        # Fallback: buscar por subscriptions
        if not deployment:
            subs = db.query(Subscription).filter_by(customer_id=customer_id).all()
            for sub in subs:
                dep = db.query(TenantDeployment).filter_by(subscription_id=sub.id).first()
                if dep:
                    deployment = dep
                    break

        if not deployment:
            return {
                "success": True,
                "customer_id": customer_id,
                "company_name": customer.company_name,
                "has_tunnel": False,
                "message": "Sin deployment/tunnel asignado",
            }

        # Info de suscripción
        subscription = db.query(Subscription).filter_by(id=deployment.subscription_id).first()

        # Info del tunnel en Cloudflare (si tiene)
        cf_status = None
        if deployment.tunnel_id:
            try:
                cf_result = await CloudflareManager.get_tunnel(deployment.tunnel_id)
                if cf_result.get("success"):
                    t = cf_result["tunnel"]
                    cf_status = {
                        "id": t.get("id"),
                        "name": t.get("name"),
                        "status": t.get("status"),
                        "connections_count": t.get("connections_count", 0),
                    }
            except Exception:
                pass

        return {
            "success": True,
            "customer_id": customer_id,
            "company_name": customer.company_name,
            "has_tunnel": bool(deployment.tunnel_id),
            "deployment": {
                "id": deployment.id,
                "subdomain": deployment.subdomain,
                "database_name": deployment.database_name,
                "tunnel_url": deployment.tunnel_url,
                "direct_url": deployment.direct_url,
                "tunnel_active": deployment.tunnel_active,
                "tunnel_id": deployment.tunnel_id,
                "plan_type": deployment.plan_type.value if deployment.plan_type else None,
            },
            "subscription": {
                "id": subscription.id,
                "status": subscription.status.value,
                "plan_name": subscription.plan_name,
                "stripe_subscription_id": subscription.stripe_subscription_id,
                "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            } if subscription else None,
            "cloudflare": cf_status,
        }
    except Exception as e:
        logger.exception(f"Error obteniendo tunnel info: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


async def handle_stripe_subscription_event(
    stripe_subscription_id: str,
    new_status: str,
) -> Dict[str, Any]:
    """
    Handler principal para eventos de Stripe que afectan tunnels.
    
    Llamado desde el webhook cuando llega:
      - customer.subscription.updated  (status cambió)
      - customer.subscription.deleted  (cancelación)
      - invoice.payment_failed         (pago fallido → past_due)
      
    Mapea stripe_subscription_id → Subscription local → sync_tunnel_lifecycle
    """
    db = SessionLocal()
    try:
        subscription = db.query(Subscription).filter_by(
            stripe_subscription_id=stripe_subscription_id
        ).first()

        if not subscription:
            logger.warning(f"Stripe sub {stripe_subscription_id} no encontrada en BD")
            return {"success": False, "error": "Subscription no encontrada en BD"}

        # Mapear status de Stripe a nuestro enum
        status_map = {
            "active": SubscriptionStatus.active,
            "past_due": SubscriptionStatus.past_due,
            "canceled": SubscriptionStatus.cancelled,
            "cancelled": SubscriptionStatus.cancelled,
            "unpaid": SubscriptionStatus.suspended,
            "incomplete": SubscriptionStatus.pending,
            "incomplete_expired": SubscriptionStatus.cancelled,
            "trialing": SubscriptionStatus.active,
            "paused": SubscriptionStatus.suspended,
        }

        mapped_status = status_map.get(new_status)
        if not mapped_status:
            logger.warning(f"Status Stripe desconocido: {new_status}")
            return {"success": False, "error": f"Status desconocido: {new_status}"}

        old_status = subscription.status
        subscription.status = mapped_status
        db.commit()

        logger.info(
            f"📋 Stripe event: sub {stripe_subscription_id} "
            f"{old_status.value} → {mapped_status.value}"
        )

        # Sincronizar tunnel
        result = await sync_tunnel_lifecycle(subscription.id)

        return {
            "success": True,
            "subscription_id": subscription.id,
            "old_status": old_status.value,
            "new_status": mapped_status.value,
            "tunnel_action": result.get("action"),
            "tunnel_active": result.get("tunnel_active"),
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Error procesando evento Stripe: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


async def _remove_dns_for_subdomain(subdomain: str, domain: str = "sajet.us"):
    """
    Busca y elimina el CNAME DNS de un subdomain en Cloudflare.
    """
    try:
        records = await CloudflareManager.list_dns_records(domain=domain, record_type="CNAME")
        if not records.get("success"):
            return

        full_name = f"{subdomain}.{domain}"
        for record in records.get("records", []):
            if record.get("name") == full_name and ".cfargotunnel.com" in record.get("content", ""):
                del_result = await CloudflareManager.delete_dns_record(
                    record["id"], domain=domain
                )
                if del_result.get("success"):
                    logger.info(f"🗑️ DNS CNAME eliminado: {full_name}")
                else:
                    logger.warning(f"Error eliminando DNS {full_name}: {del_result}")
                break
    except Exception as e:
        logger.warning(f"Error removiendo DNS para {subdomain}: {e}")


async def provision_tunnel_for_customer(
    customer_id: int,
    tunnel_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Provisiona un tunnel completo para un cliente:
    1. Crea tunnel en Cloudflare
    2. Lo vincula al deployment del cliente
    3. Crea DNS CNAME
    4. Activa si suscripción está activa
    
    Flujo end-to-end para nuevos clientes.
    """
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            return {"success": False, "error": "Cliente no encontrado"}

        # Nombre del tunnel basado en subdomain del cliente
        name = tunnel_name or customer.subdomain or f"customer-{customer_id}"

        # Crear tunnel en Cloudflare
        cf_result = await CloudflareManager.create_tunnel(name=name)
        if not cf_result.get("success"):
            return {"success": False, "error": f"Error creando tunnel: {cf_result.get('error')}"}

        new_tunnel_id = cf_result["tunnel"]["id"]
        logger.info(f"🆕 Tunnel creado: {name} ({new_tunnel_id})")

        # Vincular al cliente
        result = await link_tunnel_to_customer(
            customer_id=customer_id,
            tunnel_id=new_tunnel_id,
        )

        if result.get("success"):
            # Obtener token para instalar cloudflared
            token_result = await CloudflareManager.get_tunnel_token(new_tunnel_id)
            result["install_token"] = token_result.get("token") if token_result.get("success") else None

        return result
    except Exception as e:
        logger.exception(f"Error provisionando tunnel: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()
