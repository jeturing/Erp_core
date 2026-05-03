"""
Servicios adicionales / add-ons comprables desde portal tenant y partner.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import logging

from sqlalchemy.orm import Session

from ..models.database import (
    BillingMode,
    Customer,
    CustomerAddonSubscription,
    Invoice,
    InvoiceIssuer,
    InvoiceStatus,
    InvoiceType,
    Partner,
    Plan,
    PlanCatalogLink,
    ServiceCatalogItem,
    Subscription,
)
from .stripe_connect import normalize_country_code
from .stripe_billing import push_invoice_to_stripe

logger = logging.getLogger(__name__)

COUNTRY_ALIASES = {
    "UNITED STATES": "US",
    "UNITED STATES OF AMERICA": "US",
    "USA": "US",
    "US": "US",
    "ESTADOS UNIDOS": "US",
    "DOMINICAN REPUBLIC": "DO",
    "REPUBLICA DOMINICANA": "DO",
    "REPÚBLICA DOMINICANA": "DO",
    "DO": "DO",
    "RD": "DO",
}
SENSITIVE_METADATA_MARKERS = (
    "token",
    "secret",
    "password",
    "authorization",
    "signature",
)


def _normalize_catalog_country(country: Optional[str]) -> Optional[str]:
    raw = (country or "").strip()
    if not raw:
        return None
    if len(raw) == 2 and raw.isalpha():
        return normalize_country_code(raw, raw.upper())
    return COUNTRY_ALIASES.get(raw.upper(), raw.upper())


def _sanitize_metadata(value: Any, parent_key: str = "") -> Any:
    if isinstance(value, dict):
        return {
            key: _sanitize_metadata(item, key)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_metadata(item, parent_key) for item in value]
    key_name = (parent_key or "").lower()
    if key_name and any(marker in key_name for marker in SENSITIVE_METADATA_MARKERS):
        return "***"
    return value


def _resolve_customer_country(customer: Customer, partner: Optional[Partner]) -> Optional[str]:
    return _normalize_catalog_country(customer.country or (partner.country if partner else None))


def _item_allowed_for_country(item: ServiceCatalogItem, country_code: Optional[str]) -> bool:
    metadata = item.metadata_json or {}
    allowed = [
        code for code in (
            _normalize_catalog_country(entry)
            for entry in metadata.get("allowed_countries", [])
        )
        if code
    ]
    blocked = [
        code for code in (
            _normalize_catalog_country(entry)
            for entry in metadata.get("excluded_countries", [])
        )
        if code
    ]

    if allowed and not country_code:
        return False
    if allowed and country_code not in allowed:
        return False
    if blocked and country_code in blocked:
        return False
    return True


def _next_invoice_number(db: Session) -> str:
    year = datetime.now(timezone.utc).replace(tzinfo=None).year
    last = (
        db.query(Invoice)
        .filter(Invoice.invoice_number.like(f"INV-{year}-%"))
        .order_by(Invoice.id.desc())
        .first()
    )
    seq = 1
    if last and last.invoice_number:
        try:
            seq = int(last.invoice_number.split("-")[-1]) + 1
        except Exception:
            seq = 1
    return f"INV-{year}-{seq:04d}"


def _serialize_catalog_item(item: ServiceCatalogItem) -> Dict[str, Any]:
    return {
        "id": item.id,
        "category": item.category.value if item.category else None,
        "name": item.name,
        "description": item.description,
        "unit": item.unit,
        "price_monthly": item.price_monthly,
        "price_max": item.price_max,
        "is_addon": item.is_addon,
        "requires_service_id": item.requires_service_id,
        "min_quantity": item.min_quantity,
        "service_code": item.service_code,
        "metadata_json": _sanitize_metadata(item.metadata_json or {}),
        "is_active": item.is_active,
        "sort_order": item.sort_order,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _serialize_addon_subscription(addon: CustomerAddonSubscription) -> Dict[str, Any]:
    item = addon.catalog_item
    return {
        "id": addon.id,
        "customer_id": addon.customer_id,
        "subscription_id": addon.subscription_id,
        "partner_id": addon.partner_id,
        "catalog_item_id": addon.catalog_item_id,
        "status": addon.status,
        "quantity": addon.quantity,
        "unit_price_monthly": addon.unit_price_monthly,
        "currency": addon.currency,
        "service_code": addon.service_code,
        "metadata_json": _sanitize_metadata(addon.metadata_json or {}),
        "acquired_via": addon.acquired_via,
        "starts_at": addon.starts_at.isoformat() if addon.starts_at else None,
        "last_invoiced_year": addon.last_invoiced_year,
        "last_invoiced_month": addon.last_invoiced_month,
        "catalog_item": _serialize_catalog_item(item) if item else None,
    }


def _get_customer_context(
    db: Session,
    customer_id: int,
) -> tuple[Customer, Optional[Subscription], Optional[Plan], Optional[Partner]]:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise ValueError("Cliente no encontrado")

    subscription = (
        db.query(Subscription)
        .filter(Subscription.customer_id == customer.id)
        .order_by(Subscription.id.desc())
        .first()
    )
    plan = None
    partner = None
    if subscription and subscription.plan_name:
        plan = db.query(Plan).filter(Plan.name == subscription.plan_name).first()
    partner_id = subscription.owner_partner_id if subscription and subscription.owner_partner_id else customer.partner_id
    if partner_id:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
    return customer, subscription, plan, partner


def _resolve_catalog_offer(
    db: Session,
    customer_id: int,
    item: ServiceCatalogItem,
) -> Dict[str, Any]:
    customer, subscription, plan, _partner = _get_customer_context(db, customer_id)

    discount_percent = 0.0
    included_quantity = 0
    is_included_in_plan = False
    effective_price = float(item.price_monthly or 0)

    plan_link = None
    if plan:
        plan_link = (
            db.query(PlanCatalogLink)
            .filter(
                PlanCatalogLink.plan_id == plan.id,
                PlanCatalogLink.catalog_item_id == item.id,
            )
            .first()
        )
        if plan_link:
            if plan_link.is_included:
                included_quantity = max(0, int(plan_link.included_quantity or 0))
                is_included_in_plan = included_quantity > 0
                effective_price = 0.0 if is_included_in_plan else effective_price
            else:
                discount_percent = float(plan_link.discount_percent or 0)
                effective_price = round(effective_price * ((100.0 - discount_percent) / 100.0), 6)

    return {
        "customer": customer,
        "subscription": subscription,
        "plan": plan,
        "plan_link": plan_link,
        "discount_percent": discount_percent,
        "included_quantity": included_quantity,
        "is_included_in_plan": is_included_in_plan,
        "effective_price_monthly": effective_price,
    }


def list_available_addon_services(db: Session, customer_id: int) -> List[Dict[str, Any]]:
    customer, _subscription, _plan, partner = _get_customer_context(db, customer_id)
    customer_country = _resolve_customer_country(customer, partner)

    items = (
        db.query(ServiceCatalogItem)
        .filter(ServiceCatalogItem.is_addon == True, ServiceCatalogItem.is_active == True)
        .order_by(ServiceCatalogItem.sort_order, ServiceCatalogItem.id)
        .all()
    )

    active_quantities = {
        row.catalog_item_id: row.quantity
        for row in db.query(CustomerAddonSubscription)
        .filter(
            CustomerAddonSubscription.customer_id == customer_id,
            CustomerAddonSubscription.status == "active",
        )
        .all()
    }

    result: List[Dict[str, Any]] = []
    for item in items:
        if not _item_allowed_for_country(item, customer_country):
            continue
        offer = _resolve_catalog_offer(db, customer_id, item)
        data = _serialize_catalog_item(item)
        data.update({
            "effective_price_monthly": offer["effective_price_monthly"],
            "discount_percent": offer["discount_percent"],
            "included_quantity": offer["included_quantity"],
            "is_included_in_plan": offer["is_included_in_plan"],
            "active_quantity": active_quantities.get(item.id, 0),
            "customer_country": customer_country,
        })
        result.append(data)
    return result


def list_customer_addon_subscriptions(db: Session, customer_id: int) -> List[Dict[str, Any]]:
    addons = (
        db.query(CustomerAddonSubscription)
        .filter(
            CustomerAddonSubscription.customer_id == customer_id,
            CustomerAddonSubscription.status == "active",
        )
        .order_by(CustomerAddonSubscription.created_at.desc())
        .all()
    )
    return [_serialize_addon_subscription(addon) for addon in addons]


def purchase_customer_addon(
    db: Session,
    customer_id: int,
    catalog_item_id: int,
    quantity: int = 1,
    acquired_via: str = "tenant_portal",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    if quantity < 1:
        raise ValueError("La cantidad debe ser al menos 1")

    item = (
        db.query(ServiceCatalogItem)
        .filter(
            ServiceCatalogItem.id == catalog_item_id,
            ServiceCatalogItem.is_active == True,
            ServiceCatalogItem.is_addon == True,
        )
        .first()
    )
    if not item:
        raise ValueError("Servicio adicional no encontrado o no disponible")

    offer = _resolve_catalog_offer(db, customer_id, item)
    customer: Customer = offer["customer"]
    subscription: Optional[Subscription] = offer["subscription"]
    partner: Optional[Partner] = _get_customer_context(db, customer_id)[3]
    customer_country = _resolve_customer_country(customer, partner)

    if not _item_allowed_for_country(item, customer_country):
        raise ValueError("Este servicio no está disponible para el país configurado del cliente")

    if offer["is_included_in_plan"] and offer["effective_price_monthly"] == 0:
        raise ValueError("Este servicio ya está incluido en el plan del cliente")

    addon = (
        db.query(CustomerAddonSubscription)
        .filter(
            CustomerAddonSubscription.customer_id == customer.id,
            CustomerAddonSubscription.catalog_item_id == item.id,
            CustomerAddonSubscription.status == "active",
        )
        .first()
    )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if addon:
        addon.quantity += quantity
        addon.unit_price_monthly = offer["effective_price_monthly"]
        addon.currency = subscription.currency if subscription and subscription.currency else "USD"
        addon.service_code = item.service_code
        addon.metadata_json = item.metadata_json or {}
        addon.acquired_via = acquired_via
        if notes:
            addon.notes = notes
    else:
        addon = CustomerAddonSubscription(
            customer_id=customer.id,
            subscription_id=subscription.id if subscription else None,
            partner_id=partner.id if partner else None,
            catalog_item_id=item.id,
            status="active",
            quantity=quantity,
            unit_price_monthly=offer["effective_price_monthly"],
            currency=subscription.currency if subscription and subscription.currency else "USD",
            service_code=item.service_code,
            metadata_json=item.metadata_json or {},
            acquired_via=acquired_via,
            notes=notes,
            starts_at=now,
        )
        db.add(addon)
        db.flush()

    line_subtotal = round(quantity * offer["effective_price_monthly"], 6)
    stripe_result: Dict[str, Any] | None = None
    invoice: Optional[Invoice] = None

    if line_subtotal > 0:
        invoice = Invoice(
            invoice_number=_next_invoice_number(db),
            subscription_id=subscription.id if subscription else None,
            customer_id=customer.id,
            partner_id=partner.id if partner else None,
            invoice_type=InvoiceType.ADDON,
            billing_mode=subscription.billing_mode if subscription and subscription.billing_mode else BillingMode.JETURING_DIRECT_SUBSCRIPTION,
            issuer=InvoiceIssuer.JETURING,
            subtotal=line_subtotal,
            tax_amount=0,
            total=line_subtotal,
            currency=subscription.currency if subscription and subscription.currency else "USD",
            lines_json=[{
                "description": f"{item.name} ({quantity} × ${offer['effective_price_monthly']}/mes)",
                "qty": quantity,
                "unit_price": offer["effective_price_monthly"],
                "subtotal": line_subtotal,
                "catalog_item_id": item.id,
                "service_code": item.service_code,
                "metadata_json": item.metadata_json or {},
            }],
            status=InvoiceStatus.issued,
            issued_at=now,
            due_date=now + timedelta(days=30),
            notes=f"Generada automáticamente por compra de servicio ({acquired_via})",
        )
        db.add(invoice)
        db.flush()

        try:
            stripe_result = push_invoice_to_stripe(db, invoice)
        except Exception as exc:
            stripe_result = {"error": str(exc), "stripe_invoice_id": None}
            logger.warning("No se pudo emitir la factura adicional en Stripe: %s", exc)

        addon.last_invoiced_year = now.year
        addon.last_invoiced_month = now.month

    db.commit()
    db.refresh(addon)

    return {
        "addon": _serialize_addon_subscription(addon),
        "invoice": {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "total": invoice.total,
            "currency": invoice.currency,
            "status": invoice.status.value if invoice.status else None,
            "stripe_invoice_id": invoice.stripe_invoice_id,
            "payment_url": stripe_result.get("hosted_invoice_url") if stripe_result else None,
        } if invoice else None,
        "stripe_result": stripe_result,
    }
