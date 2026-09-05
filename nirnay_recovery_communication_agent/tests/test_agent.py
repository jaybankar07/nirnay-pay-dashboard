"""
Automated test suite for NirnayCommunicationAgent.

Run with:
    python -m unittest discover -s tests -v

The LLM is always mocked (MockCommunicationModel) -- no live provider
or network access is required, per spec section 16.
"""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nirnay_recovery_communication_agent import NirnayCommunicationAgent, MockCommunicationModel
from nirnay_recovery_communication_agent.exceptions import (
    InputValidationError,
    DecisionConsistencyError,
    IncompleteContextError,
)
from nirnay_recovery_communication_agent import templates
from nirnay_recovery_communication_agent.enums import SelectedAction


def base_case(**overrides) -> dict:
    case = {
        "recovery_case_id": "CASE-1001",
        "scenario_type": "CARD_DECLINE",
        "customer_segment": "loyal",
        "amount_at_risk": 499.0,
        "currency": "INR",
        "diagnosis": "insufficient_funds_temporary",
        "diagnosis_confidence": 0.82,
        "recovery_rights": {"allowed": True},
        "compliance_result": {"status": "APPROVED"},
        "allowed_actions": ["RETRY", "GRACE_PERIOD", "REMINDER"],
        "selected_action": "RETRY",
        "recovery_score": 0.71,
        "decision_mode": "RULE",
        "decision_rationale": "Strong payment history and loyal segment.",
        "recovery_outcome": None,
        "requested_language": "en",
        "requested_tone": "PROFESSIONAL",
        "communication_purpose": "DECISION_EXPLANATION",
    }
    case.update(overrides)
    return case


class TestActionExplanationsAndMessages(unittest.TestCase):
    def setUp(self):
        self.agent = NirnayCommunicationAgent(llm=MockCommunicationModel())

    # 1. Retry explanation ---------------------------------------------------------
    def test_retry_explanation(self):
        result = self.agent.generate(base_case(selected_action="RETRY"))
        self.assertEqual(result["type"], "DECISION_EXPLANATION")
        self.assertIn("retry", result["summary"].lower())
        self.assertFalse(result["_meta"]["fallback_used"])

    # 2. Grace-period explanation ----------------------------------------------------
    def test_grace_period_explanation(self):
        result = self.agent.generate(base_case(selected_action="GRACE_PERIOD"))
        self.assertIn("grace period", result["summary"].lower())

    # 3. Reminder message -----------------------------------------------------------
    def test_reminder_message(self):
        result = self.agent.generate(
            base_case(
                selected_action="REMINDER",
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        self.assertEqual(result["type"], "CUSTOMER_RECOVERY_MESSAGE")
        self.assertEqual(result["action_reference"], "REMINDER")
        self.assertIn("pending", result["message"].lower())

    # 4. Human-review message --------------------------------------------------------
    def test_human_review_message(self):
        result = self.agent.generate(
            base_case(
                selected_action="HUMAN_REVIEW",
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        self.assertIn("review", result["message"].lower())

    # 5. Stop message -----------------------------------------------------------------
    def test_stop_message(self):
        result = self.agent.generate(
            base_case(
                selected_action="STOP",
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
                compliance_result={"status": "APPROVED"},
            )
        )
        self.assertIn("no further", result["message"].lower())

    # 6. Blocked decision ---------------------------------------------------------------
    def test_blocked_decision_message(self):
        result = self.agent.generate(
            base_case(
                selected_action="BLOCKED",
                compliance_result={"status": "BLOCKED", "reason": "sanctions_hit"},
                recovery_rights={"allowed": False},
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        msg = result["message"].lower()
        self.assertTrue("cannot proceed" in msg or "blocked" in msg or "unable" in msg)
        self.assertNotIn("we will retry", msg)

    def test_blocked_decision_inconsistent_input_rejected(self):
        # compliance BLOCKED but selected_action is an active-recovery action
        payload = base_case(
            selected_action="RETRY",
            compliance_result={"status": "BLOCKED"},
        )
        with self.assertRaises(DecisionConsistencyError):
            self.agent.generate(payload)

    # 7. Successful recovery outcome ----------------------------------------------------
    def test_successful_recovery_outcome(self):
        result = self.agent.generate(
            base_case(
                selected_action="RETRY",
                recovery_outcome={"status": "SUCCESS"},
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        self.assertEqual(result["action_reference"], "RETRY")
        self.assertFalse(result["_meta"]["fallback_used"])

    # 8. Failed recovery outcome ---------------------------------------------------------
    def test_failed_recovery_outcome(self):
        result = self.agent.generate(
            base_case(
                selected_action="HUMAN_REVIEW",
                recovery_outcome={"status": "FAILED"},
                communication_purpose="MERCHANT_EXPLANATION",
            )
        )
        self.assertEqual(result["type"], "MERCHANT_EXPLANATION")
        self.assertNotIn("successfully", result["why_this_action"].lower())


class TestValidationErrors(unittest.TestCase):
    def setUp(self):
        self.agent = NirnayCommunicationAgent(llm=MockCommunicationModel())

    # 9. Missing context -------------------------------------------------------------------
    def test_missing_context_raises_incomplete(self):
        payload = base_case(decision_rationale=None)
        with self.assertRaises(IncompleteContextError):
            self.agent.generate(payload)

    # 10. Invalid decision ------------------------------------------------------------------
    def test_invalid_selected_action_rejected(self):
        payload = base_case(selected_action="DO_SOMETHING_UNKNOWN")
        with self.assertRaises(InputValidationError):
            self.agent.generate(payload)

    def test_invalid_scenario_type_rejected(self):
        payload = base_case(scenario_type="NOT_A_REAL_SCENARIO")
        with self.assertRaises(InputValidationError):
            self.agent.generate(payload)

    def test_negative_amount_rejected(self):
        payload = base_case(amount_at_risk=-50)
        with self.assertRaises(InputValidationError):
            self.agent.generate(payload)

    def test_negative_payment_count_rejected(self):
        payload = base_case()
        payload["successful_payment_count"] = -3
        with self.assertRaises(InputValidationError):
            self.agent.generate(payload)

    def test_malformed_decline_codes_rejected(self):
        payload = base_case()
        payload["decline_codes"] = ["OK", 123, ""]
        with self.assertRaises(InputValidationError):
            self.agent.generate(payload)


class TestLLMFailureHandling(unittest.TestCase):
    # 11. LLM timeout -----------------------------------------------------------------------
    def test_llm_timeout_falls_back(self):
        agent = NirnayCommunicationAgent(
            llm=MockCommunicationModel(raise_timeout=True)
        )
        result = agent.generate(
            base_case(
                selected_action="RETRY",
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        self.assertTrue(result["_meta"]["fallback_used"])
        self.assertIn("retry", result["message"].lower())

    # 12. Invalid LLM output ------------------------------------------------------------------
    def test_invalid_llm_output_shape_falls_back(self):
        def bad_explanation(request):
            return {"summary": "only summary, missing required keys"}

        agent = NirnayCommunicationAgent(
            llm=MockCommunicationModel(force_explanation=bad_explanation)
        )
        result = agent.generate(base_case(selected_action="RETRY"))
        self.assertTrue(result["_meta"]["fallback_used"])

    # 13. Contradictory LLM output --------------------------------------------------------------
    def test_contradictory_output_falls_back(self):
        def bad_message(request):
            return "We will retry your payment right away."  # contradicts STOP

        agent = NirnayCommunicationAgent(
            llm=MockCommunicationModel(force_customer_message=bad_message)
        )
        result = agent.generate(
            base_case(
                selected_action="STOP",
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        self.assertTrue(result["_meta"]["fallback_used"])
        self.assertNotIn("we will retry", result["message"].lower())

    # 14. Hallucinated amount ---------------------------------------------------------------------
    def test_hallucinated_amount_falls_back(self):
        def bad_message(request):
            return "Please pay INR 999999 immediately to avoid issues."

        agent = NirnayCommunicationAgent(
            llm=MockCommunicationModel(force_customer_message=bad_message)
        )
        result = agent.generate(
            base_case(
                selected_action="REMINDER",
                amount_at_risk=499.0,
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        self.assertTrue(result["_meta"]["fallback_used"])
        self.assertNotIn("999999", result["message"])

    # 15. Hallucinated recovery --------------------------------------------------------------------
    def test_hallucinated_recovery_claim_falls_back(self):
        def bad_message(request):
            return "Your payment has been successfully received, thank you!"

        agent = NirnayCommunicationAgent(
            llm=MockCommunicationModel(force_customer_message=bad_message)
        )
        result = agent.generate(
            base_case(
                selected_action="RETRY",
                recovery_outcome=None,
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        self.assertTrue(result["_meta"]["fallback_used"])
        self.assertNotIn("successfully received", result["message"].lower())

    # 16. Unsafe/threatening language -----------------------------------------------------------------
    def test_threatening_language_falls_back(self):
        def bad_message(request):
            return "Pay now or we will take legal action against you immediately."

        agent = NirnayCommunicationAgent(
            llm=MockCommunicationModel(force_customer_message=bad_message)
        )
        result = agent.generate(
            base_case(
                selected_action="REMINDER",
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        self.assertTrue(result["_meta"]["fallback_used"])
        self.assertNotIn("legal action", result["message"].lower())


class TestLanguageAndFallbackTemplates(unittest.TestCase):
    # 17. Language fallback -----------------------------------------------------------------------------
    def test_unsupported_language_falls_back_to_english(self):
        agent = NirnayCommunicationAgent(llm=MockCommunicationModel())
        result = agent.generate(
            base_case(
                selected_action="RETRY",
                requested_language="fr",
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        self.assertEqual(result["language"], "en")
        self.assertTrue(result["_meta"]["language_fallback"])

    # 18. Deterministic fallback templates exist & are safe for every action --------------------------
    def test_all_actions_have_safe_deterministic_fallbacks(self):
        for action in SelectedAction:
            msg = templates.fallback_customer_message(action)
            self.assertTrue(len(msg) > 0)
            lowered = msg.lower()
            for bad_word in ("legal action", "penalty", "guarantee", "immediately or"):
                self.assertNotIn(bad_word, lowered)

            merchant_summary = templates.fallback_merchant_summary(action)
            self.assertTrue(len(merchant_summary) > 0)

            explanation = templates.fallback_decision_explanation(action)
            self.assertIn(action.value, explanation)


class TestDecisionNeverOverridden(unittest.TestCase):
    """The agent must never substitute a different action than the one
    supplied on selected_action, regardless of communication_purpose."""

    def test_agent_never_recommends_a_different_action(self):
        agent = NirnayCommunicationAgent(llm=MockCommunicationModel())
        result = agent.generate(
            base_case(
                selected_action="GRACE_PERIOD",
                communication_purpose="CUSTOMER_RECOVERY_MESSAGE",
            )
        )
        self.assertEqual(result["action_reference"], "GRACE_PERIOD")
        self.assertNotIn("retry the payment", result["message"].lower())

    def test_input_object_is_not_mutated(self):
        agent = NirnayCommunicationAgent(llm=MockCommunicationModel())
        payload = base_case(selected_action="STOP")
        original = copy.deepcopy(payload)
        agent.generate(payload)
        self.assertEqual(payload, original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
