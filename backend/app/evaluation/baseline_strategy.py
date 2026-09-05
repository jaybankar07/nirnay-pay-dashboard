"""
Conventional Baseline Strategy for Nirnay Pay Track 03.
Implements a standard conventional recovery policy without AI diagnosis or adaptive scoring.
"""
from app.evaluation.models import EvaluationCase, ScenarioType

class ConventionalBaselineStrategy:
    """
    Conventional unguided recovery policy:
    - Payment Failure -> Generic immediate retry (ACT) unless attempt_count >= 3
    - Checkout Abandonment -> Generic recovery attempt (ACT)
    - Subscription Failure -> Standard retry (ACT)
    - Overdue Receivable -> Single generic chaser email (ACT) unless age > 30 days (ESCALATE)
    """
    @staticmethod
    def evaluate_case(case: EvaluationCase) -> tuple[str, bool, bool]:
        """
        Returns: (selected_action, compliance_blocked, stopped)
        """
        # Hard attempt rule
        if case.failed_payment_count >= 3:
            return "STOP", True, True
            
        if case.scenario_type == ScenarioType.OVERDUE_RECEIVABLE:
            if case.reason_code == "INVOICE_OVERDUE_60D":
                return "ESCALATE", False, False
            return "RETRY", False, False
            
        if case.scenario_type == ScenarioType.SUBSCRIPTION_FAILURE:
            if case.reason_code == "MANDATE_EXPIRED":
                return "RETRY", False, False  # Baseline tries unguided retry which fails
            return "RETRY", False, False
            
        return "RETRY", False, False
