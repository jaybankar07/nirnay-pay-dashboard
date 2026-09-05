from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.repositories.customer_repository import CustomerRepository
from app.models.recovery_policy import RecoveryPolicy
from app.rules.recovery_rights_rules import RecoveryRightsEngine
from app.services.audit_service import AuditService
from app.utils.enums import CustomerSegment, RecoveryRightTreatment, AuditEventType, ActorType
from app.core.exceptions import NotFoundError


class RecoveryRightsService:
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = RecoveryCaseRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.audit_service = AuditService(db)

    def determine_rights(
        self,
        merchant_id: str,
        case_id: str,
        customer_segment: Optional[CustomerSegment] = None
    ) -> Dict[str, Any]:
        case = self.case_repo.get_by_id(merchant_id, case_id)
        if not case:
            raise NotFoundError(f"Recovery case '{case_id}' not found for merchant '{merchant_id}'.")

        # Determine segment from parameter or customer entity
        segment = customer_segment
        if not segment and case.customer_id:
            customer = self.customer_repo.get_by_id(merchant_id, case.customer_id)
            if customer:
                segment = customer.customer_segment

        if not segment:
            segment = CustomerSegment.FIRST_TIME

        # Load active merchant policy
        policy = self.db.query(RecoveryPolicy).filter(
            RecoveryPolicy.merchant_id == merchant_id,
            RecoveryPolicy.active == True
        ).first()

        policy_rules = policy.rules_json if policy else None
        treatment, reason, is_fallback = RecoveryRightsEngine.determine_treatment(segment, policy_rules)

        self.audit_service.log_event(
            case_id=case_id,
            event_type=AuditEventType.RECOVERY_RIGHTS_APPLIED,
            actor_type=ActorType.RULE if not is_fallback else ActorType.SYSTEM,
            event_data={
                "customer_segment": segment.value if isinstance(segment, CustomerSegment) else str(segment),
                "recovery_right": treatment.value,
                "reason": reason,
                "is_fallback": is_fallback
            }
        )

        return {
            "recovery_right": treatment.value,
            "reason": reason
        }
