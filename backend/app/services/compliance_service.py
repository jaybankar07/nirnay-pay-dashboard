from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.repositories.action_repository import ActionRepository
from app.rules.compliance_rules import ComplianceEngine
from app.services.audit_service import AuditService
from app.utils.enums import ActionType, ComplianceResult, AuditEventType, ActorType
from app.core.exceptions import NotFoundError


class ComplianceService:
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = RecoveryCaseRepository(db)
        self.action_repo = ActionRepository(db)
        self.audit_service = AuditService(db)

    def check_compliance(
        self,
        merchant_id: str,
        case_id: str,
        candidate_actions: List[ActionType]
    ) -> Dict[str, Any]:
        case = self.case_repo.get_by_id(merchant_id, case_id)
        if not case:
            raise NotFoundError(f"Recovery case '{case_id}' not found for merchant '{merchant_id}'.")

        attempts = self.action_repo.count_attempts_for_case(case_id)
        result, allowed, blocked, reason = ComplianceEngine.evaluate(candidate_actions, attempts)

        self.audit_service.log_event(
            case_id=case_id,
            event_type=AuditEventType.COMPLIANCE_CHECKED,
            actor_type=ActorType.RULE,
            event_data={
                "result": result.value,
                "allowed_actions": [a.value for a in allowed],
                "blocked_actions": [a.value for a in blocked],
                "reason": reason
            }
        )

        return {
            "result": result.value,
            "allowed_actions": [a.value for a in allowed],
            "blocked_actions": [a.value for a in blocked],
            "reason": reason
        }
