"""
Partner portal onboarding tests.
"""
from fastapi import status

from app.models.database import Lead, Partner, PartnerPricingOverride, PartnerStatus, Plan, SupportLevel
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
