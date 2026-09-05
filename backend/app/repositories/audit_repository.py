from typing import List
from sqlalchemy.orm import Session
from app.models.audit_event import AuditEvent


class AuditRepository:
    """
    Append-Only Audit Repository.
    Strictly exposes only `create` and `list_by_case_id` methods.
    Does NOT provide update or delete operations to guarantee immutability.
    """
    def __init__(self, db: Session):
        self.db = db

    def create(self, audit_event: AuditEvent) -> AuditEvent:
        self.db.add(audit_event)
        self.db.commit()
        self.db.refresh(audit_event)
        return audit_event

    def list_by_case_id(self, case_id: str) -> List[AuditEvent]:
        return self.db.query(AuditEvent).filter(
            AuditEvent.recovery_case_id == case_id
        ).order_by(AuditEvent.created_at.asc()).all()
