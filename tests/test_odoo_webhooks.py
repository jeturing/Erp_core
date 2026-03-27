"""
Tests for Odoo tenant snapshot webhooks.
"""
import asyncio

from app.models.database import (
    BillingMode,
    Customer,
    CustomDomain,
    DomainVerificationStatus,
    Plan,
    Subscription,
    SubscriptionStatus,
)
from app.routes.odoo_webhooks import _handle_tenant_config_changed, _handle_tenant_snapshot


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
