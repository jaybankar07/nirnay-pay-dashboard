"""
NirnayCommunicationAgent -- the agent itself.

Pipeline for every call to `generate()`:

  1. Parse + structurally validate input (section 2B)          -> InputValidationError
  2. Decision-lock consistency check (section 4)                -> DecisionConsistencyError
  3. Confirm required context exists for the requested purpose  -> IncompleteContextError
  4. Build a minimal, fact-only GenerationRequest for the LLM
  5. Call the LLM (generate_explanation / generate_customer_message)
  6. Run the request through the deterministic safety layer
  7. If unsafe: retry once with correction notes
  8. If still unsafe (or the LLM failed/timed out): use a deterministic
     fallback template
  9. Emit structured telemetry
 10. Return a strictly-shaped CommunicationResult

The agent NEVER re-derives or overrides `selected_action`,
`compliance_result`, or `recovery_rights`. Those are treated as
immutable, authoritative facts from upstream systems.
"""

from typing import Optional, Union

from .enums import CommunicationPurpose, SelectedAction, SupportedLanguage
from .exceptions import (
    IncompleteContextError,
    NirnayAgentError,
)
from .llm.base import CommunicationModel, GenerationRequest, LLMProviderError, LLMTimeoutError
from .models import CommunicationResult, RecoveryCaseInput
from .safety import run_safety_checks
from .telemetry import Telemetry
from .validation import validate_decision_lock, validate_input
from . import templates


# Minimum fields required per communication purpose. The agent refuses
# to invent anything not present, so if these are missing it returns a
# structured INCOMPLETE_CONTEXT error instead of guessing.
_REQUIRED_FIELDS = {
    CommunicationPurpose.DECISION_EXPLANATION.value: [
        "selected_action",
        "decision_rationale",
    ],
    CommunicationPurpose.CUSTOMER_RECOVERY_MESSAGE.value: [
        "selected_action",
    ],
    CommunicationPurpose.MERCHANT_EXPLANATION.value: [
        "selected_action",
        "decision_rationale",
    ],
}


class NirnayCommunicationAgent:
    """Programmatic entry point.

    Example:
        agent = NirnayCommunicationAgent(llm=MockCommunicationModel())
        result = agent.generate(case_payload_dict)
    """

    def __init__(
        self,
        llm: CommunicationModel,
        telemetry: Optional[Telemetry] = None,
        provider_name: str = "unknown",
    ):
        self.llm = llm
        self.telemetry = telemetry or Telemetry()
        self.provider_name = provider_name

    # ------------------------------------------------------------------ public API
    def generate(self, case_input: Union[dict, RecoveryCaseInput]) -> dict:
        """Synchronous entry point. Returns a plain dict (JSON-serializable).

        Raises NirnayAgentError subclasses on invalid/inconsistent input
        (never returns a malformed or invented result).
        """

        case = (
            case_input
            if isinstance(case_input, RecoveryCaseInput)
            else RecoveryCaseInput.from_dict(case_input)
        )

        # 1. structural validation
        validate_input(case)

        # 2. decision-lock consistency
        validate_decision_lock(case)

        purpose = case.communication_purpose
        record = self.telemetry.start(
            recovery_case_id=case.recovery_case_id,
            generation_type=purpose,
            provider=self.provider_name,
        )

        try:
            # 3. required-context check (no hallucination rule)
            missing = _missing_required_field(case, purpose)
            if missing:
                self.telemetry.finish(
                    record,
                    validation_status="N/A",
                    fallback_used=False,
                    retry_count=0,
                    failure_reason=f"INCOMPLETE_CONTEXT:{missing}",
                )
                raise IncompleteContextError(
                    f"Required field '{missing}' is missing for "
                    f"communication_purpose={purpose}.",
                    field=missing,
                )

            if purpose == CommunicationPurpose.DECISION_EXPLANATION.value:
                result = self._generate_decision_explanation(case, record)
            elif purpose == CommunicationPurpose.CUSTOMER_RECOVERY_MESSAGE.value:
                result = self._generate_customer_message(case, record)
            elif purpose == CommunicationPurpose.MERCHANT_EXPLANATION.value:
                result = self._generate_merchant_explanation(case, record)
            else:  # unreachable given validate_input, kept defensive
                raise NirnayAgentError(
                    "Unsupported communication_purpose.",
                    field="communication_purpose",
                )

            result.request_id = record.request_id
            return result.to_dict()
        except NirnayAgentError:
            raise
        except Exception as e:  # noqa: BLE001 -- last-resort safety net
            self.telemetry.finish(
                record,
                validation_status="FAILED",
                fallback_used=True,
                retry_count=0,
                failure_reason=f"UNEXPECTED:{type(e).__name__}",
            )
            # Even on an unexpected internal error, the workflow must not
            # crash the caller (section 14: "LLM failure must never
            # prevent the core recovery workflow from completing").
            return self._safe_fallback_result(case, record).to_dict()

    # --------------------------------------------------------------- helpers: build request
    def _build_request(self, case: RecoveryCaseInput, correction_notes: str = None) -> GenerationRequest:
        language = case.requested_language or "en"
        language_fallback = language not in SupportedLanguage.values()
        effective_language = "en" if language_fallback else language

        return GenerationRequest(
            purpose=case.communication_purpose,
            selected_action=case.selected_action,
            scenario_type=case.scenario_type,
            customer_segment=case.customer_segment,
            amount_at_risk=case.amount_at_risk,
            currency=case.currency,
            diagnosis=case.diagnosis,
            diagnosis_confidence=case.diagnosis_confidence,
            decision_rationale=case.decision_rationale,
            compliance_status=(case.compliance_result or {}).get("status"),
            recovery_rights_allowed=(case.recovery_rights or {}).get("allowed"),
            recovery_outcome_status=(case.recovery_outcome or {}).get("status"),
            tone=case.requested_tone,
            language=effective_language,
            correction_notes=correction_notes,
        ), language_fallback

    # --------------------------------------------------------------- decision explanation
    def _generate_decision_explanation(self, case: RecoveryCaseInput, record) -> CommunicationResult:
        text_field = "reason"  # the field whose text we run safety checks on
        fallback_used = False
        retry_count = 0
        validation_status = "PASSED"
        failure_reason = None
        language_fallback = False
        raw = None

        for attempt in range(2):
            request, language_fallback = self._build_request(
                case, correction_notes=self._correction_notes(attempt)
            )
            try:
                raw = self.llm.generate_explanation(request)
                _assert_explanation_shape(raw)
            except (LLMTimeoutError, LLMProviderError, ValueError) as e:
                retry_count = attempt
                validation_status = "FAILED"
                failure_reason = f"LLM_ERROR:{type(e).__name__}"
                raw = None
                break

            combined_text = " ".join(
                [raw.get("summary", ""), raw.get("reason", ""), raw.get("business_context", "")]
                + list(raw.get("constraints", []) or [])
            )
            report = run_safety_checks(combined_text, case)
            if report.passed:
                validation_status = "PASSED"
                failure_reason = None
                break
            retry_count = attempt + 1
            validation_status = "FAILED"
            failure_reason = ",".join(report.violations)
            raw = None

        if raw is None:
            fallback_used = True
            selected_action = SelectedAction(case.selected_action)
            payload = {
                "summary": templates.fallback_decision_explanation(selected_action),
                "reason": case.decision_rationale or "No further detail available.",
                "business_context": (
                    f"compliance_status={((case.compliance_result or {}).get('status'))}"
                ),
                "constraints": (
                    ["No further automatic recovery action will occur."]
                    if selected_action in {SelectedAction.STOP, SelectedAction.BLOCKED}
                    else []
                ),
            }
        else:
            payload = {
                "summary": raw.get("summary", ""),
                "reason": raw.get("reason", ""),
                "business_context": raw.get("business_context", ""),
                "constraints": raw.get("constraints", []) or [],
            }

        self.telemetry.finish(
            record,
            validation_status=validation_status,
            fallback_used=fallback_used,
            retry_count=retry_count,
            failure_reason=failure_reason,
        )

        return CommunicationResult(
            type=CommunicationPurpose.DECISION_EXPLANATION.value,
            payload=payload,
            fallback_used=fallback_used,
            language_fallback=language_fallback,
        )

    # --------------------------------------------------------------- customer message
    def _generate_customer_message(self, case: RecoveryCaseInput, record) -> CommunicationResult:
        fallback_used = False
        retry_count = 0
        validation_status = "PASSED"
        failure_reason = None
        language_fallback = False
        message = None

        for attempt in range(2):
            request, language_fallback = self._build_request(
                case, correction_notes=self._correction_notes(attempt)
            )
            try:
                raw = self.llm.generate_customer_message(request)
                if not isinstance(raw, dict) or "message" not in raw:
                    raise ValueError("LLM output missing 'message' field.")
            except (LLMTimeoutError, LLMProviderError, ValueError) as e:
                retry_count = attempt
                validation_status = "FAILED"
                failure_reason = f"LLM_ERROR:{type(e).__name__}"
                message = None
                break

            candidate = raw["message"]
            report = run_safety_checks(candidate, case)
            if report.passed:
                message = candidate
                validation_status = "PASSED"
                failure_reason = None
                break
            retry_count = attempt + 1
            validation_status = "FAILED"
            failure_reason = ",".join(report.violations)
            message = None

        selected_action = SelectedAction(case.selected_action)
        if message is None:
            fallback_used = True
            message = templates.fallback_customer_message(selected_action)

        self.telemetry.finish(
            record,
            validation_status=validation_status,
            fallback_used=fallback_used,
            retry_count=retry_count,
            failure_reason=failure_reason,
        )

        payload = {
            "message": message,
            "tone": case.requested_tone,
            "language": "en" if language_fallback else (case.requested_language or "en"),
            "action_reference": selected_action.value,
        }

        return CommunicationResult(
            type=CommunicationPurpose.CUSTOMER_RECOVERY_MESSAGE.value,
            payload=payload,
            fallback_used=fallback_used,
            language_fallback=language_fallback,
        )

    # --------------------------------------------------------------- merchant explanation
    def _generate_merchant_explanation(self, case: RecoveryCaseInput, record) -> CommunicationResult:
        fallback_used = False
        retry_count = 0
        validation_status = "PASSED"
        failure_reason = None
        language_fallback = False
        raw = None

        for attempt in range(2):
            request, language_fallback = self._build_request(
                case, correction_notes=self._correction_notes(attempt)
            )
            try:
                raw = self.llm.generate_explanation(request)
                _assert_explanation_shape(raw)
            except (LLMTimeoutError, LLMProviderError, ValueError) as e:
                retry_count = attempt
                validation_status = "FAILED"
                failure_reason = f"LLM_ERROR:{type(e).__name__}"
                raw = None
                break

            combined_text = " ".join(
                [raw.get("summary", ""), raw.get("reason", ""), raw.get("business_context", "")]
            )
            report = run_safety_checks(combined_text, case)
            if report.passed:
                validation_status = "PASSED"
                failure_reason = None
                break
            retry_count = attempt + 1
            validation_status = "FAILED"
            failure_reason = ",".join(report.violations)
            raw = None

        selected_action = SelectedAction(case.selected_action)
        if raw is None:
            fallback_used = True
            payload = {
                "summary": templates.fallback_merchant_summary(selected_action),
                "why_this_action": case.decision_rationale or "Not available.",
                "expected_business_intent": (
                    "Preserve customer trust while following the approved "
                    "recovery workflow."
                ),
                "compliance_context": (
                    f"compliance_status="
                    f"{(case.compliance_result or {}).get('status')}"
                ),
            }
        else:
            payload = {
                "summary": raw.get("summary", ""),
                "why_this_action": raw.get("reason", ""),
                "expected_business_intent": raw.get("business_context", ""),
                "compliance_context": (
                    f"compliance_status="
                    f"{(case.compliance_result or {}).get('status')}"
                ),
            }

        self.telemetry.finish(
            record,
            validation_status=validation_status,
            fallback_used=fallback_used,
            retry_count=retry_count,
            failure_reason=failure_reason,
        )

        return CommunicationResult(
            type=CommunicationPurpose.MERCHANT_EXPLANATION.value,
            payload=payload,
            fallback_used=fallback_used,
            language_fallback=language_fallback,
        )

    # --------------------------------------------------------------- misc helpers
    @staticmethod
    def _correction_notes(attempt: int) -> Optional[str]:
        if attempt == 0:
            return None
        return (
            "Correction: the previous draft was rejected by the safety "
            "layer. Use only the supplied facts, reference the exact "
            "selected_action, avoid any claim of payment success/"
            "recovery unless recovery_outcome_status is SUCCESS, invent "
            "no amounts/dates/deadlines/penalties, and avoid urgent or "
            "threatening phrasing."
        )

    def _safe_fallback_result(self, case: RecoveryCaseInput, record) -> CommunicationResult:
        selected_action = SelectedAction(case.selected_action)
        purpose = case.communication_purpose
        if purpose == CommunicationPurpose.CUSTOMER_RECOVERY_MESSAGE.value:
            payload = {
                "message": templates.fallback_customer_message(selected_action),
                "tone": case.requested_tone,
                "language": "en",
                "action_reference": selected_action.value,
            }
        elif purpose == CommunicationPurpose.MERCHANT_EXPLANATION.value:
            payload = {
                "summary": templates.fallback_merchant_summary(selected_action),
                "why_this_action": case.decision_rationale or "Not available.",
                "expected_business_intent": "Follow the approved recovery workflow.",
                "compliance_context": f"compliance_status={(case.compliance_result or {}).get('status')}",
            }
        else:
            payload = {
                "summary": templates.fallback_decision_explanation(selected_action),
                "reason": case.decision_rationale or "Not available.",
                "business_context": f"compliance_status={(case.compliance_result or {}).get('status')}",
                "constraints": [],
            }
        return CommunicationResult(type=purpose, payload=payload, fallback_used=True, request_id=record.request_id)


def _missing_required_field(case: RecoveryCaseInput, purpose: str) -> Optional[str]:
    for f in _REQUIRED_FIELDS.get(purpose, []):
        if getattr(case, f, None) in (None, ""):
            return f
    return None


def _assert_explanation_shape(raw: dict) -> None:
    if not isinstance(raw, dict):
        raise ValueError("LLM explanation output must be a JSON object.")
    for key in ("summary", "reason", "business_context"):
        if key not in raw or not isinstance(raw[key], str):
            raise ValueError(f"LLM explanation output missing string field '{key}'.")
    if "constraints" in raw and not isinstance(raw["constraints"], list):
        raise ValueError("LLM explanation output field 'constraints' must be a list.")
