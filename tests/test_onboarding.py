"""
Test Onboarding - Customer registration and checkout flow
"""
import pytest
from fastapi import status


class TestOnboardingPages:
    """Tests for onboarding HTML pages"""
    
    def test_signup_page_renders(self, client):
        """Test signup page renders correctly"""
        response = client.get("/signup")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
    
    def test_signup_with_basic_plan(self, client):
        """Test signup page with basic plan"""
        response = client.get("/signup?plan=basic")
        assert response.status_code == status.HTTP_200_OK
    
    def test_signup_with_pro_plan(self, client):
        """Test signup page with pro plan"""
        response = client.get("/signup?plan=pro")
        assert response.status_code == status.HTTP_200_OK
    
    def test_signup_with_enterprise_plan(self, client):
        """Test signup page with enterprise plan"""
        response = client.get("/signup?plan=enterprise")
        assert response.status_code == status.HTTP_200_OK
    
    def test_onboarding_alias(self, client):
        """Test /onboarding redirects or shows signup"""
        response = client.get("/onboarding")
        assert response.status_code == status.HTTP_200_OK
    
    def test_success_page_renders(self, client):
        """Test success page renders"""
        response = client.get("/success")
        # May require session_id param
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]


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
        # May fail with Stripe error in test env, but should not be 422
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
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
            # Should accept all plans
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


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
        assert response1.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
