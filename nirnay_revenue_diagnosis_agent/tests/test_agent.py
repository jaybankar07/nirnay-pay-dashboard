"""
Comprehensive test suite for the Nirnay Revenue Diagnosis Agent.

Runs entirely offline against MockDiagnosisModel -- no live LLM provider
is required (section 16).

Run with:
    python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import asyncio
import unittest

from nirnay_revenue_diagnosis_agent import (
    AgentConfig,
    DiagnosisMode,
    InputValidationError,
    RevenueDiagnosisAgent,
    ScenarioType,
)
from nirnay_revenue_diagnosis_agent.enums import is_valid_root_cause
from nirnay_revenue_diagnosis_agent.exceptions import OutputValidationError
from nirnay_revenue_diagnosis_agent.llm import LLMDiagnosisResponse, MockDiagnosisModel
from nirnay_revenue_diagnosis_agent.models import DiagnosisResult, Evidence
from nirnay_revenue_diagnosis_agent.output_validation import validate_output


def fast_config(**overrides) -> AgentConfig:
    defaults = dict(
        llm_timeout_seconds=1.0,
        max_retries=1,
        base_backoff_seconds=0.001,
        max_backoff_seconds=0.002,
    )
    defaults.update(overrides)
    return AgentConfig(**defaults)


class TestClearPaymentFailure(unittest.TestCase):
    """1. Clear payment failure -> RULE mode, high confidence."""

    def test_insufficient_funds_clean_history(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "case_1",
                "scenario_type": "PAYMENT_FAILURE",
                "decline_code": "INSUFFICIENT_FUNDS",
                "successful_payment_count": 12,
                "failed_payment_count": 0,
            }
        )
        self.assertEqual(result.root_cause, "INSUFFICIENT_FUNDS")
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.RULE.value)
        self.assertGreaterEqual(result.confidence, 0.90)
        self.assertTrue(any(e.signal == "decline_code" for e in result.evidence))

    def test_temporary_processing_failure_matches_spec_example(self):
        # Matches the exact example from section 7 of the spec.
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "case_spec_example",
                "scenario_type": "PAYMENT_FAILURE",
                "failed_payment_count": 0,
                "successful_payment_count": 12,
                "decline_code": "TEMPORARY_PROCESSING_ERROR",
            }
        )
        self.assertEqual(result.root_cause, "TEMPORARY_PROCESSING_FAILURE")
        self.assertNotEqual(result.root_cause, "INSUFFICIENT_FUNDS")


class TestAmbiguousPaymentFailure(unittest.TestCase):
    """2. Ambiguous payment failure -> LLM consulted, AI mode."""

    def test_no_decline_code_uses_llm(self):
        llm = MockDiagnosisModel(
            mode="success",
            fixed_response=LLMDiagnosisResponse(
                root_cause="TEMPORARY_PROCESSING_FAILURE",
                confidence=0.6,
                diagnosis="Customer text suggests a one-off glitch, not chronic failure.",
                evidence=[
                    {
                        "signal": "customer_messages[0]",
                        "relevance": "Customer said it worked on retry.",
                    }
                ],
                uncertainties=["No decline_code confirms this."],
            ),
        )
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config())
        result = agent.diagnose(
            {
                "recovery_case_id": "case_2",
                "scenario_type": "PAYMENT_FAILURE",
                "customer_messages": ["It failed once but worked when I tried again."],
            }
        )
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.AI.value)
        self.assertEqual(result.root_cause, "TEMPORARY_PROCESSING_FAILURE")
        self.assertLess(result.confidence, 0.90)  # text-derived, capped below explicit band
        self.assertEqual(llm.call_count, 1)


class TestCheckoutAbandonment(unittest.TestCase):
    """3. Checkout abandonment scenario."""

    def test_payment_stage_dropoff(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "case_3",
                "scenario_type": "CHECKOUT_ABANDONMENT",
                "checkout_info": {"last_stage": "payment"},
            }
        )
        self.assertEqual(result.root_cause, "PAYMENT_STAGE_DROPOFF")
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.RULE.value)

    def test_checkout_error(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "case_3b",
                "scenario_type": "CHECKOUT_ABANDONMENT",
                "checkout_info": {"error": "3DS_VERIFICATION_TIMEOUT"},
            }
        )
        self.assertEqual(result.root_cause, "CHECKOUT_ERROR")


class TestSubscriptionFailure(unittest.TestCase):
    """4. Subscription failure scenario."""

    def test_mandate_failure(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "case_4",
                "scenario_type": "SUBSCRIPTION_FAILURE",
                "subscription_info": {"mandate_status": "revoked"},
            }
        )
        self.assertEqual(result.root_cause, "MANDATE_FAILURE")
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.RULE.value)

    def test_decline_code_maps_into_subscription_taxonomy(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "case_4b",
                "scenario_type": "SUBSCRIPTION_FAILURE",
                "decline_code": "INSUFFICIENT_FUNDS",
            }
        )
        self.assertEqual(result.root_cause, "INSUFFICIENT_FUNDS")
        self.assertTrue(
            is_valid_root_cause(ScenarioType.SUBSCRIPTION_FAILURE, result.root_cause)
        )


class TestOverdueReceivable(unittest.TestCase):
    """5. Overdue receivable scenario."""

    def test_customer_dispute(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "case_5",
                "scenario_type": "OVERDUE_RECEIVABLE",
                "receivable_info": {"dispute_flag": True},
            }
        )
        self.assertEqual(result.root_cause, "CUSTOMER_DISPUTE")
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.RULE.value)

    def test_cash_flow_delay(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "case_5b",
                "scenario_type": "OVERDUE_RECEIVABLE",
                "receivable_info": {"days_overdue": 20, "cash_flow_issue": True},
            }
        )
        self.assertEqual(result.root_cause, "CASH_FLOW_DELAY")


class TestMissingFields(unittest.TestCase):
    """6. Missing fields handled gracefully, never invents facts."""

    def test_minimal_input_no_llm(self):
        agent = RevenueDiagnosisAgent()  # no LLM configured
        result = agent.diagnose(
            {"recovery_case_id": "case_6", "scenario_type": "PAYMENT_FAILURE"}
        )
        self.assertEqual(result.root_cause, "UNKNOWN_PAYMENT_FAILURE")
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.FALLBACK.value)
        self.assertLessEqual(result.confidence, 0.10)
        self.assertEqual(result.evidence, [])

    def test_only_case_id_and_scenario_required(self):
        # Everything else optional -- must not raise.
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {"recovery_case_id": "case_6b", "scenario_type": "CHECKOUT_ABANDONMENT"}
        )
        self.assertEqual(result.root_cause, "UNKNOWN_ABANDONMENT")


class TestConflictingSignals(unittest.TestCase):
    """7. Conflicting signals -> confidence lowered, uncertainty reported."""

    def test_temporary_code_with_repeated_failures_lowers_confidence(self):
        agent = RevenueDiagnosisAgent()
        clean = agent.diagnose(
            {
                "recovery_case_id": "case_7_clean",
                "scenario_type": "PAYMENT_FAILURE",
                "decline_code": "TEMPORARY_PROCESSING_ERROR",
                "failed_payment_count": 0,
            }
        )
        conflicted = agent.diagnose(
            {
                "recovery_case_id": "case_7_conflict",
                "scenario_type": "PAYMENT_FAILURE",
                "decline_code": "TEMPORARY_PROCESSING_ERROR",
                "failed_payment_count": 5,
            }
        )
        self.assertEqual(conflicted.root_cause, "TEMPORARY_PROCESSING_FAILURE")
        self.assertLess(conflicted.confidence, clean.confidence)
        self.assertTrue(len(conflicted.uncertainties) > 0)

    def test_llm_conflict_with_structured_signal_prefers_structured(self):
        # Structured evidence says INSUFFICIENT_FUNDS is close but not
        # decisive-threshold on its own in this synthetic setup: force via
        # a scenario where rule engine has *some* signal but LLM disagrees.
        llm = MockDiagnosisModel(
            mode="success",
            fixed_response=LLMDiagnosisResponse(
                root_cause="UNKNOWN_ABANDONMENT",
                confidence=0.5,
                diagnosis="Text suggests generic abandonment.",
                evidence=[],
                uncertainties=[],
            ),
        )
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config(always_consult_llm=True))
        result = agent.diagnose(
            {
                "recovery_case_id": "case_7c",
                "scenario_type": "CHECKOUT_ABANDONMENT",
                "checkout_info": {"last_stage": "price_review", "price_viewed": True},
            }
        )
        # Structured signal (PRICE_FRICTION) should win over LLM's UNKNOWN.
        self.assertEqual(result.root_cause, "PRICE_FRICTION")
        self.assertTrue(any("conflict" in u.lower() for u in result.uncertainties))


class TestInvalidLLMOutput(unittest.TestCase):
    """8. Invalid/malformed LLM output triggers fallback."""

    def test_malformed_response_falls_back(self):
        llm = MockDiagnosisModel(mode="malformed")
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config())
        result = agent.diagnose(
            {"recovery_case_id": "case_8", "scenario_type": "PAYMENT_FAILURE"}
        )
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.FALLBACK.value)

    def test_response_with_invalid_root_cause_is_rejected(self):
        llm = MockDiagnosisModel(
            mode="success",
            fixed_response=LLMDiagnosisResponse(
                root_cause="NOT_A_REAL_ROOT_CAUSE",
                confidence=0.8,
                diagnosis="bogus",
            ),
        )
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config())
        result = agent.diagnose(
            {"recovery_case_id": "case_8b", "scenario_type": "PAYMENT_FAILURE"}
        )
        # Parsing rejects the payload -> deterministic fallback used instead.
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.FALLBACK.value)
        self.assertNotEqual(result.root_cause, "NOT_A_REAL_ROOT_CAUSE")

    def test_response_with_out_of_range_confidence_is_rejected(self):
        llm = MockDiagnosisModel(
            mode="success",
            fixed_response=LLMDiagnosisResponse(
                root_cause="UNKNOWN_PAYMENT_FAILURE",
                confidence=1.5,
                diagnosis="bogus confidence",
            ),
        )
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config())
        result = agent.diagnose(
            {"recovery_case_id": "case_8c", "scenario_type": "PAYMENT_FAILURE"}
        )
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.FALLBACK.value)


class TestLLMTimeout(unittest.TestCase):
    """9. LLM timeout -> retried once, then deterministic fallback."""

    def test_timeout_triggers_fallback_after_retry(self):
        llm = MockDiagnosisModel(mode="timeout")
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config(max_retries=1))
        result = agent.diagnose(
            {"recovery_case_id": "case_9", "scenario_type": "PAYMENT_FAILURE"}
        )
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.FALLBACK.value)
        self.assertEqual(llm.call_count, 2)  # 1 initial + 1 retry

    def test_never_retries_more_than_configured(self):
        llm = MockDiagnosisModel(mode="timeout")
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config(max_retries=3))
        agent.diagnose({"recovery_case_id": "case_9b", "scenario_type": "PAYMENT_FAILURE"})
        self.assertEqual(llm.call_count, 4)  # 1 initial + 3 retries, never more


class TestLLMProviderFailure(unittest.TestCase):
    """10. Generic LLM provider failure -> deterministic fallback."""

    def test_provider_error_triggers_fallback(self):
        llm = MockDiagnosisModel(mode="error")
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config())
        result = agent.diagnose(
            {"recovery_case_id": "case_10", "scenario_type": "PAYMENT_FAILURE"}
        )
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.FALLBACK.value)

    def test_flaky_provider_recovers_on_retry(self):
        llm = MockDiagnosisModel(
            mode="flaky",
            fail_times=1,
            fixed_response=LLMDiagnosisResponse(
                root_cause="UNKNOWN_PAYMENT_FAILURE",
                confidence=0.2,
                diagnosis="Recovered after retry.",
            ),
        )
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config(max_retries=1))
        result = agent.diagnose(
            {"recovery_case_id": "case_10b", "scenario_type": "PAYMENT_FAILURE"}
        )
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.AI.value)
        self.assertEqual(llm.call_count, 2)


class TestDeterministicFallback(unittest.TestCase):
    """11. Deterministic fallback uses structured signals only, never
    invents information."""

    def test_fallback_never_invents_evidence(self):
        agent = RevenueDiagnosisAgent()  # no LLM
        result = agent.diagnose(
            {
                "recovery_case_id": "case_11",
                "scenario_type": "SUBSCRIPTION_FAILURE",
                "customer_segment": "enterprise",
            }
        )
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.FALLBACK.value)
        for e in result.evidence:
            # Every evidence signal must trace back to a real input field.
            self.assertNotIn("decline_code", e.signal)


class TestConfidenceBounds(unittest.TestCase):
    """12. Confidence must always be within [0, 1] across all modes."""

    def test_bounds_across_many_cases(self):
        agent = RevenueDiagnosisAgent()
        cases = [
            {"recovery_case_id": "c1", "scenario_type": "PAYMENT_FAILURE"},
            {
                "recovery_case_id": "c2",
                "scenario_type": "PAYMENT_FAILURE",
                "decline_code": "INSUFFICIENT_FUNDS",
            },
            {
                "recovery_case_id": "c3",
                "scenario_type": "PAYMENT_FAILURE",
                "decline_code": "GARBAGE_CODE_XYZ",
            },
            {
                "recovery_case_id": "c4",
                "scenario_type": "OVERDUE_RECEIVABLE",
                "receivable_info": {"days_overdue": 3},
            },
        ]
        for raw in cases:
            result = agent.diagnose(raw)
            self.assertGreaterEqual(result.confidence, 0.0)
            self.assertLessEqual(result.confidence, 1.0)

    def test_conflict_penalty_never_pushes_below_zero(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "c5",
                "scenario_type": "PAYMENT_FAILURE",
                "decline_code": "TEMPORARY_PROCESSING_ERROR",
                "failed_payment_count": 999,
            }
        )
        self.assertGreaterEqual(result.confidence, 0.0)


class TestHallucinationPrevention(unittest.TestCase):
    """13. The agent must never invent facts not present in the input."""

    def test_no_customer_history_invented(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "case_13",
                "scenario_type": "PAYMENT_FAILURE",
                "decline_code": "INSUFFICIENT_FUNDS",
            }
        )
        # No successful/failed payment counts were supplied -> must not
        # appear as evidence signals.
        signal_names = [e.signal for e in result.evidence]
        self.assertNotIn("payment_history", signal_names)
        self.assertNotIn("successful_payment_count", signal_names)

    def test_unknown_when_no_evidence_present(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {"recovery_case_id": "case_13b", "scenario_type": "OVERDUE_RECEIVABLE"}
        )
        self.assertTrue(result.root_cause.startswith("UNKNOWN_"))
        self.assertEqual(result.evidence, [])

    def test_llm_cannot_smuggle_extra_output_fields(self):
        # parse_llm_payload only extracts the defined shape; extra keys in
        # the raw payload must be dropped, never surfaced.
        llm = MockDiagnosisModel(
            mode="success",
            response_fn=lambda ctx: LLMDiagnosisResponse(
                root_cause="UNKNOWN_PAYMENT_FAILURE",
                confidence=0.3,
                diagnosis="test",
                raw_provider_payload={"recommended_action": "REFUND_NOW"},
            ),
        )
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config())
        result = agent.diagnose(
            {"recovery_case_id": "case_13c", "scenario_type": "PAYMENT_FAILURE"}
        )
        result_dict = result.to_dict()
        self.assertNotIn("recommended_action", result_dict)
        self.assertEqual(
            set(result_dict.keys()),
            {
                "schema_version",
                "recovery_case_id",
                "scenario_type",
                "root_cause",
                "confidence",
                "diagnosis",
                "evidence",
                "uncertainties",
                "diagnosis_mode",
            },
        )


class TestUnsupportedScenario(unittest.TestCase):
    """14. Unsupported scenario_type is rejected at validation time."""

    def test_unsupported_scenario_raises(self):
        agent = RevenueDiagnosisAgent()
        with self.assertRaises(InputValidationError) as ctx:
            agent.diagnose(
                {"recovery_case_id": "case_14", "scenario_type": "REFUND_REQUEST"}
            )
        self.assertEqual(ctx.exception.error_code, "INVALID_INPUT")
        self.assertEqual(ctx.exception.field, "scenario_type")

    def test_missing_scenario_type_raises(self):
        agent = RevenueDiagnosisAgent()
        with self.assertRaises(InputValidationError):
            agent.diagnose({"recovery_case_id": "case_14b"})

    def test_missing_case_id_raises(self):
        agent = RevenueDiagnosisAgent()
        with self.assertRaises(InputValidationError):
            agent.diagnose({"scenario_type": "PAYMENT_FAILURE"})

    def test_negative_amount_raises(self):
        agent = RevenueDiagnosisAgent()
        with self.assertRaises(InputValidationError):
            agent.diagnose(
                {
                    "recovery_case_id": "case_14c",
                    "scenario_type": "PAYMENT_FAILURE",
                    "amount_at_risk": -50,
                }
            )

    def test_invalid_currency_raises(self):
        agent = RevenueDiagnosisAgent()
        with self.assertRaises(InputValidationError):
            agent.diagnose(
                {
                    "recovery_case_id": "case_14d",
                    "scenario_type": "PAYMENT_FAILURE",
                    "currency": "dollars",
                }
            )

    def test_negative_payment_counts_raise(self):
        agent = RevenueDiagnosisAgent()
        with self.assertRaises(InputValidationError):
            agent.diagnose(
                {
                    "recovery_case_id": "case_14e",
                    "scenario_type": "PAYMENT_FAILURE",
                    "failed_payment_count": -1,
                }
            )

    def test_malformed_decline_code_raises(self):
        agent = RevenueDiagnosisAgent()
        with self.assertRaises(InputValidationError):
            agent.diagnose(
                {
                    "recovery_case_id": "case_14f",
                    "scenario_type": "PAYMENT_FAILURE",
                    "decline_code": "not a valid code!!",
                }
            )

    def test_non_dict_input_raises(self):
        agent = RevenueDiagnosisAgent()
        with self.assertRaises(InputValidationError):
            agent.diagnose("not a dict")


class TestStructuredOutputValidation(unittest.TestCase):
    """15. Structured output validation catches contract violations."""

    def test_valid_result_passes(self):
        result = DiagnosisResult(
            schema_version="1.0",
            recovery_case_id="ok",
            scenario_type="PAYMENT_FAILURE",
            root_cause="INSUFFICIENT_FUNDS",
            confidence=0.9,
            diagnosis="fine",
            evidence=[Evidence(signal="decline_code", relevance="matches")],
            uncertainties=[],
            diagnosis_mode="RULE",
        )
        validate_output(result)  # should not raise

    def test_invalid_root_cause_for_scenario_rejected(self):
        result = DiagnosisResult(
            schema_version="1.0",
            recovery_case_id="bad",
            scenario_type="CHECKOUT_ABANDONMENT",
            root_cause="INSUFFICIENT_FUNDS",  # not in checkout taxonomy
            confidence=0.9,
            diagnosis="fine",
            diagnosis_mode="RULE",
        )
        with self.assertRaises(OutputValidationError):
            validate_output(result)

    def test_confidence_out_of_range_rejected(self):
        result = DiagnosisResult(
            schema_version="1.0",
            recovery_case_id="bad2",
            scenario_type="PAYMENT_FAILURE",
            root_cause="UNKNOWN_PAYMENT_FAILURE",
            confidence=1.2,
            diagnosis="fine",
            diagnosis_mode="RULE",
        )
        with self.assertRaises(OutputValidationError):
            validate_output(result)

    def test_invalid_diagnosis_mode_rejected(self):
        result = DiagnosisResult(
            schema_version="1.0",
            recovery_case_id="bad3",
            scenario_type="PAYMENT_FAILURE",
            root_cause="UNKNOWN_PAYMENT_FAILURE",
            confidence=0.1,
            diagnosis="fine",
            diagnosis_mode="EXECUTE_REFUND",
        )
        with self.assertRaises(OutputValidationError):
            validate_output(result)

    def test_empty_diagnosis_rejected(self):
        result = DiagnosisResult(
            schema_version="1.0",
            recovery_case_id="bad4",
            scenario_type="PAYMENT_FAILURE",
            root_cause="UNKNOWN_PAYMENT_FAILURE",
            confidence=0.1,
            diagnosis="   ",
            diagnosis_mode="FALLBACK",
        )
        with self.assertRaises(OutputValidationError):
            validate_output(result)


class TestAsyncInterface(unittest.TestCase):
    """The async entry point must produce an identical contract."""

    def test_diagnose_async_matches_sync_shape(self):
        agent = RevenueDiagnosisAgent()

        async def run():
            return await agent.diagnose_async(
                {
                    "recovery_case_id": "case_async",
                    "scenario_type": "PAYMENT_FAILURE",
                    "decline_code": "INSUFFICIENT_FUNDS",
                }
            )

        result = asyncio.run(run())
        self.assertEqual(result.root_cause, "INSUFFICIENT_FUNDS")
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.RULE.value)

    def test_async_llm_timeout_falls_back(self):
        llm = MockDiagnosisModel(mode="timeout")
        agent = RevenueDiagnosisAgent(llm=llm, config=fast_config())

        async def run():
            return await agent.diagnose_async(
                {"recovery_case_id": "case_async2", "scenario_type": "PAYMENT_FAILURE"}
            )

        result = asyncio.run(run())
        self.assertEqual(result.diagnosis_mode, DiagnosisMode.FALLBACK.value)


class TestSafetyBoundary(unittest.TestCase):
    """The agent must never produce recovery/compliance/execution fields."""

    def test_output_contains_only_diagnosis_fields(self):
        agent = RevenueDiagnosisAgent()
        result = agent.diagnose(
            {
                "recovery_case_id": "case_safety",
                "scenario_type": "PAYMENT_FAILURE",
                "decline_code": "INSUFFICIENT_FUNDS",
            }
        )
        forbidden = {
            "recovery_action",
            "action",
            "compliance_approval",
            "recovery_rights",
            "recovery_score",
            "execution_command",
        }
        self.assertTrue(forbidden.isdisjoint(result.to_dict().keys()))


if __name__ == "__main__":
    unittest.main()
