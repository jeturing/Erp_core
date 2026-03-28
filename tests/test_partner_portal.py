"""
Partner portal onboarding tests.
"""
from fastapi import status

from app.models.database import Partner, PartnerStatus
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
