"""
Example: calling the agent programmatically from another system.

Run:
    python examples/example_usage.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nirnay_agent import NirnayCommunicationAgent, MockCommunicationModel
# In production, swap MockCommunicationModel for:
# from nirnay_agent.llm.anthropic_provider import AnthropicCommunicationModel
# llm = AnthropicCommunicationModel()

APPROVED_DECISION = {
    "recovery_case_id": "CASE-88213",
    "scenario_type": "CARD_DECLINE",
    "customer_segment": "loyal",
    "amount_at_risk": 1499.0,
    "currency": "INR",
    "diagnosis": "insufficient_funds_temporary",
    "diagnosis_confidence": 0.86,
    "recovery_rights": {"allowed": True},
    "compliance_result": {"status": "APPROVED"},
    "allowed_actions": ["RETRY", "GRACE_PERIOD", "REMINDER"],
    "selected_action": "GRACE_PERIOD",
    "recovery_score": 0.74,
    "decision_mode": "RULE",
    "decision_rationale": (
        "Customer has a strong payment history and is classified as "
        "loyal; a grace period is preferred over an aggressive retry."
    ),
    "recovery_outcome": None,
    "requested_language": "en",
    "requested_tone": "FRIENDLY",
    "communication_purpose": "CUSTOMER_RECOVERY_MESSAGE",
}


def main():
    agent = NirnayCommunicationAgent(
        llm=MockCommunicationModel(), provider_name="mock-demo"
    )

    print("=== Customer message ===")
    print(json.dumps(agent.generate(APPROVED_DECISION), indent=2))

    print("\n=== Merchant explanation for the same decision ===")
    merchant_payload = dict(APPROVED_DECISION)
    merchant_payload["communication_purpose"] = "MERCHANT_EXPLANATION"
    print(json.dumps(agent.generate(merchant_payload), indent=2))

    print("\n=== Decision explanation for the same decision ===")
    explanation_payload = dict(APPROVED_DECISION)
    explanation_payload["communication_purpose"] = "DECISION_EXPLANATION"
    print(json.dumps(agent.generate(explanation_payload), indent=2))


if __name__ == "__main__":
    main()
