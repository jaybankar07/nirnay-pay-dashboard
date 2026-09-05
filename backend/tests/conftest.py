import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database.session import Base, get_db
from app.models import Merchant, Customer, RevenueEvent, RecoveryCase, RecoveryPolicy
from app.utils.enums import CustomerSegment, RevenueEventType, RecoveryCaseStatus

# Use in-memory SQLite with StaticPool so all threads share the exact same in-memory DB connection
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_merchant(db_session):
    merchant = Merchant(
        id="merchant_test_001",
        name="Test Merchant",
        email="test@merchant.com"
    )
    db_session.add(merchant)
    db_session.commit()
    return merchant


@pytest.fixture
def seeded_case(db_session, seeded_merchant):
    customer = Customer(
        id="cust_test_001",
        merchant_id=seeded_merchant.id,
        external_customer_id="EXT_001",
        name="John Doe",
        customer_segment=CustomerSegment.FIRST_TIME
    )
    event = RevenueEvent(
        id="evt_test_001",
        merchant_id=seeded_merchant.id,
        customer_id=customer.id,
        event_type=RevenueEventType.PAYMENT_FAILURE,
        amount_paise=49900
    )
    case = RecoveryCase(
        id="case_test_001",
        merchant_id=seeded_merchant.id,
        customer_id=customer.id,
        revenue_event_id=event.id,
        status=RecoveryCaseStatus.DETECTED,
        scenario_type=RevenueEventType.PAYMENT_FAILURE,
        amount_at_risk_paise=49900
    )
    db_session.add_all([customer, event, case])
    db_session.commit()
    return case
