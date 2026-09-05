from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.recovery_action import RecoveryAction
from app.models.recovery_outcome import RecoveryOutcome


class ActionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_action_by_id(self, action_id: str) -> Optional[RecoveryAction]:
        return self.db.query(RecoveryAction).filter(RecoveryAction.id == action_id).first()

    def create_action(self, action: RecoveryAction) -> RecoveryAction:
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def create_outcome(self, outcome: RecoveryOutcome) -> RecoveryOutcome:
        self.db.add(outcome)
        self.db.commit()
        self.db.refresh(outcome)
        return outcome

    def get_outcome_by_action_id(self, action_id: str) -> Optional[RecoveryOutcome]:
        return self.db.query(RecoveryOutcome).filter(RecoveryOutcome.action_id == action_id).first()

    def count_attempts_for_case(self, case_id: str) -> int:
        from app.models.decision import Decision
        return self.db.query(RecoveryAction).join(
            Decision, RecoveryAction.decision_id == Decision.id
        ).filter(Decision.recovery_case_id == case_id).count()
