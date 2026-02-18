"""
Tests para el Catálogo de Servicios SAJET y vinculación Plan↔Catálogo
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Configurar para SQLite en tests
os.environ["ENABLE_SQLITE_FALLBACK"] = "true"
os.environ["SQLALCHEMY_DATABASE_URL"] = "sqlite:///./test_catalog.db"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Crea un TestClient con BD SQLite de prueba."""
    from app.models.database import Base, _get_engine, init_db
    from app.main import app

    init_db()

    with TestClient(app) as c:
        yield c

    # Cleanup
    try:
        os.unlink("./test_catalog.db")
    except FileNotFoundError:
        pass


def _admin_headers():
    """Headers con un token JWT de admin simulado."""
    import jwt
    token = jwt.encode(
        {"sub": "admin", "role": "admin", "exp": 9999999999},
        os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-me"),
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════
# CATALOG CRUD
# ═══════════════════════════════════════════

class TestCatalogCRUD:
    """Tests para CRUD del catálogo de servicios."""

    def test_list_catalog_requires_auth(self, client):
        """GET /api/catalog requiere autenticación."""
        resp = client.get("/api/catalog")
        assert resp.status_code == 401

    def test_list_catalog_empty(self, client):
        """Catálogo vacío devuelve estructura correcta."""
        resp = client.get("/api/catalog", headers=_admin_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "by_category" in data
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0  # Al menos las categorías enum

    def test_create_catalog_item(self, client):
        """Crear un item en el catálogo."""
        resp = client.post("/api/catalog", json={
            "category": "saas_platform",
            "name": "Odoo SaaS Basic",
            "description": "Instancia Odoo compartida",
            "unit": "Por mes",
            "price_monthly": 49.99,
            "sort_order": 1,
        }, headers=_admin_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Servicio añadido al catálogo"
        assert data["item"]["name"] == "Odoo SaaS Basic"
        assert data["item"]["price_monthly"] == 49.99
        assert data["item"]["is_active"] is True

    def test_create_second_item(self, client):
        """Crear un segundo item (add-on)."""
        resp = client.post("/api/catalog", json={
            "category": "saas_support",
            "name": "Soporte Premium 24/7",
            "description": "Soporte técnico con SLA 4h",
            "unit": "Por mes",
            "price_monthly": 199.00,
            "is_addon": True,
            "sort_order": 2,
        }, headers=_admin_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["item"]["is_addon"] is True

    def test_list_catalog_with_items(self, client):
        """Catálogo con items devuelve datos agrupados."""
        resp = client.get("/api/catalog", headers=_admin_headers())
        data = resp.json()
        assert data["total"] >= 2
        assert "saas_platform" in data["by_category"]

    def test_update_catalog_item(self, client):
        """Actualizar un item del catálogo."""
        # Primero obtener el ID
        resp = client.get("/api/catalog", headers=_admin_headers())
        items = resp.json()["items"]
        item_id = items[0]["id"]

        resp = client.put(f"/api/catalog/{item_id}", json={
            "category": "saas_platform",
            "name": "Odoo SaaS Basic v2",
            "unit": "Por mes",
            "price_monthly": 59.99,
        }, headers=_admin_headers())
        assert resp.status_code == 200
        assert resp.json()["item"]["price_monthly"] == 59.99

    def test_delete_catalog_item_soft(self, client):
        """Desactivar un item del catálogo (soft delete)."""
        resp = client.get("/api/catalog?include_inactive=true", headers=_admin_headers())
        items = resp.json()["items"]
        item_id = items[-1]["id"]

        resp = client.delete(f"/api/catalog/{item_id}", headers=_admin_headers())
        assert resp.status_code == 200
        assert "desactivado" in resp.json()["message"].lower()

    def test_reactivate_catalog_item(self, client):
        """Reactivar un item desactivado."""
        resp = client.get("/api/catalog?include_inactive=true", headers=_admin_headers())
        items = resp.json()["items"]
        # Find inactive item
        inactive = [i for i in items if not i["is_active"]]
        if inactive:
            resp = client.put(f"/api/catalog/{inactive[0]['id']}/reactivate", headers=_admin_headers())
            assert resp.status_code == 200
            assert "reactivado" in resp.json()["message"].lower()

    def test_filter_by_category(self, client):
        """Filtrar catálogo por categoría."""
        resp = client.get("/api/catalog?category=saas_platform", headers=_admin_headers())
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["category"] == "saas_platform"

    def test_invalid_category_returns_all(self, client):
        """Categoría inválida no filtra (devuelve todo)."""
        resp = client.get("/api/catalog?category=invalid_category", headers=_admin_headers())
        assert resp.status_code == 200


# ═══════════════════════════════════════════
# PLAN ↔ CATALOG LINKING
# ═══════════════════════════════════════════

class TestPlanCatalogLinks:
    """Tests para vinculación plan↔catálogo."""

    @pytest.fixture(autouse=True)
    def _setup_plan(self, client):
        """Asegura que existe al menos un plan."""
        resp = client.get("/api/plans?include_inactive=true", headers=_admin_headers())
        if resp.json()["total"] == 0:
            client.post("/api/plans", json={
                "name": "test_basic",
                "display_name": "Test Basic",
                "base_price": 29.99,
                "price_per_user": 5.0,
                "included_users": 1,
            }, headers=_admin_headers())

    def test_list_plan_links_empty(self, client):
        """Lista de vínculos vacía."""
        resp = client.get("/api/catalog/plan-links", headers=_admin_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert "links" in data
        assert "total" in data

    def test_create_plan_link(self, client):
        """Vincular un item del catálogo a un plan."""
        # Get plan
        plans_resp = client.get("/api/plans?include_inactive=true", headers=_admin_headers())
        plan_id = plans_resp.json()["items"][0]["id"]

        # Get catalog item
        cat_resp = client.get("/api/catalog", headers=_admin_headers())
        cat_item_id = cat_resp.json()["items"][0]["id"]

        resp = client.post("/api/catalog/plan-links", json={
            "plan_id": plan_id,
            "catalog_item_id": cat_item_id,
            "included_quantity": 1,
            "is_included": True,
            "discount_percent": 0,
            "notes": "Incluido en plan básico",
        }, headers=_admin_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert "vinculado" in data["message"].lower()
        assert data["link"]["plan_id"] == plan_id
        assert data["link"]["catalog_item_id"] == cat_item_id

    def test_duplicate_link_rejected(self, client):
        """No se puede vincular el mismo item dos veces al mismo plan."""
        plans_resp = client.get("/api/plans?include_inactive=true", headers=_admin_headers())
        plan_id = plans_resp.json()["items"][0]["id"]

        cat_resp = client.get("/api/catalog", headers=_admin_headers())
        cat_item_id = cat_resp.json()["items"][0]["id"]

        resp = client.post("/api/catalog/plan-links", json={
            "plan_id": plan_id,
            "catalog_item_id": cat_item_id,
        }, headers=_admin_headers())
        assert resp.status_code == 409

    def test_link_with_invalid_plan(self, client):
        """Plan inexistente devuelve 404."""
        cat_resp = client.get("/api/catalog", headers=_admin_headers())
        cat_item_id = cat_resp.json()["items"][0]["id"]

        resp = client.post("/api/catalog/plan-links", json={
            "plan_id": 9999,
            "catalog_item_id": cat_item_id,
        }, headers=_admin_headers())
        assert resp.status_code == 404

    def test_catalog_items_include_linked_plans(self, client):
        """Los items del catálogo incluyen los planes vinculados."""
        resp = client.get("/api/catalog", headers=_admin_headers())
        items = resp.json()["items"]
        linked_items = [i for i in items if i.get("linked_plans") and len(i["linked_plans"]) > 0]
        assert len(linked_items) > 0

    def test_filter_links_by_plan(self, client):
        """Filtrar vínculos por plan_id."""
        plans_resp = client.get("/api/plans?include_inactive=true", headers=_admin_headers())
        plan_id = plans_resp.json()["items"][0]["id"]

        resp = client.get(f"/api/catalog/plan-links?plan_id={plan_id}", headers=_admin_headers())
        assert resp.status_code == 200
        for link in resp.json()["links"]:
            assert link["plan_id"] == plan_id

    def test_delete_plan_link(self, client):
        """Eliminar un vínculo plan↔catálogo."""
        resp = client.get("/api/catalog/plan-links", headers=_admin_headers())
        links = resp.json()["links"]
        if links:
            link_id = links[0]["id"]
            resp = client.delete(f"/api/catalog/plan-links/{link_id}", headers=_admin_headers())
            assert resp.status_code == 200
            assert "eliminado" in resp.json()["message"].lower()
