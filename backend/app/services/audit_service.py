from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.utils.enums import AuditEventType, ActorType


def sanitize_event_data(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not data:
        return {}
    clean = {}
    for k, v in data.items():
        if hasattr(v, 'hex') or hasattr(v, '__composite_values__'):  # UUID
            clean[k] = str(v)
        elif hasattr(v, 'value'):  # Enum
            clean[k] = v.value
        elif isinstance(v, dict):
            clean[k] = sanitize_event_data(v)
        elif isinstance(v, list):
            clean[k] = [str(item) if hasattr(item, 'hex') else item for item in v]
        else:
            clean[k] = v
    return clean


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditRepository(db)

    def log_event(
        self,
        case_id: str,
        event_type: AuditEventType,
        actor_type: ActorType,
        event_data: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        event = AuditEvent(
            recovery_case_id=str(case_id),
            event_type=event_type,
            actor_type=actor_type,
            event_data_json=sanitize_event_data(event_data)
        )
        return self.repo.create(event)

    def get_audit_trail(self, case_id: str) -> List[AuditEvent]:
        return self.repo.list_by_case_id(str(case_id))
