"""
OutcomeEnvironment for Nirnay Pay Track 03.
Provides an objective, deterministic synthetic world for both Baseline and Nirnay strategies.
Evaluates outcomes without synthetic uplift math (base_prob + 0.20).
"""
from app.evaluation.models import (
    EvaluationCase,
    EvaluationOutcome,
    FailureCategory
)

class OutcomeEnvironment:
    """
    Evaluates strategy actions against case ground-truth deterministically.
    Identical environment for Baseline and Nirnay.
    """
    @staticmethod
    def evaluate_action(case: EvaluationCase, selected_action: str, compliance_blocked: bool = False, stopped: bool = False) -> tuple[EvaluationOutcome, int, FailureCategory]:
        gt = case.ground_truth
        
        # 1. Compliance or Stopping Gate
        if compliance_blocked:
            return EvaluationOutcome.BLOCKED, 0, FailureCategory.COMPLIANCE_BLOCK
            
        if stopped or selected_action == "STOP":
            return EvaluationOutcome.STOPPED, 0, FailureCategory.STOP_RULE_TRIGGERED

        if selected_action == "WAIT":
            return EvaluationOutcome.NOT_RECOVERED, 0, FailureCategory.NO_RECOVERY_OPPORTUNITY

        if selected_action == "ESCALATE":
            if "ESCALATE" in gt.effective_actions:
                return EvaluationOutcome.ESCALATED, gt.max_recoverable_amount_paise, FailureCategory.NONE
            else:
                return EvaluationOutcome.NOT_RECOVERED, 0, FailureCategory.INEFFECTIVE_INTERVENTION

        # 2. Check if Action is Prohibited by Ground Truth
        if selected_action in gt.prohibited_actions or not gt.recovery_opportunity:
            return EvaluationOutcome.NOT_RECOVERED, 0, FailureCategory.INEFFECTIVE_INTERVENTION

        # 3. Check Effective Action
        if selected_action in gt.effective_actions:
            return EvaluationOutcome.RECOVERED, gt.max_recoverable_amount_paise, FailureCategory.NONE

        return EvaluationOutcome.NOT_RECOVERED, 0, FailureCategory.INEFFECTIVE_INTERVENTION
