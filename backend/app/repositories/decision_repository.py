from typing import Optional
from sqlalchemy.orm import Session
from app.models.decision import Decision


class DecisionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, decision_id: str) -> Optional[Decision]:
        return self.db.query(Decision).filter(Decision.id == decision_id).first()

    def get_latest_for_case(self, case_id: str) -> Optional[Decision]:
        return self.db.query(Decision).filter(
            Decision.recovery_case_id == case_id
        ).order_by(Decision.decided_at.desc()).first()

    def create(self, decision: Decision) -> Decision:
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision
