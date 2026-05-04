"""
Partner portal onboarding tests.
"""
from fastapi import status

from app.models.database import (
    Customer,
    Invoice,
    Lead,
    LeadStatus,
    ModulePackage,
    Partner,
    PartnerDeployment,
    PartnerPricingOverride,
    PartnerStatus,
    Plan,
    Subscription,
    SupportLevel,
)
from app.routes.roles import create_access_token


def _partner_auth_headers(partner_id: int) -> dict:
    token = create_access_token(f"partner-{partner_id}", "partner", user_id=partner_id)
    return {"Authorization": f"Bearer {token}"}


class TestPartnerStripeOnboarding:
    def test_start_stripe_requires_signed_contract(self, client, db_session):
        partner = Partner(
            company_name="Unsigned Partner",
            contact_email="unsigned@example.com",
            portal_email="unsigned@example.com",
            status=PartnerStatus.active,
            onboarding_step=3,
            country="US",
            portal_access=True,
        )
        db_session.add(partner)
        db_session.commit()
        db_session.refresh(partner)

        response = client.post(
            "/api/partner-portal/onboarding/start-stripe",
            headers=_partner_auth_headers(partner.id),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "firmar" in response.json()["detail"].lower()

    def test_skip_stripe_requires_bypass(self, client, db_session):
        partner = Partner(
            company_name="No Bypass Partner",
            contact_email="nobypass@example.com",
            portal_email="nobypass@example.com",
            status=PartnerStatus.active,
            onboarding_step=3,
            country="US",
            portal_access=True,
        )
        db_session.add(partner)
        db_session.commit()
        db_session.refresh(partner)

        response = client.post(
            "/api/partner-portal/onboarding/skip-stripe",
            headers=_partner_auth_headers(partner.id),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "obligatorio" in response.json()["detail"].lower()


class TestPartnerPrivateData:
    def test_partner_lead_is_registered_under_authenticated_partner(self, client, db_session):
        partner = Partner(
            company_name="Lead Owner Partner",
            contact_email="lead-owner@example.com",
            portal_email="lead-owner@example.com",
            status=PartnerStatus.active,
            onboarding_step=4,
            country="US",
            portal_access=True,
        )
        db_session.add(partner)
        db_session.commit()
        db_session.refresh(partner)

        response = client.post(
            "/api/partner-portal/leads",
            headers=_partner_auth_headers(partner.id),
            json={
                "company_name": "Lead Co",
                "contact_name": "Lead Contact",
                "contact_email": "lead@example.com",
                "estimated_monthly_value": 250,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        lead = db_session.query(Lead).filter(Lead.contact_email == "lead@example.com").first()
        assert lead is not None
        assert lead.partner_id == partner.id

    def test_partner_portal_pricing_uses_private_override(self, client, db_session):
        partner = Partner(
            company_name="Pricing Partner",
            contact_email="pricing-partner@example.com",
            portal_email="pricing-partner@example.com",
            status=PartnerStatus.active,
            onboarding_step=4,
            country="US",
            portal_access=True,
        )
        plan = Plan(
            name="pricing_private",
            display_name="Pricing Private",
            base_price=200,
            price_per_user=50,
            included_users=1,
            is_active=True,
        )
        db_session.add_all([partner, plan])
        db_session.commit()
        db_session.refresh(partner)

        override = PartnerPricingOverride(
            partner_id=partner.id,
            plan_name="pricing_private",
            base_price_override=120,
            price_per_user_override=17.5,
            included_users_override=1,
            support_level=SupportLevel.priority,
            is_active=True,
        )
        db_session.add(override)
        db_session.commit()

        response = client.get(
            "/api/partner-portal/pricing",
            headers=_partner_auth_headers(partner.id),
        )

        assert response.status_code == status.HTTP_200_OK
        item = next(i for i in response.json()["items"] if i["plan_name"] == "pricing_private")
        assert item["base_price"] == 120
        assert item["price_per_user"] == 17.5
        assert item["has_custom_pricing"] is True


class TestPartnerAutomatedDeployments:
    def _seed_partner_plan_package(self, db_session):
        partner = Partner(
            company_name="Auto Deploy Partner",
            contact_email="auto-partner@example.com",
            portal_email="auto-partner@example.com",
            status=PartnerStatus.active,
            onboarding_step=4,
            country="US",
            portal_access=True,
        )
        plan = Plan(
            name="basic",
            display_name="Basic",
            base_price=160,
            price_per_user=25,
            included_users=1,
            is_active=True,
        )
        package = ModulePackage(
            name="retail_click_go",
            display_name="Retail Click-and-Go",
            description="Retail POS + inventory",
            module_list=["point_of_sale", "stock", "account"],
            is_active=True,
        )
        db_session.add_all([partner, plan, package])
        db_session.commit()
        db_session.refresh(partner)
        return partner, plan, package

    def test_partner_can_start_automated_deployment_from_lead(self, client, db_session, monkeypatch):
        from app.routes import partner_portal

        partner, _plan, package = self._seed_partner_plan_package(db_session)
        lead = Lead(
            partner_id=partner.id,
            company_name="Retail Target",
            contact_name="Buyer",
            contact_email="buyer@example.com",
            status=LeadStatus.won,
        )
        db_session.add(lead)
        db_session.commit()
        db_session.refresh(lead)

        def fake_push_invoice_to_stripe(db, invoice):
            invoice.stripe_invoice_id = "in_test_123"
            return {"stripe_invoice_id": "in_test_123", "hosted_invoice_url": "https://pay.test"}

        async def fake_provision(db, deployment, partner_record):
            deployment.status = "invoiced"
            deployment.provisioning_status = "ready"
            deployment.current_phase = "validation"
            deployment.current_week = 3
            deployment.progress_percent = 68
            deployment.tenant_url = f"https://{deployment.subdomain}.sajet.us"
            deployment.admin_login = f"{deployment.subdomain}@sajet.us"
            deployment.admin_password = "secret"
            partner_portal._mark_checklist(deployment, ["tenant", "blueprint"])
            partner_portal._ensure_deployment_invoice(db, deployment, partner_record)
            db.commit()
            return {"success": True, "result": {"fake": True}}

        monkeypatch.setattr(partner_portal, "push_invoice_to_stripe", fake_push_invoice_to_stripe)
        monkeypatch.setattr(partner_portal, "_run_partner_deployment_provision", fake_provision)

        response = client.post(
            "/api/partner-portal/deployments/auto-start",
            headers=_partner_auth_headers(partner.id),
            json={
                "lead_id": lead.id,
                "company_name": "Retail Target",
                "contact_name": "Buyer",
                "contact_email": "buyer@example.com",
                "subdomain": "retailtarget",
                "plan_name": "basic",
                "user_count": 3,
                "country_code": "US",
                "blueprint_package_name": package.name,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["deployment"]["provisioning_status"] == "ready"
        assert body["deployment"]["invoice"] is not None
        assert body["deployment"]["package_snapshot"]["module_count"] == 3
        assert db_session.query(Customer).filter_by(subdomain="retailtarget").first() is not None
        assert db_session.query(Subscription).count() == 1
        assert db_session.query(Invoice).count() == 1

    def test_invalid_blueprint_blocks_before_customer_creation(self, client, db_session):
        partner, _plan, _package = self._seed_partner_plan_package(db_session)

        response = client.post(
            "/api/partner-portal/deployments/auto-start",
            headers=_partner_auth_headers(partner.id),
            json={
                "company_name": "Bad Blueprint Co",
                "contact_email": "bad@example.com",
                "subdomain": "badblueprint",
                "plan_name": "basic",
                "blueprint_package_name": "missing_package",
            },
        )

        assert response.status_code == 400
        assert db_session.query(Customer).filter_by(subdomain="badblueprint").first() is None
        assert db_session.query(PartnerDeployment).count() == 0

    def test_partner_cannot_view_other_partner_deployment(self, client, db_session):
        partner, _plan, _package = self._seed_partner_plan_package(db_session)
        other = Partner(
            company_name="Other Partner",
            contact_email="other-partner@example.com",
            portal_email="other-partner@example.com",
            status=PartnerStatus.active,
            onboarding_step=4,
            country="US",
            portal_access=True,
        )
        dep = PartnerDeployment(
            partner_id=partner.id,
            company_name="Private Client",
            contact_email="private@example.com",
            subdomain="privateclient",
            plan_name="basic",
        )
        db_session.add_all([other, dep])
        db_session.commit()
        db_session.refresh(other)
        db_session.refresh(dep)

        response = client.get(
            f"/api/partner-portal/deployments/{dep.id}",
            headers=_partner_auth_headers(other.id),
        )

        assert response.status_code == 404

    def test_failed_provisioning_leaves_recoverable_deployment(self, client, db_session, monkeypatch):
        from app.routes import partner_portal

        partner, _plan, _package = self._seed_partner_plan_package(db_session)

        async def fake_failed_provision(db, deployment, partner_record):
            deployment.status = "provisioning_failed"
            deployment.provisioning_status = "failed"
            deployment.last_error = "capacity unavailable"
            partner_portal._append_deployment_event(deployment, "provisioning_failed", {"error": deployment.last_error})
            db.commit()
            return {"success": False, "error": deployment.last_error}

        monkeypatch.setattr(partner_portal, "_run_partner_deployment_provision", fake_failed_provision)

        response = client.post(
            "/api/partner-portal/deployments/auto-start",
            headers=_partner_auth_headers(partner.id),
            json={
                "company_name": "Blocked Client",
                "contact_email": "blocked@example.com",
                "subdomain": "blockedclient",
                "plan_name": "basic",
            },
        )

        assert response.status_code == 200
        deployment = response.json()["deployment"]
        assert deployment["status"] == "provisioning_failed"
        assert deployment["last_error"] == "capacity unavailable"
        assert db_session.query(PartnerDeployment).filter_by(subdomain="blockedclient").first() is not None
