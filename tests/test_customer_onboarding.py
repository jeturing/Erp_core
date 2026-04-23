from fastapi import status

from app.models.database import Customer, Subscription, SubscriptionStatus
from app.security.tokens import TokenManager


def _tenant_headers(customer: Customer) -> dict:
    token = TokenManager.create_access_token(
        username=customer.email,
        role="tenant",
        user_id=customer.id,
        tenant_id=customer.id,
    )
    return {"Authorization": f"Bearer {token}"}


def test_admin_role_cannot_complete_customer_onboarding(client, db_session):
    client.cookies.clear()
    customer = Customer(
        email="admin-collision@example.com",
        full_name="Admin Collision",
        company_name="Admin Collision Co",
        subdomain="admincollision",
        country="US",
        requires_ecf=False,
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    token = TokenManager.create_access_token(
        username="admin",
        role="admin",
        user_id=customer.id,
        tenant_id=customer.id,
    )

    response = client.post(
        "/api/customer-onboarding/complete",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_complete_onboarding_requires_active_provisioned_subscription(client, db_session):
    client.cookies.clear()
    customer = Customer(
        email="tenant-complete@example.com",
        full_name="Tenant Complete",
        company_name="Tenant Complete Co",
        subdomain="tenantcomplete",
        country="US",
        requires_ecf=False,
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    headers = _tenant_headers(customer)

    missing = client.post("/api/customer-onboarding/complete", headers=headers)
    assert missing.status_code == status.HTTP_409_CONFLICT

    subscription = Subscription(
        customer_id=customer.id,
        plan_name="pro",
        status=SubscriptionStatus.active,
        tenant_provisioned=False,
    )
    db_session.add(subscription)
    db_session.commit()

    not_ready = client.post("/api/customer-onboarding/complete", headers=headers)
    assert not_ready.status_code == status.HTTP_409_CONFLICT

    subscription.tenant_provisioned = True
    db_session.commit()

    completed = client.post("/api/customer-onboarding/complete", headers=headers)
    assert completed.status_code == status.HTTP_200_OK
    db_session.refresh(customer)
    assert customer.onboarding_step == 4
    assert customer.onboarding_completed_at is not None


def test_complete_onboarding_requires_ecf_when_dominican_customer(client, db_session):
    client.cookies.clear()
    customer = Customer(
        email="tenant-ecf@example.com",
        full_name="Tenant ECF",
        company_name="Tenant ECF Co",
        subdomain="tenantecf",
        country="DO",
        requires_ecf=True,
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    db_session.add(Subscription(
        customer_id=customer.id,
        plan_name="pro",
        status=SubscriptionStatus.active,
        tenant_provisioned=True,
    ))
    db_session.commit()

    response = client.post("/api/customer-onboarding/complete", headers=_tenant_headers(customer))

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "e-CF" in response.json()["detail"]
