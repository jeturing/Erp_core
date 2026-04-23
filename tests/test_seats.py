from fastapi import status

from app.models.database import (
    BillingMode,
    Customer,
    SeatHighWater,
    Subscription,
    SubscriptionStatus,
)


def _create_direct_subscription(db_session):
    customer = Customer(
        email="seats@example.com",
        full_name="Seats Admin",
        company_name="Seats Co",
        subdomain="seatsco",
        user_count=1,
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    subscription = Subscription(
        customer_id=customer.id,
        plan_name="pro",
        status=SubscriptionStatus.active,
        tenant_provisioned=True,
        user_count=1,
        billing_mode=BillingMode.JETURING_DIRECT_SUBSCRIPTION,
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    return customer, subscription


def test_seat_event_requires_api_key(client, db_session):
    _, subscription = _create_direct_subscription(db_session)

    response = client.post("/api/seats/event", json={
        "subscription_id": subscription.id,
        "event_type": "user_created",
        "user_count_after": 2,
        "source": "odoo",
    })

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_seat_event_with_api_key_updates_hwm_and_counts(client, db_session):
    customer, subscription = _create_direct_subscription(db_session)

    response = client.post(
        "/api/seats/event",
        headers={"X-API-KEY": "prov-key-2026-secure"},
        json={
            "subscription_id": subscription.id,
            "event_type": "user_created",
            "odoo_user_id": 42,
            "odoo_login": "user@seats.example",
            "user_count_after": 4,
            "source": "odoo",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_count_after"] == 4
    assert data["hwm_today"] == 4
    assert data["stripe_synced"] is False

    db_session.refresh(customer)
    db_session.refresh(subscription)
    hwm = db_session.query(SeatHighWater).filter(
        SeatHighWater.subscription_id == subscription.id,
    ).one()
    assert customer.user_count == 4
    assert subscription.user_count == 4
    assert hwm.hwm_count == 4


def test_seats_aggregate_reads_require_admin(client, db_session):
    _, subscription = _create_direct_subscription(db_session)

    hwm_response = client.get(f"/api/seats/hwm/{subscription.id}")
    summary_response = client.get(f"/api/seats/summary/{subscription.id}")
    overview_response = client.get("/api/seats/overview")

    assert hwm_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert summary_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert overview_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_sync_stripe_requires_api_key(client):
    response = client.post("/api/seats/sync-stripe")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
