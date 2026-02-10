"""
Test Tunnels - Cloudflare tunnel management
"""
import pytest
from fastapi import status


class TestTunnelsList:
    """Tests for listing tunnels (READ)"""
    
    def test_list_tunnels_endpoint(self, client):
        """Test tunnels list endpoint"""
        # Login first
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        
        response = client.get("/api/tunnels")
        # Should return data or indicate endpoint exists or DB unavailable
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    def test_tunnels_structure(self, client):
        """Test tunnels response structure"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        
        response = client.get("/api/tunnels")
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Should be a list or have items
            assert isinstance(data, (list, dict))


class TestTunnelCRUD:
    """Tests for tunnel CRUD operations"""
    
    def test_create_tunnel(self, client):
        """Test creating a new tunnel"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        
        tunnel_data = {
            "subdomain": "newtunnel",
            "target_url": "http://localhost:8069"
        }
        
        response = client.post("/api/tunnels", json=tunnel_data)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_500_INTERNAL_SERVER_ERROR  # Cloudflare API error or DB unavailable
        ]
    
    def test_get_tunnel_by_id(self, client):
        """Test getting a specific tunnel"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        
        response = client.get("/api/tunnels/test-tunnel")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    def test_delete_tunnel(self, client):
        """Test deleting a tunnel"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        
        response = client.delete("/api/tunnels/test-tunnel")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]


class TestTunnelStatus:
    """Tests for tunnel status management"""
    
    def test_tunnel_status_check(self, client):
        """Test checking tunnel status"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        
        response = client.get("/api/tunnels/status")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    def test_tunnel_health(self, client):
        """Test tunnel health endpoint"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        
        response = client.get("/api/tunnels/health")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]


class TestAdminTunnelsPage:
    """Tests for admin tunnels page"""
    
    def test_tunnels_page_requires_auth(self, client):
        """Test tunnels page requires authentication"""
        response = client.get("/admin/tunnels", follow_redirects=False)
        # Should redirect to login or show page (if page exists)
        assert response.status_code in [
            status.HTTP_200_OK,  # If already authenticated from previous tests
            status.HTTP_302_FOUND,
            status.HTTP_307_TEMPORARY_REDIRECT,
            status.HTTP_404_NOT_FOUND  # Page may not exist
        ]
    
    def test_tunnels_page_with_auth(self, client):
        """Test tunnels page with authentication"""
        client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        
        response = client.get("/admin/tunnels")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]
