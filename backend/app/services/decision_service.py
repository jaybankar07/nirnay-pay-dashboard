from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.repositories.decision_repository import DecisionRepository
from app.repositories.action_repository import ActionRepository
from app.models.decision import Decision
from app.services.compliance_service import ComplianceService
from app.services.recovery_rights_service import RecoveryRightsService
from app.services.recovery_score_service import RecoveryScoreService
from app.services.communication_service import CommunicationService
from app.services.audit_service import AuditService
from app.rules.stopping_rules import StoppingRulesEngine
from app.utils.enums import (
    ActionType, ComplianceResult, RecoveryRightTreatment,
    DecisionMode, AuditEventType, ActorType, RecoveryCaseStatus
)
from app.core.exceptions import NotFoundError
from app.core.logging import logger


class DecisionService:
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = RecoveryCaseRepository(db)
        self.decision_repo = DecisionRepository(db)
        self.action_repo = ActionRepository(db)
        self.compliance_service = ComplianceService(db)
        self.rights_service = RecoveryRightsService(db)
        self.score_service = RecoveryScoreService(db)
        self.comm_service = CommunicationService(db)
        self.audit_service = AuditService(db)

    async def make_decision(
        self,
        merchant_id: str,
        case_id: str,
        candidate_actions: List[ActionType]
    ) -> Dict[str, Any]:
        case = self.case_repo.get_by_id(merchant_id, case_id)
        if not case:
            raise NotFoundError(f"Recovery case '{case_id}' not found for merchant '{merchant_id}'.")

        # 1. Compliance Check
        compliance = self.compliance_service.check_compliance(merchant_id, case_id, candidate_actions)
        if compliance["result"] == ComplianceResult.BLOCKED.value or not compliance["allowed_actions"]:
            decision = Decision(
                recovery_case_id=case_id,
                diagnosis=case.root_cause,
                compliance_result=ComplianceResult.BLOCKED,
                recovery_right=RecoveryRightTreatment.STOP,
                recovery_score=0.0,
                selected_action=ActionType.STOP,
                ai_rationale="Compliance gate blocked recovery action.",
                ai_confidence=1.0,
                decision_mode=DecisionMode.RULE
            )
            saved_dec = self.decision_repo.create(decision)
            self.db.commit()  # COMMIT DECISION IMMEDIATELY
            self.case_repo.update_status(case, RecoveryCaseStatus.BLOCKED)
            self.audit_service.log_event(case_id, AuditEventType.DECISION_MADE, ActorType.RULE, {"selected_action": "STOP", "reason": "COMPLIANCE_BLOCKED"})
            return {
                "decision_id": str(saved_dec.id),
                "case_id": str(case.id),
                "compliance_result": ComplianceResult.BLOCKED.value,
                "recovery_right": RecoveryRightTreatment.STOP.value,
                "recovery_score": 0.0,
                "selected_action": ActionType.STOP.value,
                "decision_mode": DecisionMode.RULE.value,
                "rationale": "Compliance gate blocked recovery action."
            }

        allowed_actions = [ActionType(a) for a in compliance["allowed_actions"]]

        # 2. Recovery Rights Policy
        rights = self.rights_service.determine_rights(merchant_id, case_id)
        rec_right_treatment = RecoveryRightTreatment(rights["recovery_right"])

        if rec_right_treatment == RecoveryRightTreatment.STOP:
            selected_action = ActionType.STOP
        elif rec_right_treatment == RecoveryRightTreatment.HUMAN_REVIEW:
            selected_action = ActionType.HUMAN_REVIEW
        elif rec_right_treatment == RecoveryRightTreatment.GRACE_PERIOD:
            selected_action = ActionType.WAIT
        elif rec_right_treatment == RecoveryRightTreatment.SOFT_REMINDER:
            selected_action = ActionType.REMINDER if ActionType.REMINDER in allowed_actions else allowed_actions[0]
        elif rec_right_treatment == RecoveryRightTreatment.ESCALATE:
            selected_action = ActionType.ESCALATE if ActionType.ESCALATE in allowed_actions else allowed_actions[0]
        else:
            selected_action = ActionType.RETRY if ActionType.RETRY in allowed_actions else allowed_actions[0]

        # 3. RecoveryScore Calculation
        score_candidates = [{"action": a.value, "probability_of_recovery": 0.70, "channel_cost_paise": 0} for a in allowed_actions]
        score_data = self.score_service.calculate_scores(merchant_id, case_id, score_candidates)

        selected_score = 0.0
        for item in score_data["scores"]:
            if item["action"] == selected_action.value:
                selected_score = item["score"]
                break

        # 4. Stopping Rules Check
        attempts = self.action_repo.count_attempts_for_case(case_id)
        should_stop, stop_reason = StoppingRulesEngine.should_stop(attempts)
        if should_stop:
            selected_action = ActionType.STOP
            self.audit_service.log_event(case_id, AuditEventType.CASE_STOPPED, ActorType.RULE, {"reason": stop_reason})

        initial_rationale = f"Selected {selected_action.value} based on {rec_right_treatment.value} policy and score {selected_score}."

        # 5. Save & COMMIT Decision FIRST (Decoupled from LLM call)
        decision = Decision(
            recovery_case_id=case_id,
            diagnosis=case.root_cause,
            compliance_result=ComplianceResult.APPROVED,
            recovery_right=rec_right_treatment,
            recovery_score=selected_score,
            selected_action=selected_action,
            ai_rationale=initial_rationale,
            ai_confidence=0.90,
            decision_mode=DecisionMode.RULE
        )
        saved_decision = self.decision_repo.create(decision)
        self.db.commit()  # COMMIT DECISION BEFORE CALLING AGENT 2

        # Update case status
        if selected_action == ActionType.STOP:
            self.case_repo.update_status(case, RecoveryCaseStatus.STOPPED)
        else:
            self.case_repo.update_status(case, RecoveryCaseStatus.APPROVED)

        # 6. Call Agent 2 for Explanation out-of-transaction (failures won't rollback decision)
        explanation = initial_rationale
        try:
            comm_res = await self.comm_service.generate_explanation(merchant_id, case_id, str(saved_decision.id))
            if comm_res and "explanation" in comm_res:
                explanation = comm_res["explanation"]
                saved_decision.ai_rationale = explanation
                self.db.commit()
        except Exception as e:
            logger.warning(f"Communication Agent 2 execution failed cleanly: {str(e)}. Decision {saved_decision.id} remains committed.")

        why_selected = f"Selected {selected_action.value} based on {rec_right_treatment.value} policy and recovery score {selected_score}."
        why_rejected = {}
        all_possible = [ActionType.RETRY, ActionType.REMINDER, ActionType.ESCALATE, ActionType.STOP, ActionType.WAIT]
        for act in all_possible:
            if act != selected_action:
                if act not in allowed_actions:
                    why_rejected[act.value] = "Blocked by pre-execution compliance checks or customer communication preferences."
                elif act == ActionType.STOP:
                    why_rejected[act.value] = "Case remains fully eligible for recovery; maximum attempt threshold not reached."
                elif act == ActionType.ESCALATE:
                    why_rejected[act.value] = "Current failure pattern does not require manual high-priority support escalation."
                elif act == ActionType.REMINDER:
                    why_rejected[act.value] = "Technical payment failure requires direct gateway retry rather than customer reminder."
                elif act == ActionType.RETRY:
                    why_rejected[act.value] = "Customer behavioral/grace-period state favors reminder or wait strategy."
                elif act == ActionType.WAIT:
                    why_rejected[act.value] = "Immediate recovery opportunity identified; grace period hold not indicated."
                else:
                    why_rejected[act.value] = f"Yielded lower expected net recovery value than {selected_action.value}."

        return {
            "decision_id": str(saved_decision.id),
            "case_id": str(case.id),
            "compliance_result": ComplianceResult.APPROVED.value,
            "recovery_right": rec_right_treatment.value,
            "recovery_score": selected_score,
            "selected_action": selected_action.value,
            "decision_mode": DecisionMode.RULE.value,
            "rationale": explanation,
            "why_selected": why_selected,
            "why_rejected": why_rejected
        }

