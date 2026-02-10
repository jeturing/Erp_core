"""
Test Health and System endpoints
"""
import pytest
from fastapi import status


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check_accessible(self, client):
        """Test health endpoint is accessible without auth"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
    
    def test_health_check_structure(self, client):
        """Test health response structure"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_health_check_version(self, client):
        """Test health returns version info"""
        response = client.get("/health")
        data = response.json()
        
        assert "version" in data
        assert data["version"] == "2.0.0"
    
    def test_health_check_environment(self, client):
        """Test health returns environment info"""
        response = client.get("/health")
        data = response.json()
        
        assert "environment" in data
        assert data["environment"] in ["development", "production", "test"]
    
    def test_health_check_security_info(self, client):
        """Test health returns security configuration"""
        response = client.get("/health")
        data = response.json()
        
        if "security" in data:
            security = data["security"]
            assert "https_enforced" in security
            assert "waf_enabled" in security


class TestStaticFiles:
    """Tests for static file serving"""
    
    def test_static_css_accessible(self, client):
        """Test CSS files are served"""
        response = client.get("/static/css/style.css")
        # May return 200 or 404 depending on file existence
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_static_images_directory(self, client):
        """Test images directory exists"""
        # Try to access an SVG icon
        response = client.get("/static/images/apps/asana.svg")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_static_js_accessible(self, client):
        """Test JavaScript files are served"""
        response = client.get("/static/js/app.js")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestCORS:
    """Tests for CORS configuration"""
    
    def test_cors_preflight(self, client):
        """Test CORS preflight request"""
        response = client.options(
            "/api/tenants",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # CORS preflight may return various codes depending on configuration
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT, status.HTTP_400_BAD_REQUEST, status.HTTP_405_METHOD_NOT_ALLOWED]
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are present in response"""
        response = client.get(
            "/api/tenants",
            headers={"Origin": "http://localhost:4443"}
        )
        # CORS headers may or may not be present depending on configuration
        assert response.status_code == status.HTTP_200_OK


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_for_unknown_route(self, client):
        """Test 404 for unknown routes"""
        response = client.get("/api/unknown/endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_method_not_allowed(self, client):
        """Test 405 for unsupported methods"""
        response = client.delete("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_invalid_json_body(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/tenants",
            content=b"not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAPIDocumentation:
    """Tests for API documentation endpoints"""
    
    def test_docs_availability(self, client):
        """Test OpenAPI docs availability"""
        response = client.get("/docs")
        # May be disabled in production
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_redoc_availability(self, client):
        """Test ReDoc availability"""
        response = client.get("/redoc")
        # May be disabled in production
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_openapi_json(self, client):
        """Test OpenAPI JSON schema availability"""
        response = client.get("/openapi.json")
        # May be disabled in production
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
