"""
RevenueDiagnosisAgent -- the public programmatic interface (section 2A).

    class RevenueDiagnosisAgent:
        diagnose(case: RecoveryCaseInput) -> DiagnosisResult

This module wires together the full pipeline described in section 4:

    Input normalization
        -> Signal extraction
        -> Scenario-specific analysis
        -> Root-cause classification
        -> Confidence estimation
        -> Evidence extraction
        -> Structured diagnosis
        -> Validation

and implements the LLM-fallback flow from section 13 plus the
timeout/retry policy from section 14. It answers exactly one question,
"why is this revenue at risk", and never produces a recovery action,
compliance approval, Recovery Rights decision, RecoveryScore, or
execution command (section 11).
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional, Union

from . import confidence as conf
from .combine import combine_rule_and_llm
from .config import AgentConfig
from .enums import DiagnosisMode, UNKNOWN_ROOT_CAUSE_BY_SCENARIO, ScenarioType
from .exceptions import (
    InputValidationError,
    LLMMalformedResponseError,
    LLMProviderError,
    LLMTimeoutError,
    OutputValidationError,
)
from .llm.base import DiagnosisModel, LLMDiagnosisResponse
from .llm.parsing import parse_llm_payload
from .llm.prompting import build_prompt_context
from .models import DiagnosisResult, RecoveryCaseInput, SCHEMA_VERSION
from .narrative import generate_diagnosis_text
from .normalization import normalize
from .output_validation import validate_output
from .rules import RuleOutcome, run_rule_engine
from .signals import extract_signals
from .telemetry import TelemetryRecorder
from .validation import validate_input

CaseLike = Union[RecoveryCaseInput, Dict[str, Any]]


class RevenueDiagnosisAgent:
    """The Nirnay Revenue Diagnosis Agent.

    Stateless and safe to reuse/share across requests. Accepts an
    optional `llm` (any `DiagnosisModel` implementation) used only for
    ambiguous cases where structured signals alone are insufficient; the
    agent works correctly with `llm=None` (rule-engine-only operation) and
    degrades gracefully whenever the LLM is unavailable or fails.
    """

    def __init__(
        self,
        llm: Optional[DiagnosisModel] = None,
        config: Optional[AgentConfig] = None,
    ):
        self.llm = llm
        self.config = config or AgentConfig()

    # -- Public interface -------------------------------------------------

    def diagnose(self, case: CaseLike) -> DiagnosisResult:
        """Synchronous diagnosis entry point.

        Raises `InputValidationError` on invalid input. Never raises on
        LLM failure -- that path is handled internally via the
        deterministic fallback.
        """
        validated = self._validate(case)
        telemetry = TelemetryRecorder(
            recovery_case_id=validated.recovery_case_id,
            scenario_type=validated.scenario_type,
            provider=getattr(self.llm, "name", None) if self.llm else None,
        )

        normalized = normalize(validated)
        signals = extract_signals(normalized)
        rule_outcome = run_rule_engine(normalized)

        if self._should_use_rule_only(rule_outcome):
            result = self._finalize_rule_result(normalized, rule_outcome, DiagnosisMode.RULE)
            telemetry.finish(diagnosis_mode=result.diagnosis_mode, validation_status="OK")
            return result

        if self.llm is None:
            result = self._finalize_rule_result(
                normalized, rule_outcome, DiagnosisMode.FALLBACK
            )
            telemetry.finish(diagnosis_mode=result.diagnosis_mode, validation_status="OK")
            return result

        llm_response, retries, failure_reason = self._call_llm_with_retry(
            normalized, signals, rule_outcome, telemetry
        )

        if llm_response is None:
            result = self._finalize_rule_result(
                normalized, rule_outcome, DiagnosisMode.FALLBACK
            )
            telemetry.finish(
                diagnosis_mode=result.diagnosis_mode,
                validation_status="OK",
                failure_reason=failure_reason,
            )
            return result

        result = self._finalize_ai_result(normalized, rule_outcome, llm_response)
        telemetry.finish(diagnosis_mode=result.diagnosis_mode, validation_status="OK")
        return result

    async def diagnose_async(self, case: CaseLike) -> DiagnosisResult:
        """Async diagnosis entry point. Identical output contract to
        `diagnose`; only the LLM call (if any) is awaited."""
        validated = self._validate(case)
        telemetry = TelemetryRecorder(
            recovery_case_id=validated.recovery_case_id,
            scenario_type=validated.scenario_type,
            provider=getattr(self.llm, "name", None) if self.llm else None,
        )

        normalized = normalize(validated)
        signals = extract_signals(normalized)
        rule_outcome = run_rule_engine(normalized)

        if self._should_use_rule_only(rule_outcome):
            result = self._finalize_rule_result(normalized, rule_outcome, DiagnosisMode.RULE)
            telemetry.finish(diagnosis_mode=result.diagnosis_mode, validation_status="OK")
            return result

        if self.llm is None:
            result = self._finalize_rule_result(
                normalized, rule_outcome, DiagnosisMode.FALLBACK
            )
            telemetry.finish(diagnosis_mode=result.diagnosis_mode, validation_status="OK")
            return result

        llm_response, retries, failure_reason = await self._call_llm_with_retry_async(
            normalized, signals, rule_outcome, telemetry
        )

        if llm_response is None:
            result = self._finalize_rule_result(
                normalized, rule_outcome, DiagnosisMode.FALLBACK
            )
            telemetry.finish(
                diagnosis_mode=result.diagnosis_mode,
                validation_status="OK",
                failure_reason=failure_reason,
            )
            return result

        result = self._finalize_ai_result(normalized, rule_outcome, llm_response)
        telemetry.finish(diagnosis_mode=result.diagnosis_mode, validation_status="OK")
        return result

    # -- Internal helpers ---------------------------------------------------

    def _validate(self, case: CaseLike) -> RecoveryCaseInput:
        if isinstance(case, RecoveryCaseInput):
            # Still validate, in case the caller hand-built an invalid
            # instance -- round-trip through the dict validator.
            raw = {k: getattr(case, k) for k in RecoveryCaseInput.field_names()}
            return validate_input(raw)
        return validate_input(case)

    def _should_use_rule_only(self, rule_outcome: RuleOutcome) -> bool:
        return (
            rule_outcome.decisive
            and rule_outcome.confidence >= self.config.rule_decisive_confidence_threshold
            and not self.config.always_consult_llm
        )

    def _finalize_rule_result(
        self, normalized, rule_outcome: RuleOutcome, mode: DiagnosisMode
    ) -> DiagnosisResult:
        uncertainties = list(rule_outcome.uncertainties)
        confidence = rule_outcome.confidence
        if mode == DiagnosisMode.FALLBACK and self.llm is not None:
            uncertainties.append(
                "LLM diagnosis was unavailable for this request; a deterministic "
                "fallback based only on structured signals was used."
            )
            confidence = conf.lower_for_missing_data(confidence, penalty=0.05)
        diagnosis_text = generate_diagnosis_text(
            normalized.scenario_type, rule_outcome.root_cause, rule_outcome.evidence, uncertainties
        )
        if not rule_outcome.evidence and not uncertainties:
            uncertainties.append("Insufficient evidence.")
        result = DiagnosisResult(
            schema_version=SCHEMA_VERSION,
            recovery_case_id=normalized.recovery_case_id,
            scenario_type=normalized.scenario_type,
            root_cause=rule_outcome.root_cause,
            confidence=conf.clamp(confidence),
            diagnosis=diagnosis_text,
            evidence=list(rule_outcome.evidence),
            uncertainties=uncertainties,
            diagnosis_mode=mode.value,
        )
        return validate_output(result)

    def _finalize_ai_result(
        self, normalized, rule_outcome: RuleOutcome, llm_response: LLMDiagnosisResponse
    ) -> DiagnosisResult:
        combined = combine_rule_and_llm(
            normalized.scenario_type, rule_outcome, llm_response
        )
        result = DiagnosisResult(
            schema_version=SCHEMA_VERSION,
            recovery_case_id=normalized.recovery_case_id,
            scenario_type=normalized.scenario_type,
            root_cause=combined.root_cause,
            confidence=combined.confidence,
            diagnosis=combined.diagnosis,
            evidence=combined.evidence,
            uncertainties=combined.uncertainties,
            diagnosis_mode=DiagnosisMode.AI.value,
        )
        return validate_output(result)

    def _backoff_seconds(self, attempt: int) -> float:
        delay = self.config.base_backoff_seconds * (2 ** attempt)
        return min(delay, self.config.max_backoff_seconds)

    def _call_llm_with_retry(self, normalized, signals, rule_outcome, telemetry):
        prompt_context = build_prompt_context(normalized, signals, rule_outcome)
        max_attempts = 1 + self.config.max_retries
        last_failure_reason = None

        for attempt in range(max_attempts):
            try:
                raw = self.llm.generate_structured_diagnosis(
                    prompt_context, self.config.llm_timeout_seconds
                )
                payload = raw if isinstance(raw, dict) else _response_to_dict(raw)
                parsed = parse_llm_payload(payload, normalized.scenario_type)
                return parsed, attempt, None
            except (LLMTimeoutError, LLMProviderError, LLMMalformedResponseError) as exc:
                last_failure_reason = f"{type(exc).__name__}: {exc}"
                if attempt < max_attempts - 1:
                    telemetry.mark_retry()
                    time.sleep(self._backoff_seconds(attempt))
                continue

        return None, max_attempts - 1, last_failure_reason

    async def _call_llm_with_retry_async(self, normalized, signals, rule_outcome, telemetry):
        prompt_context = build_prompt_context(normalized, signals, rule_outcome)
        max_attempts = 1 + self.config.max_retries
        last_failure_reason = None

        for attempt in range(max_attempts):
            try:
                raw = await self.llm.generate_structured_diagnosis_async(
                    prompt_context, self.config.llm_timeout_seconds
                )
                payload = raw if isinstance(raw, dict) else _response_to_dict(raw)
                parsed = parse_llm_payload(payload, normalized.scenario_type)
                return parsed, attempt, None
            except (LLMTimeoutError, LLMProviderError, LLMMalformedResponseError) as exc:
                last_failure_reason = f"{type(exc).__name__}: {exc}"
                if attempt < max_attempts - 1:
                    telemetry.mark_retry()
                    await asyncio.sleep(self._backoff_seconds(attempt))
                continue

        return None, max_attempts - 1, last_failure_reason


def _response_to_dict(response: LLMDiagnosisResponse) -> Dict[str, Any]:
    return {
        "root_cause": response.root_cause,
        "confidence": response.confidence,
        "diagnosis": response.diagnosis,
        "evidence": response.evidence,
        "uncertainties": response.uncertainties,
    }
