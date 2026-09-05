import pytest
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.models import Merchant, Customer, RecoveryCase, RevenueEvent
from app.utils.enums import CustomerSegment, RevenueEventType, RecoveryCaseStatus


def test_merchant_repository(db_session):
    repo = MerchantRepository(db_session)
    merchant = Merchant(name="Repository Test Merchant", email="repo@test.com")
    created = repo.create(merchant)
    assert created.id is not None

    fetched = repo.get_by_id(created.id)
    assert fetched.name == "Repository Test Merchant"


def test_customer_repository_merchant_isolation(db_session, seeded_merchant):
    repo = CustomerRepository(db_session)
    customer = Customer(
        merchant_id=seeded_merchant.id,
        external_customer_id="EXT_101",
        name="Iso Customer",
        customer_segment=CustomerSegment.LOYAL
    )
    repo.create(customer)

    # Fetching with wrong merchant ID must return None
    wrong = repo.get_by_id("wrong_merchant_id", customer.id)
    assert wrong is None

    # Fetching with correct merchant ID returns customer
    correct = repo.get_by_id(seeded_merchant.id, customer.id)
    assert correct is not None
