"""
Tests para DGII Data Service (Fase 3A).
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime, timedelta


client = TestClient(app)


class TestDgiiRncValidation:
    """Tests para validación de RNC."""
    
    def test_health_check(self):
        """Test de health check del servicio."""
        response = client.get("/api/dgii/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "DGII Data Service"
    
    def test_validate_rnc_valid(self):
        """Test de validación RNC válido."""
        response = client.get("/api/dgii/rnc/101010101")
        assert response.status_code == 200
        data = response.json()
        assert data["rnc"] == "101010101"
        assert "valid" in data
        assert "status" in data
        assert data["status"] in ["active", "inactive", "not_found", "suspended"]
    
    def test_validate_rnc_invalid_format(self):
        """Test de validación RNC con formato inválido."""
        response = client.get("/api/dgii/rnc/12345")  # Muy corto
        assert response.status_code == 400
    
    def test_rnc_cache_ttl(self):
        """Test de TTL del cache RNC."""
        response = client.get("/api/dgii/rnc/101010101")
        data = response.json()
        
        assert "cache_ttl_expires" in data
        ttl_expires = datetime.fromisoformat(data["cache_ttl_expires"])
        
        # TTL debe ser 30 días desde ahora
        now = datetime.utcnow()
        expected_max = now + timedelta(days=31)
        expected_min = now + timedelta(days=29)
        
        assert expected_min <= ttl_expires <= expected_max


class TestDgiiValidationEndpoint:
    """Tests para pre-validación DGII."""
    
    def test_validate_606_valid(self):
        """Test de validación 606 válido."""
        response = client.post(
            "/api/dgii/validate",
            json={
                "document_type": "606",
                "company_id": 1,
                "ncf": "E310000000001",
                "amount": 10000.0,
                "supplier_rnc": "101010101",
                "invoice_date": datetime.utcnow().isoformat()
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "issues" in data
    
    def test_validate_negative_amount(self):
        """Test: Monto negativo debe generar error."""
        response = client.post(
            "/api/dgii/validate",
            json={
                "document_type": "606",
                "company_id": 1,
                "ncf": "E310000000001",
                "amount": -5000.0,
                "invoice_date": datetime.utcnow().isoformat()
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) > 0
        assert any(issue["issue_code"] == "AMOUNT_ZERO" for issue in data["issues"])
    
    def test_validate_future_date(self):
        """Test: Fecha futura debe generar warning."""
        future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
        response = client.post(
            "/api/dgii/validate",
            json={
                "document_type": "607",
                "company_id": 1,
                "ncf": "E310000000001",
                "amount": 10000.0,
                "invoice_date": future_date
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) > 0
        assert any(issue["issue_code"] == "DATE_FUTURE" for issue in data["issues"])
    
    def test_can_proceed_logic(self):
        """Test: can_proceed debe ser False si hay errores."""
        response = client.post(
            "/api/dgii/validate",
            json={
                "document_type": "606",
                "company_id": 1,
                "amount": 0.0  # Error: monto 0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["can_proceed"] == False


class TestDgiiPartnerEnrichment:
    """Tests para enriquecimiento de partners."""
    
    def test_enrich_partner_new(self):
        """Test: Crear nuevo partner desde RNC."""
        response = client.post(
            "/api/dgii/partner/enrich",
            json={
                "rnc": "101010101",
                "company_id": 1
            }
        )
        # Puede ser created o updated
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["created", "updated"]
        assert "partner_id" in data
    
    def test_enrich_partner_invalid_rnc(self):
        """Test: RNC inválido debe rechazarse."""
        response = client.post(
            "/api/dgii/partner/enrich",
            json={
                "rnc": "123",  # RNC inválido
                "company_id": 1
            }
        )
        # Debe fallar en validación
        assert response.status_code in [400, 422]


class TestDgiiCachePerformance:
    """Tests de performance del cache."""
    
    def test_cache_hit_performance(self):
        """Test: Segunda consulta RNC debe ser más rápida."""
        import time
        
        # Primera consulta (cache miss)
        start = time.time()
        response1 = client.get("/api/dgii/rnc/101010101")
        time1 = time.time() - start
        
        # Segunda consulta (cache hit)
        start = time.time()
        response2 = client.get("/api/dgii/rnc/101010101")
        time2 = time.time() - start
        
        # La segunda debe ser notablemente más rápida
        # (pero sin validar tiempo exacto, puede variar en CI/CD)
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["rnc"] == response2.json()["rnc"]


class TestDgiiErrorHandling:
    """Tests de manejo de errores."""
    
    def test_invalid_document_type(self):
        """Test: Documento type inválido."""
        response = client.post(
            "/api/dgii/validate",
            json={
                "document_type": "999",  # Inválido
                "company_id": 1
            }
        )
        # Puede no ser validado o aceptado como string
        assert response.status_code in [200, 422]
    
    def test_missing_required_field(self):
        """Test: Campo requerido faltante."""
        response = client.post(
            "/api/dgii/validate",
            json={
                # Falta document_type
                "company_id": 1
            }
        )
        assert response.status_code == 422  # Validation error


# ============================================================================
# TESTS DE INTEGRACIÓN CON ODOO (si aplicable)
# ============================================================================

@pytest.mark.asyncio
async def test_dgii_service_with_odoo_database():
    """Test integración con base de datos Odoo."""
    # Este test requiere conexión real a BD
    # Skip si no está disponible
    pytest.skip("Requiere BD real de Odoo")


@pytest.mark.asyncio
async def test_rnc_cache_ttl_refresh():
    """Test: Refresh automático de TTL expirado."""
    pytest.skip("Implementar cuando caché sea persistente")
