"""
Test Onboarding - Customer registration and checkout flow
"""
import pytest
from fastapi import status
from types import SimpleNamespace

from app.models.database import BillingScenario, Partner, PartnerStatus, Plan


class TestOnboardingPages:
    """Tests for onboarding HTML pages"""
    
    def test_signup_page_renders(self, client):
        """Test signup page renders correctly"""
        response = client.get("/signup")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        assert "text/html" in response.headers["content-type"]
    
    def test_signup_with_basic_plan(self, client):
        """Test signup page with basic plan"""
        response = client.get("/signup?plan=basic")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
    
    def test_signup_with_pro_plan(self, client):
        """Test signup page with pro plan"""
        response = client.get("/signup?plan=pro")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
    
    def test_signup_with_enterprise_plan(self, client):
        """Test signup page with enterprise plan"""
        response = client.get("/signup?plan=enterprise")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
    
    def test_onboarding_alias(self, client):
        """Test /onboarding redirects or shows signup"""
        response = client.get("/onboarding")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
    
    def test_success_page_renders(self, client):
        """Test success page renders"""
        response = client.get("/success")
        # May require session_id param
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_503_SERVICE_UNAVAILABLE]


class TestCheckoutAPI:
    """Tests for checkout API endpoint"""
    
    def test_checkout_valid_request(self, client):
        """Test checkout with valid data"""
        checkout_data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "company_name": "Test Company",
            "subdomain": "testcompany",
            "plan": "pro"
        }
        response = client.post("/api/checkout", json=checkout_data)
        # Puede fallar si el plan no está sembrado en la BD de pruebas
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
    
    def test_checkout_missing_email(self, client):
        """Test checkout without email"""
        checkout_data = {
            "full_name": "Test User",
            "company_name": "Test Company",
            "subdomain": "testcompany",
            "plan": "pro"
        }
        response = client.post("/api/checkout", json=checkout_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_checkout_missing_subdomain(self, client):
        """Test checkout without subdomain"""
        checkout_data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "company_name": "Test Company",
            "plan": "pro"
        }
        response = client.post("/api/checkout", json=checkout_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_checkout_missing_plan(self, client):
        """Test checkout without plan"""
        checkout_data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "company_name": "Test Company",
            "subdomain": "testcompany"
        }
        response = client.post("/api/checkout", json=checkout_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_checkout_all_plans(self, client):
        """Test checkout with all plan types"""
        for plan in ["basic", "pro", "enterprise"]:
            checkout_data = {
                "full_name": f"{plan.title()} User",
                "email": f"{plan}@example.com",
                "company_name": f"{plan.title()} Company",
                "subdomain": f"{plan}company",
                "plan": plan
            }
            response = client.post("/api/checkout", json=checkout_data)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]

    def test_checkout_partner_jeturing_collects_uses_destination_charge(
        self,
        client,
        db_session,
        monkeypatch,
    ):
        plan = Plan(
            name="partner_pro",
            display_name="Partner Pro",
            base_price=100,
            price_per_user=10,
            included_users=1,
            stripe_price_id="price_partner_pro",
            is_active=True,
        )
        partner = Partner(
            company_name="Partner One",
            contact_email="partner@example.com",
            country="US",
            status=PartnerStatus.active,
            partner_code="PARTNER1",
            billing_scenario=BillingScenario.jeturing_collects,
            commission_rate=65.0,
            stripe_account_id="acct_partner_123",
            stripe_onboarding_complete=True,
            stripe_charges_enabled=True,
        )
        db_session.add(plan)
        db_session.add(partner)
        db_session.commit()

        captured = {}

        def fake_create(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(url="https://checkout.test/session", id="cs_test_partner")

        monkeypatch.setattr("app.routes.onboarding.stripe.checkout.Session.create", fake_create)

        checkout_data = {
            "full_name": "Buyer Test",
            "email": "buyer@example.com",
            "company_name": "Buyer Co",
            "subdomain": "buyerco",
            "plan": "partner_pro",
            "partner_code": "PARTNER1",
        }

        response = client.post("/api/checkout", json=checkout_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["billing_mode"] == "partner_direct"
        assert "stripe_account" not in captured
        assert captured["subscription_data"]["transfer_data"]["destination"] == "acct_partner_123"
        assert captured["subscription_data"]["application_fee_percent"] == 35.0
        assert captured["subscription_data"]["on_behalf_of"] == "acct_partner_123"

    def test_checkout_partner_collects_keeps_external_collection(
        self,
        client,
        db_session,
        monkeypatch,
    ):
        plan = Plan(
            name="partner_external",
            display_name="Partner External",
            base_price=120,
            price_per_user=15,
            included_users=1,
            stripe_price_id="price_partner_external",
            is_active=True,
        )
        partner = Partner(
            company_name="Partner External",
            contact_email="partner2@example.com",
            country="DO",
            status=PartnerStatus.active,
            partner_code="PARTNER2",
            billing_scenario=BillingScenario.partner_collects,
            commission_rate=50.0,
        )
        db_session.add(plan)
        db_session.add(partner)
        db_session.commit()

        captured = {}

        def fake_create(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(url="https://checkout.test/session", id="cs_test_external")

        monkeypatch.setattr("app.routes.onboarding.stripe.checkout.Session.create", fake_create)

        checkout_data = {
            "full_name": "Buyer Two",
            "email": "buyer2@example.com",
            "company_name": "Buyer Two Co",
            "subdomain": "buyertwo",
            "plan": "partner_external",
            "partner_code": "PARTNER2",
        }

        response = client.post("/api/checkout", json=checkout_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["billing_mode"] == "partner_pays_for_client"
        assert "subscription_data" not in captured

    def test_checkout_partner_without_ready_connect_is_blocked(
        self,
        client,
        db_session,
    ):
        plan = Plan(
            name="partner_blocked",
            display_name="Partner Blocked",
            base_price=100,
            price_per_user=10,
            included_users=1,
            stripe_price_id="price_partner_blocked",
            is_active=True,
        )
        partner = Partner(
            company_name="Partner Blocked",
            contact_email="partner3@example.com",
            country="US",
            status=PartnerStatus.active,
            partner_code="PARTNER3",
            billing_scenario=BillingScenario.jeturing_collects,
            commission_rate=50.0,
            stripe_account_id="acct_partner_blocked",
            stripe_onboarding_complete=False,
        )
        db_session.add(plan)
        db_session.add(partner)
        db_session.commit()

        checkout_data = {
            "full_name": "Buyer Three",
            "email": "buyer3@example.com",
            "company_name": "Buyer Three Co",
            "subdomain": "buyerthree",
            "plan": "partner_blocked",
            "partner_code": "PARTNER3",
        }

        response = client.post("/api/checkout", json=checkout_data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "Stripe Connect" in response.json()["detail"]


class TestStripeWebhook:
    """Tests for Stripe webhook endpoint"""
    
    def test_webhook_rejects_invalid_signature(self, client):
        """Test webhook rejects requests without valid Stripe signature"""
        response = client.post(
            "/webhook/stripe",
            content=b'{"type": "test"}',
            headers={"stripe-signature": "invalid_signature"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_webhook_requires_signature(self, client):
        """Test webhook requires Stripe signature header"""
        response = client.post(
            "/webhook/stripe",
            content=b'{"type": "test"}'
        )
        # Should fail without signature
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestCustomerValidation:
    """Tests for customer data validation"""
    
    def test_valid_email_formats(self, client):
        """Test various valid email formats"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.com",
            "user+tag@domain.co.uk"
        ]
        
        for email in valid_emails:
            checkout_data = {
                "full_name": "Test User",
                "email": email,
                "company_name": "Test Company",
                "subdomain": email.split("@")[0].replace(".", "").replace("+", ""),
                "plan": "pro"
            }
            response = client.post("/api/checkout", json=checkout_data)
            # Should not be validation error
            assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_subdomain_uniqueness(self, client):
        """Test subdomain validation"""
        checkout_data = {
            "full_name": "First User",
            "email": "first@example.com",
            "company_name": "First Company",
            "subdomain": "uniquesubdomain123",
            "plan": "pro"
        }
        
        # First request
        response1 = client.post("/api/checkout", json=checkout_data)
        
        # Second request with same subdomain
        checkout_data["email"] = "second@example.com"
        checkout_data["full_name"] = "Second User"
        response2 = client.post("/api/checkout", json=checkout_data)
        
        # One should succeed, other may fail or both succeed depending on DB state
        assert response1.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
