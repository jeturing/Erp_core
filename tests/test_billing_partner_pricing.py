from datetime import datetime

from app.models.database import (
    BillingMode,
    Customer,
    Invoice,
    Partner,
    PartnerStatus,
    PartnerPricingOverride,
    Plan,
    Subscription,
    SubscriptionStatus,
)
from app.services.stripe_billing import generate_consumption_invoice


def test_generate_consumption_invoice_uses_partner_override_and_is_idempotent(db_session, monkeypatch):
    partner = Partner(
        company_name="Techeels Partner",
        contact_email="partner@test.com",
        status=PartnerStatus.active,
        partner_code="TECHPARTNER",
    )
    plan = Plan(
        name="pro",
        display_name="Pro",
        base_price=150,
        price_per_user=17.10,
        included_users=1,
        is_active=True,
    )
    override = PartnerPricingOverride(
        partner=partner,
        plan_name="pro",
        base_price_override=150,
        price_per_user_override=17.10,
        included_users_override=1,
        is_active=True,
    )
    customer = Customer(
        email="admin@techeels.com",
        full_name="TecHeels",
        company_name="TecHeels",
        subdomain="techeels",
        user_count=4,
    )
    db_session.add_all([partner, plan, override, customer])
    db_session.commit()
    customer.partner_id = partner.id
    db_session.commit()

    subscription = Subscription(
        customer_id=customer.id,
        plan_name="pro",
        status=SubscriptionStatus.active,
        user_count=4,
        billing_mode=BillingMode.PARTNER_DIRECT,
        owner_partner_id=partner.id,
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)

    monkeypatch.setattr(
        "app.services.stripe_billing.push_invoice_to_stripe",
        lambda db, invoice: {"stripe_invoice_id": "in_test_123", "status": "draft"},
    )

    period_start = datetime(2026, 3, 1)
    period_end = datetime(2026, 4, 1)

    first = generate_consumption_invoice(
        db_session,
        subscription.id,
        period_start=period_start,
        period_end=period_end,
    )
    second = generate_consumption_invoice(
        db_session,
        subscription.id,
        period_start=period_start,
        period_end=period_end,
    )

    invoice = db_session.query(Invoice).filter(Invoice.id == first["invoice_id"]).first()

    assert round(first["total"], 2) == 201.30
    assert first["pricing_source"] == "partner_override"
    assert invoice is not None
    assert invoice.billing_period_key == "2026-03-01__2026-04-01"
    assert second["invoice_id"] == first["invoice_id"]
    assert second["pricing_source"] == "existing_invoice"
