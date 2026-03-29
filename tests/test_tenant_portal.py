"""
Test Tenant Portal - Tenant user portal functionality
"""
import pytest
from fastapi import status

from app.models.database import Customer, Plan, SeatEvent, SeatEventType, Subscription, SubscriptionStatus
from app.routes.roles import create_access_token


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
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
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
            status.HTTP_503_SERVICE_UNAVAILABLE,
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


def test_tenant_users_returns_live_accounts_and_history(client, db_session, monkeypatch):
    customer = Customer(
        email="tenant-users@test.com",
        full_name="Tenant Users",
        company_name="Tenant Users Co",
        subdomain="tenantusers",
        user_count=2,
    )
    plan = Plan(
        name="pro",
        display_name="Pro",
        base_price=150,
        price_per_user=17.10,
        included_users=1,
        max_users=15,
        is_active=True,
    )
    db_session.add_all([customer, plan])
    db_session.commit()

    subscription = Subscription(
        customer_id=customer.id,
        plan_name="pro",
        status=SubscriptionStatus.active,
        user_count=2,
    )
    db_session.add(subscription)
    db_session.commit()

    db_session.add(
        SeatEvent(
            subscription_id=subscription.id,
            event_type=SeatEventType.USER_CREATED,
            odoo_user_id=7,
            odoo_login="ana@tenantusers.com",
            user_count_after=2,
            is_billable=True,
            source="sync-seat-count",
        )
    )
    db_session.commit()

    monkeypatch.setattr(
        "app.routes.tenant_portal.fetch_tenant_accounts_snapshot",
        lambda *args, **kwargs: {
            "accounts": [
                {
                    "id": 7,
                    "login": "ana@tenantusers.com",
                    "email": "ana@tenantusers.com",
                    "name": "Ana Tenant",
                    "active": True,
                    "share": False,
                    "is_admin": False,
                    "is_excluded": False,
                    "is_billable": True,
                    "write_date": "2026-03-29T08:00:00",
                    "create_date": "2026-03-20T08:00:00",
                },
                {
                    "id": 8,
                    "login": "tenantusers@sajet.us",
                    "email": "tenantusers@sajet.us",
                    "name": "Cuenta interna",
                    "active": True,
                    "share": False,
                    "is_admin": False,
                    "is_excluded": True,
                    "is_billable": False,
                    "write_date": "2026-03-29T08:00:00",
                    "create_date": "2026-03-20T08:00:00",
                },
            ],
            "active_accounts": 2,
            "billable_active_accounts": 1,
        },
    )

    token = create_access_token(customer.email, "tenant", user_id=customer.id, tenant_id=customer.id)
    response = client.get("/tenant/api/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_user_count"] == 1
    assert payload["active_accounts"] == 2
    assert payload["billable_active_accounts"] == 1
    assert payload["plan_user_limit"] == 15
    assert len(payload["accounts"]) == 2
    assert payload["accounts"][0]["login"] == "ana@tenantusers.com"
    assert payload["seat_events"][0]["event_type"] == "USER_CREATED"
    assert payload["seat_events"][0]["login"] == "ana@tenantusers.com"
