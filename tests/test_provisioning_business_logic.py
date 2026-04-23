from app.models.database import Customer, Subscription, SubscriptionStatus
from app.routes.provisioning import _update_local_subscription_suspension_state


def test_subscription_suspension_preserves_and_restores_previous_status(db_session):
    customer = Customer(
        email="pastdue@example.com",
        full_name="Past Due",
        company_name="Past Due Co",
        subdomain="pastdueco",
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    subscription = Subscription(
        customer_id=customer.id,
        plan_name="pro",
        status=SubscriptionStatus.past_due,
        tenant_provisioned=True,
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)

    _update_local_subscription_suspension_state("pastdueco", suspend=True)
    db_session.refresh(subscription)
    assert subscription.status == SubscriptionStatus.suspended
    assert subscription.suspension_previous_status == "past_due"

    _update_local_subscription_suspension_state("pastdueco", suspend=False)
    db_session.refresh(subscription)
    assert subscription.status == SubscriptionStatus.past_due
    assert subscription.suspension_previous_status is None
