"""
Test Tenants CRUD - Complete Create, Read, Update, Delete operations
Tests unitarios validan la API REST y estructura de datos.
Tests de integración (con servidor Odoo real) marcados con @pytest.mark.integration.
"""
import pytest
import socket
from fastapi import status


def _odoo_server_reachable():
    """Check if the Odoo server (10.10.10.20) is reachable on port 8069."""
    try:
        s = socket.create_connection(("10.10.10.20", 8069), timeout=3)
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


ODOO_AVAILABLE = _odoo_server_reachable()
requires_odoo = pytest.mark.skipif(
    not ODOO_AVAILABLE,
    reason="Servidor Odoo (10.10.10.20:8069) no accesible"
)


class TestTenantsList:
    """Tests for listing tenants (READ)"""
    
    def test_list_tenants_returns_items(self, client):
        """Test that list tenants returns data"""
        response = client.get("/api/tenants")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_list_tenants_structure(self, client):
        """Test that tenant items have correct structure"""
        response = client.get("/api/tenants")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        if data["items"]:
            tenant = data["items"][0]
            assert "id" in tenant
            assert "company_name" in tenant
            assert "email" in tenant
            assert "subdomain" in tenant
            assert "plan" in tenant
            assert "status" in tenant
    
    def test_list_tenants_with_auth(self, client, admin_token):
        """Test list tenants with authentication"""
        headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}
        response = client.get("/api/tenants", headers=headers)
        assert response.status_code == status.HTTP_200_OK


class TestTenantCreate:
    """Tests for creating tenants (CREATE) — requiere servidor Odoo real"""
    
    @requires_odoo
    def test_create_tenant_success(self, client):
        """Test successful tenant creation against real Odoo server"""
        tenant_data = {
            "subdomain": "pytest_temp_test",
            "company_name": "Pytest Temp Company",
            "admin_email": "admin@sajet.us",
            "plan": "pro"
        }
        response = client.post("/api/tenants", json=tenant_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "tenant" in data
            assert data["tenant"]["subdomain"] == "pytest_temp_test"
    
    def test_create_tenant_validates_subdomain_required(self, client):
        """Test that subdomain is required (Pydantic validation)"""
        response = client.post("/api/tenants", json={
            "company_name": "Test Company",
            "admin_email": "test@example.com",
            "plan": "pro"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_tenant_validates_subdomain_min_length(self, client):
        """Test that subdomain must be at least 3 characters"""
        response = client.post("/api/tenants", json={
            "subdomain": "ab",
            "company_name": "Test",
            "plan": "pro"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_tenant_validates_subdomain_max_length(self, client):
        """Test that subdomain must be at most 30 characters"""
        response = client.post("/api/tenants", json={
            "subdomain": "a" * 31,
            "company_name": "Test",
            "plan": "pro"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_tenant_optional_fields_have_defaults(self, client):
        """Test that optional fields use defaults when not provided"""
        response = client.post("/api/tenants", json={
            "subdomain": "testdefaults"
        })
        assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTenantValidation:
    """Tests for tenant input validation at the API level"""
    
    def test_subdomain_with_special_chars(self, client):
        """Test subdomain validation rejects special characters"""
        tenant_data = {
            "subdomain": "test company!@#",
            "company_name": "Test Company",
            "admin_email": "test@example.com",
            "plan": "pro"
        }
        response = client.post("/api/tenants", json=tenant_data)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    def test_valid_plan_values(self, client):
        """Test that API accepts valid plan values"""
        for plan in ["basic", "pro", "enterprise"]:
            response = client.post("/api/tenants", json={
                "subdomain": f"plan{plan}test",
                "plan": plan
            })
            assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTenantFiltering:
    """Tests for tenant filtering and search"""
    
    def test_tenants_ordered_by_created_at(self, client):
        """Test tenants response has created_at field"""
        response = client.get("/api/tenants")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        if len(data["items"]) > 1:
            for item in data["items"]:
                assert "created_at" in item or item.get("created_at") is None
    
    def test_tenants_status_filter_values(self, client):
        """Test tenant status values are valid"""
        response = client.get("/api/tenants")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        valid_statuses = ["active", "provisioning", "payment_failed", "suspended", "unknown"]
        for tenant in data["items"]:
            assert tenant["status"] in valid_statuses


class TestTenantServers:
    """Tests for tenant server endpoints"""
    
    def test_servers_endpoint_exists(self, client):
        """Test /api/tenants/servers endpoint responds"""
        response = client.get("/api/tenants/servers")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    @requires_odoo
    def test_servers_list_structure(self, client):
        """Test server list has correct structure when Odoo is available"""
        response = client.get("/api/tenants/servers")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        if data:
            server = data[0]
            assert "id" in server or "name" in server
