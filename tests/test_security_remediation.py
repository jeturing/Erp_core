import pytest
from fastapi import HTTPException


def test_empty_jwt_secret_fails(monkeypatch):
    from app.routes import auth

    monkeypatch.setattr(auth, "get_runtime_setting", lambda key, default="": "")

    with pytest.raises(RuntimeError):
        auth.create_access_token("admin")


def test_deprecated_auth_router_not_mounted(client):
    response = client.post("/api/admin/login", json={"username": "admin", "password": "x"})
    assert response.status_code == 404


def test_provision_request_generates_strong_password():
    from app.routes.provisioning import TenantProvisionRequest

    req = TenantProvisionRequest(subdomain="tenantdemo")
    assert req.admin_password != "admin"
    assert len(req.admin_password) >= 12


def test_unsupported_server_error_is_sanitized(monkeypatch):
    from app.routes import provisioning

    monkeypatch.setattr(provisioning, "_cached_odoo_servers", lambda: ({"primary": {"ip": "10.0.0.10"}}, {}))

    with pytest.raises(HTTPException) as exc:
        provisioning._resolve_server_config("pct-201")

    assert exc.value.status_code == 400
    assert "10.0.0.10" not in exc.value.detail
    assert "primary" not in exc.value.detail


def test_spa_path_accepts_nested_routes():
    from app.main import _is_spa_path

    assert _is_spa_path("/dashboard/customer/123")
    assert _is_spa_path("/billing/invoice/456")
    assert not _is_spa_path("/api/customers/123")


def test_odoo_engine_helper_is_cached(monkeypatch):
    from app.routes import provisioning

    provisioning._odoo_engine_for_db.cache_clear()
    monkeypatch.setattr(provisioning, "_odoo_db_host", lambda: "localhost")
    monkeypatch.setattr(provisioning, "_odoo_db_user", lambda: "odoo")
    monkeypatch.setattr(provisioning, "_odoo_db_password", lambda: "")

    first = provisioning._odoo_engine_for_db("tenantdemo")
    second = provisioning._odoo_engine_for_db("tenantdemo")

    assert first is second
    assert first.pool.size() == 2


def test_list_customers_bulk_response_shape(client, db_session):
    from app.models.database import Customer, Plan, Subscription, SubscriptionStatus

    plan = Plan(
        name="pro",
        display_name="Pro",
        base_price=50,
        price_per_user=10,
        included_users=1,
        is_active=True,
    )
    customer = Customer(
        email="bulk@example.com",
        full_name="Bulk Customer",
        company_name="Bulk Co",
        subdomain="bulkco",
        user_count=3,
    )
    db_session.add_all([plan, customer])
    db_session.commit()
    db_session.refresh(customer)
    db_session.add(
        Subscription(
            customer_id=customer.id,
            plan_name="pro",
            status=SubscriptionStatus.active,
            user_count=3,
            monthly_amount=70,
        )
    )
    db_session.commit()

    login = client.post("/api/auth/login", json={"email": "admin", "password": "SecurePass2026!"})
    assert login.status_code == 200

    response = client.get("/api/customers")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["subscription"]["plan_name"] == "pro"
    assert body["items"][0]["plan"]["display_name"] == "Pro"
