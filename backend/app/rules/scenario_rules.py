from typing import List
from app.utils.enums import RevenueEventType, ActionType


class ScenarioRulesEngine:
    """
    Candidate action generator for the 4 supported revenue scenarios.
    """
    @classmethod
    def get_candidate_actions(cls, scenario_type: RevenueEventType) -> List[ActionType]:
        if scenario_type == RevenueEventType.PAYMENT_FAILURE:
            return [ActionType.RETRY, ActionType.WAIT, ActionType.REMINDER, ActionType.STOP]
        elif scenario_type == RevenueEventType.CHECKOUT_ABANDONMENT:
            return [ActionType.REMINDER, ActionType.WAIT, ActionType.STOP]
        elif scenario_type == RevenueEventType.SUBSCRIPTION_FAILURE:
            return [ActionType.RETRY, ActionType.REMINDER, ActionType.WAIT, ActionType.HUMAN_REVIEW, ActionType.STOP]
        elif scenario_type == RevenueEventType.OVERDUE_RECEIVABLE:
            return [ActionType.REMINDER, ActionType.ESCALATE, ActionType.HUMAN_REVIEW, ActionType.STOP]
        else:
            raise ValueError(f"Unsupported revenue scenario: {scenario_type}")
