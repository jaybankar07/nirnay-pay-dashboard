import pytest
from app.repositories.audit_repository import AuditRepository
from app.models.audit_event import AuditEvent
from app.utils.enums import AuditEventType, ActorType


def test_audit_repository_surface_immutability(db_session, seeded_case):
    repo = AuditRepository(db_session)

    # 1. Verify repo does not expose update or delete methods
    assert not hasattr(repo, "update")
    assert not hasattr(repo, "delete")
    assert hasattr(repo, "create")
    assert hasattr(repo, "list_by_case_id")

    # 2. Verify creation and retrieval
    event = AuditEvent(
        recovery_case_id=seeded_case.id,
        event_type=AuditEventType.CASE_DETECTED,
        actor_type=ActorType.SYSTEM,
        event_data_json={"test": "data"}
    )
    saved = repo.create(event)
    assert saved.id is not None

    logs = repo.list_by_case_id(seeded_case.id)
    assert len(logs) == 1
    assert logs[0].event_type == AuditEventType.CASE_DETECTED
