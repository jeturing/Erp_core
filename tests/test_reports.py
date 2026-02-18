"""
Test Reports - /api/reports/overview endpoint
"""
import pytest
from fastapi import status


class TestReportsOverview:
    """Tests for consolidated reports overview endpoint"""

    def test_reports_overview_requires_auth(self, client):
        """Test overview endpoint requires admin authentication"""
        response = client.get("/api/reports/overview")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_reports_overview_with_auth(self, client):
        """Test overview endpoint accessible with admin auth"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })

        response = client.get("/api/reports/overview")
        assert response.status_code == status.HTTP_200_OK

    def test_reports_overview_structure(self, client):
        """Test overview response has all required top-level sections"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })

        response = client.get("/api/reports/overview")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        required_sections = [
            "revenue", "customers", "partners", "leads",
            "commissions", "infrastructure", "settlements",
            "work_orders", "reconciliation", "invoices",
            "system_health", "recent_activity", "recent_stripe_events",
        ]
        for section in required_sections:
            assert section in data, f"Missing section: {section}"

    def test_reports_overview_revenue_structure(self, client):
        """Test revenue section has correct fields"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })

        response = client.get("/api/reports/overview")
        data = response.json()
        revenue = data["revenue"]

        assert "mrr" in revenue
        assert "arr" in revenue
        assert "churn_rate" in revenue
        assert "plan_distribution" in revenue
        assert "pending_amount" in revenue
        assert "total_users" in revenue
        assert "new_this_month" in revenue
        assert "cancelled_30d" in revenue

        assert isinstance(revenue["mrr"], (int, float))
        assert isinstance(revenue["arr"], (int, float))
        assert isinstance(revenue["churn_rate"], (int, float))
        assert isinstance(revenue["plan_distribution"], dict)

    def test_reports_overview_customers_structure(self, client):
        """Test customers section has correct fields"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })

        response = client.get("/api/reports/overview")
        data = response.json()
        customers = data["customers"]

        assert isinstance(customers["total"], int)
        assert isinstance(customers["active"], int)
        assert isinstance(customers["suspended"], int)
        assert isinstance(customers["active_subscriptions"], int)

    def test_reports_overview_infrastructure_structure(self, client):
        """Test infrastructure section has correct fields"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })

        response = client.get("/api/reports/overview")
        data = response.json()
        infra = data["infrastructure"]

        assert "nodes_total" in infra
        assert "nodes_online" in infra
        assert "containers_total" in infra
        assert "containers_running" in infra
        assert "cpu" in infra
        assert "ram" in infra
        assert "disk" in infra

        # CPU/RAM/Disk should have percent field
        for key in ["cpu", "ram", "disk"]:
            assert "percent" in infra[key], f"Missing percent in {key}"
            assert isinstance(infra[key]["percent"], (int, float))

    def test_reports_overview_system_health(self, client):
        """Test system_health is a list of status items"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })

        response = client.get("/api/reports/overview")
        data = response.json()

        assert isinstance(data["system_health"], list)
        assert len(data["system_health"]) >= 1

        for item in data["system_health"]:
            assert "name" in item
            assert "status" in item
            assert "detail" in item
            assert item["status"] in ["ok", "warning", "error"]

    def test_reports_overview_recent_activity(self, client):
        """Test recent_activity is a list"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })

        response = client.get("/api/reports/overview")
        data = response.json()

        assert isinstance(data["recent_activity"], list)

    def test_reports_overview_work_orders(self, client):
        """Test work_orders section"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })

        response = client.get("/api/reports/overview")
        data = response.json()
        wo = data["work_orders"]

        assert isinstance(wo["total"], int)
        assert isinstance(wo["requested"], int)
        assert isinstance(wo["in_progress"], int)
        assert isinstance(wo["completed"], int)

    def test_reports_overview_values_non_negative(self, client):
        """Test that numeric values are non-negative"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })

        response = client.get("/api/reports/overview")
        data = response.json()

        assert data["revenue"]["mrr"] >= 0
        assert data["revenue"]["arr"] >= 0
        assert data["customers"]["total"] >= 0
        assert data["invoices"]["total"] >= 0
        assert data["work_orders"]["total"] >= 0
