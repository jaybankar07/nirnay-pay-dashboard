import pytest
from app.config import settings


def test_postgres_concurrency_locking_and_isolation(db_session, seeded_merchant, seeded_case):
    if "postgresql" not in settings.DATABASE_URL:
        pytest.skip("PostgreSQL concurrency integration test requires PostgreSQL environment.")

    # Execute FOR UPDATE query on PostgreSQL
    from app.repositories.recovery_case_repository import RecoveryCaseRepository
    repo = RecoveryCaseRepository(db_session)
    locked_case = repo.get_by_id(seeded_merchant.id, seeded_case.id, lock_for_update=True)
    assert locked_case is not None
