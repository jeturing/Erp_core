"""
Tests for Odoo tenant snapshot webhooks.
"""
import asyncio

from app.models.database import (
    BillingMode,
    Customer,
    CustomDomain,
    DomainVerificationStatus,
    PartnerStatus,
    Plan,
    Partner,
    Subscription,
    SubscriptionStatus,
)
from app.routes.odoo_webhooks import (
    _handle_tenant_config_changed,
    _handle_tenant_snapshot,
    _handle_user_created,
)


class TestOdooTenantSnapshots:
    def test_tenant_snapshot_creates_customer_subscription_and_domains(self, db_session):
        plan = Plan(
            name="basic",
            display_name="Basic",
            is_active=True,
            max_domains=3,
        )
        db_session.add(plan)
        db_session.commit()

        payload = {
            "company_name": "La Taza Curiosa SRL",
            "admin_email": "adm@latazacuriosa.net",
            "user_count": 4,
            "plan_name": "basic",
            "billing_mode": "legacy_imported",
            "base_url": "https://latazacuriosa.com",
            "domains": [
                {"domain": "latazacuriosa.com", "is_primary": True},
                {"domain": "www.latazacuriosa.com"},
            ],
        }

        result = asyncio.run(_handle_tenant_snapshot("latazacuriosa", payload))

        customer = db_session.query(Customer).filter(Customer.subdomain == "latazacuriosa").first()
        subscription = db_session.query(Subscription).filter(Subscription.customer_id == customer.id).first()
        domains = db_session.query(CustomDomain).filter(CustomDomain.customer_id == customer.id).all()

        assert result["synced"] is True
        assert result["customer_created"] is True
        assert result["subscription_created"] is True
        assert customer.company_name == "La Taza Curiosa SRL"
        assert customer.email == "adm@latazacuriosa.net"
        assert customer.user_count == 4
        assert subscription.status == SubscriptionStatus.active
        assert subscription.plan_name == "basic"
        assert subscription.billing_mode == BillingMode.LEGACY_IMPORTED
        assert subscription.user_count == 4
        assert {row.external_domain for row in domains} == {
            "latazacuriosa.com",
            "www.latazacuriosa.com",
        }
        assert any(row.external_domain == "latazacuriosa.com" and row.is_primary for row in domains)
        assert all(row.is_active for row in domains)
        assert all(row.verification_status == DomainVerificationStatus.verified for row in domains)

    def test_tenant_config_changed_ignores_internal_sajet_domains(self, db_session):
        plan = Plan(
            name="basic",
            display_name="Basic",
            is_active=True,
            max_domains=3,
        )
        db_session.add(plan)
        db_session.commit()

        existing_customer = Customer(
            email="old@techeels.com",
            full_name="Techeels",
            company_name="Old Techeels",
            subdomain="techeels",
        )
        db_session.add(existing_customer)
        db_session.commit()

        payload = {
            "company_name": "Techeels Holdings",
            "admin_email": "admin@techeels.com",
            "plan_name": "basic",
            "base_url": "https://techeels.sajet.us",
            "domains": [
                "techeels.sajet.us",
                {"domain": "portal.techeels.com", "is_primary": True},
            ],
        }

        result = asyncio.run(_handle_tenant_config_changed("techeels", payload))

        customer = db_session.query(Customer).filter(Customer.subdomain == "techeels").first()
        subscription = db_session.query(Subscription).filter(Subscription.customer_id == customer.id).first()
        domains = db_session.query(CustomDomain).filter(CustomDomain.customer_id == customer.id).all()

        assert result["synced"] is True
        assert customer.company_name == "Techeels Holdings"
        assert customer.email == "admin@techeels.com"
        assert subscription is not None
        assert len(domains) == 1
        assert domains[0].external_domain == "portal.techeels.com"
        assert domains[0].sajet_subdomain == "techeels"
        assert domains[0].is_primary is True

    def test_user_created_excludes_partner_admin_and_sajet_admin_from_billable_count(self, db_session):
        partner = Partner(
            company_name="Partner",
            contact_email="partner@example.com",
            status=PartnerStatus.active,
            partner_code="P1",
        )
        plan = Plan(
            name="basic",
            display_name="Basic",
            is_active=True,
            base_price=120,
            price_per_user=17.5,
            included_users=1,
        )
        customer = Customer(
            email="manager@partner.com",
            full_name="Manager",
            company_name="TecHeels",
            subdomain="techeels",
            partner_id=None,
            user_count=1,
        )
        db_session.add_all([partner, plan, customer])
        db_session.commit()
        customer.partner_id = partner.id
        db_session.commit()

        subscription = Subscription(
            customer_id=customer.id,
            plan_name="basic",
            status=SubscriptionStatus.active,
            user_count=1,
            owner_partner_id=partner.id,
        )
        db_session.add(subscription)
        db_session.commit()

        partner_admin = asyncio.run(_handle_user_created("techeels", {
            "user_id": 10,
            "login": "manager@partner.com",
            "active": True,
            "share": False,
        }))
        sajet_admin = asyncio.run(_handle_user_created("techeels", {
            "user_id": 11,
            "login": "techeels@sajet.us",
            "active": True,
            "share": False,
        }))

        db_session.refresh(customer)
        db_session.refresh(subscription)

        assert partner_admin["synced"] is False
        assert partner_admin["reason"] == "non_billable_user"
        assert sajet_admin["synced"] is False
        assert sajet_admin["reason"] == "non_billable_user"
        assert customer.user_count == 1
        assert subscription.user_count == 1
