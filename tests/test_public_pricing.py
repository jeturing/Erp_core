from fastapi import status

from app.models.database import Partner, PartnerPricingOverride, PartnerStatus, Plan, SupportLevel


class TestPublicPricing:
    def test_public_calculate_ignores_partner_discount(self, client, db_session):
        plan = Plan(
            name="public_basic",
            display_name="Public Basic",
            base_price=200,
            price_per_user=50,
            included_users=1,
            is_active=True,
        )
        partner = Partner(
            company_name="Referral Partner",
            contact_email="referral@example.com",
            status=PartnerStatus.active,
            partner_code="REF123",
        )
        db_session.add_all([plan, partner])
        db_session.commit()
        db_session.refresh(partner)

        db_session.add(
            PartnerPricingOverride(
                partner_id=partner.id,
                plan_name="public_basic",
                base_price_override=120,
                price_per_user_override=17.5,
                included_users_override=1,
                support_level=SupportLevel.priority,
                is_active=True,
            )
        )
        db_session.commit()

        response = client.post("/api/public/calculate", json={
            "plan_name": "public_basic",
            "user_count": 2,
            "partner_code": "REF123",
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["monthly"]["total"] == 250
        assert data["monthly"]["base"] == 200
        assert data["monthly"]["users_cost"] == 50
        assert data["base_price"] == 200
        assert data["price_per_user"] == 50
        assert data["has_partner_pricing"] is False

    def test_partner_landing_keeps_public_plan_prices(self, client, db_session):
        plan = Plan(
            name="public_partner_plan",
            display_name="Public Partner Plan",
            base_price=180,
            price_per_user=35,
            included_users=1,
            is_active=True,
            is_public=True,
        )
        partner = Partner(
            company_name="Brand Partner",
            contact_email="brand@example.com",
            status=PartnerStatus.active,
            partner_code="BRAND1",
            slug="brand-partner",
        )
        db_session.add_all([plan, partner])
        db_session.commit()
        db_session.refresh(partner)

        db_session.add(
            PartnerPricingOverride(
                partner_id=partner.id,
                plan_name="public_partner_plan",
                base_price_override=99,
                price_per_user_override=9,
                included_users_override=5,
                support_level=SupportLevel.priority,
                is_active=True,
            )
        )
        db_session.commit()

        response = client.get("/api/public/partner/brand-partner")

        assert response.status_code == status.HTTP_200_OK
        plan_data = next(p for p in response.json()["plans"] if p["name"] == "public_partner_plan")
        assert plan_data["base_price"] == 180
        assert plan_data["price_per_user"] == 35
        assert plan_data["included_users"] == 1
        assert plan_data["has_partner_pricing"] is False
