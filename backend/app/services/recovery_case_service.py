from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.recovery_case import RecoveryCase
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.utils.enums import RecoveryCaseStatus, RevenueEventType
from app.core.exceptions import NotFoundError, ValidationError


class RecoveryCaseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RecoveryCaseRepository(db)

    def create_case(
        self,
        merchant_id: str,
        customer_id: Optional[str],
        revenue_event_id: str,
        scenario_type: RevenueEventType,
        amount_at_risk_paise: int
    ) -> RecoveryCase:
        if amount_at_risk_paise < 0:
            raise ValidationError("Amount at risk cannot be negative.")

        case = RecoveryCase(
            merchant_id=merchant_id,
            customer_id=customer_id,
            revenue_event_id=revenue_event_id,
            status=RecoveryCaseStatus.DETECTED,
            scenario_type=scenario_type,
            amount_at_risk_paise=amount_at_risk_paise
        )
        return self.repo.create(case)

    def get_case(self, merchant_id: str, case_id: str) -> RecoveryCase:
        case = self.repo.get_by_id(merchant_id, case_id)
        if not case:
            raise NotFoundError(f"Recovery case '{case_id}' not found for merchant '{merchant_id}'.")
        return case

    def list_cases(
        self,
        merchant_id: str,
        status: Optional[RecoveryCaseStatus] = None,
        scenario_type: Optional[RevenueEventType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[RecoveryCase], int]:
        return self.repo.list_cases(merchant_id, status, scenario_type, limit, offset)
