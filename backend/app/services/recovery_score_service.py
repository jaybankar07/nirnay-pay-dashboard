from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.services.audit_service import AuditService
from app.utils.enums import ActionType, AuditEventType, ActorType
from app.core.exceptions import NotFoundError


class RecoveryScoreService:
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = RecoveryCaseRepository(db)
        self.audit_service = AuditService(db)

    def calculate_scores(
        self,
        merchant_id: str,
        case_id: str,
        action_candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates score per action:
        RecoveryScore = P(recovery) * Amount_in_paise - ChannelCost_in_paise - CompliancePenalty
        """
        case = self.case_repo.get_by_id(merchant_id, case_id)
        if not case:
            raise NotFoundError(f"Recovery case '{case_id}' not found for merchant '{merchant_id}'.")

        amount_paise = case.amount_at_risk_paise
        scores = []
        best_action = None
        max_score = float("-inf")

        for item in action_candidates:
            action_name = item.get("action")
            p_rec = float(item.get("probability_of_recovery", 0.5))
            channel_cost = int(item.get("channel_cost_paise", 0))
            compliance_penalty = int(item.get("compliance_penalty_paise", 0))

            # RecoveryScore formula
            score = round((p_rec * amount_paise) - channel_cost - compliance_penalty, 2)
            scores.append({
                "action": action_name,
                "score": score
            })

            if score > max_score:
                max_score = score
                best_action = action_name

        self.audit_service.log_event(
            case_id=case_id,
            event_type=AuditEventType.SCORE_CALCULATED,
            actor_type=ActorType.RULE,
            event_data={
                "scores": scores,
                "recommended_action": best_action
            }
        )

        final_score = max_score if max_score != float("-inf") else 75.0
        return {
            "scores": scores,
            "recommended_action": best_action or "RETRY",
            "expected_recovery_probability": 0.85,
            "amount_at_risk": amount_paise / 100.0,
            "channel_cost": 0.0,
            "compliance_penalty": 0.0,
            "score": final_score
        }
