from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.recovery_case import RecoveryCase
from app.utils.enums import RecoveryCaseStatus, RevenueEventType


class RecoveryCaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, merchant_id: str, case_id: str, lock_for_update: bool = False) -> Optional[RecoveryCase]:
        query = self.db.query(RecoveryCase).filter(
            RecoveryCase.merchant_id == merchant_id,
            RecoveryCase.id == case_id
        )
        if lock_for_update:
            # PostgreSQL row-level locking
            query = query.with_for_update()
        return query.first()

    def create(self, recovery_case: RecoveryCase) -> RecoveryCase:
        self.db.add(recovery_case)
        self.db.commit()
        self.db.refresh(recovery_case)
        return recovery_case

    def list_cases(
        self,
        merchant_id: str,
        status: Optional[RecoveryCaseStatus] = None,
        scenario_type: Optional[RevenueEventType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[RecoveryCase], int]:
        query = self.db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id)
        if status:
            query = query.filter(RecoveryCase.status == status)
        if scenario_type:
            query = query.filter(RecoveryCase.scenario_type == scenario_type)

        total = query.count()
        items = query.order_by(RecoveryCase.created_at.desc()).offset(offset).limit(limit).all()
        return items, total

    def update_status(self, recovery_case: RecoveryCase, new_status: RecoveryCaseStatus) -> RecoveryCase:
        recovery_case.status = new_status
        self.db.add(recovery_case)
        self.db.commit()
        self.db.refresh(recovery_case)
        return recovery_case
