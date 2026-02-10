"""
Pytest Configuration and Fixtures
Provides common test fixtures for all test modules
"""
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.database import Base, Customer, Subscription, SubscriptionStatus, ProxmoxNode, LXCContainer


# Test database - SQLite in memory for speed
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["FORCE_HTTPS"] = "false"
    os.environ["ENABLE_WAF"] = "false"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["ADMIN_USERNAME"] = "admin"
    os.environ["ADMIN_PASSWORD"] = "testpass123"
    yield


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token(client):
    """Get admin JWT token for authenticated requests"""
    response = client.post("/api/auth/login", json={
        "email": "admin",
        "password": "testpass123",
        "role": "admin"
    })
    if response.status_code == 200:
        # Token is in cookie
        return response.cookies.get("access_token")
    return None


@pytest.fixture
def auth_headers(admin_token):
    """Get authorization headers with admin token"""
    if admin_token:
        return {"Authorization": f"Bearer {admin_token}"}
    return {}


@pytest.fixture
def sample_customer(db_session):
    """Create a sample customer for testing"""
    customer = Customer(
        email="test@example.com",
        full_name="Test User",
        company_name="Test Company",
        subdomain="testcompany",
        stripe_customer_id="cus_test123"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def sample_subscription(db_session, sample_customer):
    """Create a sample subscription for testing"""
    subscription = Subscription(
        customer_id=sample_customer.id,
        stripe_subscription_id="sub_test123",
        stripe_checkout_session_id="cs_test123",
        plan_name="pro",
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    return subscription


@pytest.fixture
def sample_node(db_session):
    """Create a sample Proxmox node for testing"""
    from app.models.database import NodeStatus
    node = ProxmoxNode(
        name="test-node-1",
        hostname="192.168.1.100",
        api_port=8006,
        total_cpu_cores=32,
        total_ram_gb=128,
        total_storage_gb=1000,
        status=NodeStatus.online,
        region="us-east"
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    return node


# Helper functions for tests
def create_test_customer(db_session, email: str, subdomain: str) -> Customer:
    """Helper to create test customers"""
    customer = Customer(
        email=email,
        full_name=f"Test {subdomain}",
        company_name=f"{subdomain.title()} Company",
        subdomain=subdomain
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


def create_test_subscription(db_session, customer_id: int, plan: str = "pro") -> Subscription:
    """Helper to create test subscriptions"""
    subscription = Subscription(
        customer_id=customer_id,
        plan_name=plan,
        status=SubscriptionStatus.active
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    return subscription
