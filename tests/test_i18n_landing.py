"""
E2E Tests for Landing Page i18n System
Tests public endpoints, admin CRUD, testimonials, landing sections, and translations.
"""
import os
os.environ["ENABLE_WAF"] = "false"  # Disable WAF for tests (before app import)

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD
from app.models.database import (
    Base, Testimonial, LandingSection, Translation,
)

# Re-use the engine/session from conftest
from tests.conftest import engine, TestingSessionLocal


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_tables():
    """Ensure tables exist before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up i18n tables after each test
    db = TestingSessionLocal()
    try:
        db.query(Testimonial).delete()
        db.query(LandingSection).delete()
        db.query(Translation).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_client():
    """Create a test client that is already authenticated as admin.
    Uses a single login for the entire module to avoid rate limiting."""
    with TestClient(app) as c:
        resp = c.post("/api/auth/login", json={
            "email": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD,
            "role": "admin",
        })
        # The TestClient stores cookies automatically from Set-Cookie headers
        yield c


@pytest.fixture
def seed_testimonials():
    """Seed sample testimonials."""
    db = TestingSessionLocal()
    items = [
        Testimonial(name="Alice", role="CEO", company="AcmeCo", text="Great!", locale="en", featured=True, sort_order=1),
        Testimonial(name="Bob", role="CTO", company="BobTech", text="Amazing!", locale="en", featured=False, sort_order=2),
        Testimonial(name="Carlos", role="CFO", company="AcmeCo", text="Excelente!", locale="es", featured=True, sort_order=1),
    ]
    db.add_all(items)
    db.commit()
    ids = [i.id for i in items]
    db.close()
    return ids


@pytest.fixture
def seed_sections():
    """Seed sample landing sections."""
    db = TestingSessionLocal()
    items = [
        LandingSection(section_key="hero", locale="en", title="Modern ERP", meta_description="Best ERP"),
        LandingSection(section_key="hero", locale="es", title="ERP Moderno", meta_description="Mejor ERP"),
        LandingSection(section_key="features", locale="en", title="Features", meta_description="All features"),
    ]
    db.add_all(items)
    db.commit()
    ids = [i.id for i in items]
    db.close()
    return ids


@pytest.fixture
def seed_translations():
    """Seed sample translations."""
    db = TestingSessionLocal()
    items = [
        Translation(key="landing.hero.badge", locale="en", value="Now in Spanish", context="landing", is_approved=True),
        Translation(key="landing.hero.badge", locale="es", value="Ahora en espanol", context="landing", is_approved=True),
        Translation(key="footer.copyright", locale="en", value="All rights reserved", context="footer", is_approved=False),
    ]
    db.add_all(items)
    db.commit()
    ids = [i.id for i in items]
    db.close()
    return ids


# ══════════════════════════════════════════════════════════════
# PUBLIC ENDPOINTS — No auth required
# ══════════════════════════════════════════════════════════════

class TestPublicTestimonials:
    def test_list_all(self, admin_client, seed_testimonials):
        resp = admin_client.get("/api/public/testimonials")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2  # At least en testimonials
        assert "testimonials" in data

    def test_filter_by_locale(self, admin_client, seed_testimonials):
        resp = admin_client.get("/api/public/testimonials?locale=es")
        assert resp.status_code == 200
        data = resp.json()
        assert data["locale"] == "es"
        for item in data["testimonials"]:
            assert item["locale"] == "es"

    def test_filter_by_locale_en(self, admin_client, seed_testimonials):
        resp = admin_client.get("/api/public/testimonials?locale=en")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        for item in data["testimonials"]:
            assert item["locale"] == "en"


class TestPublicLandingSections:
    def test_list_all(self, admin_client, seed_sections):
        resp = admin_client.get("/api/public/content")
        assert resp.status_code == 200
        data = resp.json()
        assert "sections" in data

    def test_filter_locale_en(self, admin_client, seed_sections):
        resp = admin_client.get("/api/public/content?locale=en")
        assert resp.status_code == 200
        data = resp.json()
        assert data["locale"] == "en"
        # sections is a dict keyed by section_key
        for key, section in data["sections"].items():
            assert section["locale"] == "en"

    def test_filter_locale_es(self, admin_client, seed_sections):
        resp = admin_client.get("/api/public/content?locale=es")
        assert resp.status_code == 200
        data = resp.json()
        assert data["locale"] == "es"


class TestPublicTranslations:
    def test_list_all(self, admin_client, seed_translations):
        resp = admin_client.get("/api/public/translations")
        assert resp.status_code == 200
        data = resp.json()
        assert "translations" in data

    def test_filter_locale(self, admin_client, seed_translations):
        resp = admin_client.get("/api/public/translations?locale=en")
        assert resp.status_code == 200
        data = resp.json()
        assert data["locale"] == "en"
        # translations is a dict key->value
        assert isinstance(data["translations"], dict)

    def test_filter_context(self, admin_client, seed_translations):
        resp = admin_client.get("/api/public/translations?context=landing")
        assert resp.status_code == 200
        data = resp.json()
        assert data["context"] == "landing"


# ══════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS — Require authentication
# ══════════════════════════════════════════════════════════════

class TestAdminTestimonials:
    def test_list_requires_auth(self, client):
        resp = client.get("/api/admin/testimonials")
        assert resp.status_code == 401

    def test_create(self, admin_client):
        resp = admin_client.post("/api/admin/testimonials", json={
            "name": "Test User",
            "role": "Manager",
            "company": "TestCo",
            "text": "This is a test testimonial.",
            "locale": "en",
            "featured": False,
            "sort_order": 10,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test User"
        assert data["locale"] == "en"
        assert data["id"] > 0

    def test_list(self, admin_client, seed_testimonials):
        resp = admin_client.get("/api/admin/testimonials")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 3

    def test_list_filter_locale(self, admin_client, seed_testimonials):
        resp = admin_client.get("/api/admin/testimonials?locale=es")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["locale"] == "es"

    def test_list_filter_featured(self, admin_client, seed_testimonials):
        resp = admin_client.get("/api/admin/testimonials?featured=true")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["featured"] is True

    def test_get_by_id(self, admin_client, seed_testimonials):
        tid = seed_testimonials[0]
        resp = admin_client.get(f"/api/admin/testimonials/{tid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == tid

    def test_get_not_found(self, admin_client):
        resp = admin_client.get("/api/admin/testimonials/99999")
        assert resp.status_code == 404

    def test_update(self, admin_client, seed_testimonials):
        tid = seed_testimonials[0]
        resp = admin_client.put(f"/api/admin/testimonials/{tid}", json={
            "name": "Alice Updated",
            "text": "Updated text",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Alice Updated"

    def test_delete(self, admin_client, seed_testimonials):
        tid = seed_testimonials[1]
        resp = admin_client.delete(f"/api/admin/testimonials/{tid}")
        assert resp.status_code == 204

        # Confirm it's gone
        resp = admin_client.get(f"/api/admin/testimonials/{tid}")
        assert resp.status_code == 404


class TestAdminLandingSections:
    def test_create(self, admin_client):
        resp = admin_client.post("/api/admin/landing-sections", json={
            "section_key": "pricing",
            "locale": "en",
            "title": "Pricing Plans",
            "content": "<p>Choose your plan</p>",
            "meta_description": "Affordable ERP pricing",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["section_key"] == "pricing"

    def test_list(self, admin_client, seed_sections):
        resp = admin_client.get("/api/admin/landing-sections")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

    def test_filter_locale(self, admin_client, seed_sections):
        resp = admin_client.get("/api/admin/landing-sections?locale=es")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["locale"] == "es"

    def test_filter_section_key(self, admin_client, seed_sections):
        resp = admin_client.get("/api/admin/landing-sections?section_key=hero")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["section_key"] == "hero"

    def test_get_by_id(self, admin_client, seed_sections):
        sid = seed_sections[0]
        resp = admin_client.get(f"/api/admin/landing-sections/{sid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == sid

    def test_update(self, admin_client, seed_sections):
        sid = seed_sections[0]
        resp = admin_client.put(f"/api/admin/landing-sections/{sid}", json={
            "title": "Updated Hero Title",
            "meta_description": "Updated meta",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Hero Title"

    def test_delete(self, admin_client, seed_sections):
        sid = seed_sections[2]
        resp = admin_client.delete(f"/api/admin/landing-sections/{sid}")
        assert resp.status_code == 204


class TestAdminTranslations:
    def test_create(self, admin_client):
        resp = admin_client.post("/api/admin/translations", json={
            "key": "test.key.new",
            "locale": "en",
            "value": "Test Value",
            "context": "landing",
            "is_approved": False,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["key"] == "test.key.new"
        assert data["is_approved"] is False

    def test_create_duplicate_conflict(self, admin_client, seed_translations):
        resp = admin_client.post("/api/admin/translations", json={
            "key": "landing.hero.badge",
            "locale": "en",
            "value": "Duplicate",
            "context": "landing",
        })
        assert resp.status_code == 409

    def test_list(self, admin_client, seed_translations):
        resp = admin_client.get("/api/admin/translations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

    def test_filter_locale(self, admin_client, seed_translations):
        resp = admin_client.get("/api/admin/translations?locale=en")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["locale"] == "en"

    def test_filter_context(self, admin_client, seed_translations):
        resp = admin_client.get("/api/admin/translations?context=footer")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["context"] == "footer"

    def test_filter_approved_only(self, admin_client, seed_translations):
        resp = admin_client.get("/api/admin/translations?approved_only=true")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["is_approved"] is True

    def test_get_by_id(self, admin_client, seed_translations):
        tid = seed_translations[0]
        resp = admin_client.get(f"/api/admin/translations/{tid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == tid

    def test_update(self, admin_client, seed_translations):
        tid = seed_translations[0]
        resp = admin_client.put(f"/api/admin/translations/{tid}", json={
            "value": "Updated Translation Value",
        })
        assert resp.status_code == 200
        assert resp.json()["value"] == "Updated Translation Value"

    def test_patch(self, admin_client, seed_translations):
        tid = seed_translations[2]
        resp = admin_client.patch(f"/api/admin/translations/{tid}", json={
            "is_approved": True,
        })
        assert resp.status_code == 200
        assert resp.json()["is_approved"] is True

    def test_delete(self, admin_client, seed_translations):
        tid = seed_translations[1]
        resp = admin_client.delete(f"/api/admin/translations/{tid}")
        assert resp.status_code == 204

        # Confirm it's gone
        resp = admin_client.get(f"/api/admin/translations/{tid}")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════
# CROSS-CUTTING CONCERNS
# ══════════════════════════════════════════════════════════════

class TestI18nPagination:
    def test_testimonials_pagination(self, admin_client, seed_testimonials):
        resp = admin_client.get("/api/admin/testimonials?limit=1&offset=0")
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["total"] >= 3

    def test_translations_pagination(self, admin_client, seed_translations):
        resp = admin_client.get("/api/admin/translations?limit=2&offset=0")
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["total"] >= 3


class TestI18nAuth:
    """Ensure all admin endpoints reject unauthenticated requests."""

    ADMIN_ENDPOINTS = [
        ("GET",    "/api/admin/testimonials"),
        ("POST",   "/api/admin/testimonials"),
        ("GET",    "/api/admin/landing-sections"),
        ("POST",   "/api/admin/landing-sections"),
        ("GET",    "/api/admin/translations"),
        ("POST",   "/api/admin/translations"),
    ]

    @pytest.mark.parametrize("method,url", ADMIN_ENDPOINTS)
    def test_requires_auth(self, client, method, url):
        if method == "GET":
            resp = client.get(url)
        else:
            resp = client.post(url, json={})
        assert resp.status_code in (401, 403, 422), f"{method} {url} should require auth, got {resp.status_code}"
