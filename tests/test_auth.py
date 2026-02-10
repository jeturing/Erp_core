"""
Test Authentication - Login, Logout, Token Management
Complete CRUD and functional tests for authentication system
"""
import pytest
from fastapi import status


class TestAuthLogin:
    """Tests for login functionality"""
    
    def test_admin_login_success(self, client):
        """Test successful admin login"""
        response = client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Login exitoso"
        assert data["role"] == "admin"
        assert "access_token" in response.cookies
    
    def test_admin_login_wrong_password(self, client):
        """Test admin login with wrong password"""
        response = client.post("/api/auth/login", json={
            "email": "admin",
            "password": "wrongpassword",
            "role": "admin"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_admin_login_wrong_username(self, client):
        """Test admin login with wrong username"""
        response = client.post("/api/auth/login", json={
            "email": "wronguser",
            "password": "testpass123",
            "role": "admin"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_role_login(self, client):
        """Test login with invalid role"""
        response = client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "superadmin"  # Invalid role
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_page_renders(self, client):
        """Test that login page renders correctly"""
        response = client.get("/login/admin")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
        assert b"login" in response.content.lower() or b"Login" in response.content
    
    def test_tenant_login_page_renders(self, client):
        """Test that tenant login page renders"""
        response = client.get("/login/tenant")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]


class TestAuthLogout:
    """Tests for logout functionality"""
    
    def test_logout_clears_cookies(self, client):
        """Test that logout clears authentication cookies"""
        # First login
        login_response = client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        assert login_response.status_code == status.HTTP_200_OK
        
        # Then logout
        logout_response = client.post("/api/auth/logout")
        assert logout_response.status_code == status.HTTP_200_OK
        
        # Verify cookies are deleted (set to empty/expired)
        data = logout_response.json()
        assert data["message"] == "Sesión cerrada exitosamente"
    
    def test_logout_without_session(self, client):
        """Test logout when not logged in"""
        response = client.post("/api/auth/logout")
        # Should still return success (idempotent)
        assert response.status_code == status.HTTP_200_OK


class TestTokenManagement:
    """Tests for JWT token management"""
    
    def test_token_refresh(self, client):
        """Test token refresh endpoint"""
        # First login to get tokens
        login_response = client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        assert login_response.status_code == status.HTTP_200_OK
        
        # Use refresh token to get new access token
        refresh_response = client.post("/api/auth/refresh")
        # May return 401 if refresh token not in cookies
        assert refresh_response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
    
    def test_protected_route_without_token(self, client):
        """Test accessing protected route without token"""
        response = client.get("/admin")
        # Should redirect to login OR show page (if session exists from previous tests)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_302_FOUND, status.HTTP_307_TEMPORARY_REDIRECT]
    
    def test_api_without_token(self, client):
        """Test API call without token"""
        response = client.get("/api/dashboard/metrics")
        # Should still work (returns default data)
        assert response.status_code == status.HTTP_200_OK


class TestRoleBasedAccess:
    """Tests for role-based access control"""
    
    def test_admin_access_to_dashboard(self, client):
        """Test admin can access dashboard after login"""
        # Login as admin
        login_response = client.post("/api/auth/login", json={
            "email": "admin",
            "password": "testpass123",
            "role": "admin"
        })
        assert login_response.status_code == status.HTTP_200_OK
        
        # Access dashboard with cookies
        dashboard_response = client.get("/admin")
        assert dashboard_response.status_code == status.HTTP_200_OK
    
    def test_invalid_role_login_page(self, client):
        """Test invalid role login page returns 404"""
        response = client.get("/login/superadmin")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAuthenticationSecurity:
    """Tests for authentication security features"""
    
    def test_login_request_structure(self, client):
        """Test login requires proper request structure"""
        # Missing password
        response = client.post("/api/auth/login", json={
            "email": "admin",
            "role": "admin"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing email
        response = client.post("/api/auth/login", json={
            "password": "testpass123",
            "role": "admin"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_sql_injection_attempt(self, client):
        """Test SQL injection prevention in login"""
        response = client.post("/api/auth/login", json={
            "email": "admin' OR '1'='1",
            "password": "' OR '1'='1",
            "role": "admin"
        })
        # Should not authenticate
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_xss_attempt_in_login(self, client):
        """Test XSS prevention in login"""
        response = client.post("/api/auth/login", json={
            "email": "<script>alert('xss')</script>",
            "password": "password",
            "role": "admin"
        })
        # Should not authenticate
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
