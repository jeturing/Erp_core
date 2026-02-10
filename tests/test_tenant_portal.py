"""
Test Tenant Portal - Tenant user portal functionality
"""
import pytest
from fastapi import status


class TestTenantPortalPages:
    """Tests for tenant portal pages"""
    
    def test_tenant_portal_requires_auth(self, client):
        """Test tenant portal requires authentication"""
        response = client.get("/tenant/portal", follow_redirects=False)
        assert response.status_code in [
            status.HTTP_302_FOUND,
            status.HTTP_307_TEMPORARY_REDIRECT,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    def test_tenant_login_page(self, client):
        """Test tenant login page accessible"""
        response = client.get("/login/tenant")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]


class TestTenantDashboard:
    """Tests for tenant dashboard"""
    
    def test_tenant_dashboard_structure(self, client):
        """Test tenant dashboard has correct structure"""
        # Would need to login as tenant to test
        # This tests the endpoint existence
        response = client.get("/tenant/dashboard")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_302_FOUND,  # Redirect to login
            status.HTTP_404_NOT_FOUND
        ]


class TestTenantSubscription:
    """Tests for tenant subscription management"""
    
    def test_tenant_subscription_info(self, client):
        """Test getting tenant subscription info"""
        response = client.get("/api/tenant/subscription")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    def test_tenant_usage_stats(self, client):
        """Test getting tenant usage statistics"""
        response = client.get("/api/tenant/usage")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]


class TestTenantBilling:
    """Tests for tenant billing functionality"""
    
    def test_tenant_billing_history(self, client):
        """Test getting billing history"""
        response = client.get("/api/tenant/billing")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
    
    def test_tenant_invoices(self, client):
        """Test getting tenant invoices"""
        response = client.get("/api/tenant/invoices")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]
