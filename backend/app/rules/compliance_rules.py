from typing import List, Dict, Any, Tuple, Optional
from app.utils.enums import ComplianceResult, ActionType


class ComplianceEngine:
    MAX_ATTEMPTS = 3

    @classmethod
    def evaluate(
        self,
        candidate_actions: List[ActionType],
        previous_attempts_count: int,
        merchant_policy: Optional[Dict[str, Any]] = None
    ) -> Tuple[ComplianceResult, List[ActionType], List[ActionType], str]:
        max_allowed_attempts = self.MAX_ATTEMPTS
        if merchant_policy and "max_attempts" in merchant_policy:
            max_allowed_attempts = merchant_policy["max_attempts"]

        if previous_attempts_count >= max_allowed_attempts:
            return (
                ComplianceResult.BLOCKED,
                [],
                candidate_actions,
                f"Maximum attempt limit ({max_allowed_attempts}) reached."
            )

        allowed = []
        blocked = []
        for action in candidate_actions:
            # ESCALATE might be blocked if max attempts reached soon
            allowed.append(action)

        return (
            ComplianceResult.APPROVED if allowed else ComplianceResult.BLOCKED,
            allowed,
            blocked,
            "Compliance check completed."
        )
