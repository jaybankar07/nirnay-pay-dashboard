from typing import Tuple
from app.utils.enums import RevenueEventType, DecisionMode, ActionType


class DeterministicFallback:
    @classmethod
    def get_fallback_diagnosis(cls, reason_code: str = None, scenario_type: RevenueEventType = RevenueEventType.PAYMENT_FAILURE) -> Tuple[str, float, DecisionMode, str]:
        code = (reason_code or "DEFAULT").upper()
        if "EXPIRED" in code:
            root_cause = "card_expired"
        elif "INSUFFICIENT" in code:
            root_cause = "insufficient_funds"
        elif "DECLINE" in code or "TEMPORARY" in code:
            root_cause = "temporary_payment_failure"
        else:
            root_cause = f"unspecified_{scenario_type.value.lower()}_risk"

        confidence = 0.70
        mode = DecisionMode.FALLBACK
        rationale = "Deterministic fallback diagnosis applied due to AI unavailability or invalid AI response."
        return root_cause, confidence, mode, rationale

    @classmethod
    def get_fallback_rationale(cls, selected_action: ActionType, recovery_right_treatment: str) -> Tuple[str, float, DecisionMode]:
        rationale = f"Rule-based decision selects {selected_action.value} adhering to business treatment {recovery_right_treatment}."
        confidence = 0.85
        mode = DecisionMode.FALLBACK
        return rationale, confidence, mode
