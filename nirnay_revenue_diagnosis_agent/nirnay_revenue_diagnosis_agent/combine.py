"""
Combines the deterministic rule-engine outcome with a validated LLM
response into a single reconciled result, applying the conflict
resolution policy from section 9:

    1. Prefer explicit structured transaction signals.
    2. Prefer verified historical data.
    3. Use customer/support text as contextual evidence.
    4. If conflict remains, lower confidence.
    5. Report the uncertainty.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from . import confidence as conf
from .enums import UNKNOWN_ROOT_CAUSE_BY_SCENARIO, ScenarioType
from .llm.base import LLMDiagnosisResponse
from .models import Evidence
from .rules import RuleOutcome


@dataclass
class CombinedResult:
    root_cause: str
    confidence: float
    diagnosis: str
    evidence: List[Evidence] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)


def combine_rule_and_llm(
    scenario_type: str,
    rule_outcome: RuleOutcome,
    llm_response: LLMDiagnosisResponse,
) -> CombinedResult:
    unknown = UNKNOWN_ROOT_CAUSE_BY_SCENARIO[ScenarioType(scenario_type)].value

    evidence: List[Evidence] = list(rule_outcome.evidence)
    for e in llm_response.evidence:
        evidence.append(Evidence(signal=e["signal"], relevance=e["relevance"]))

    uncertainties: List[str] = list(rule_outcome.uncertainties) + list(
        llm_response.uncertainties
    )

    rule_has_signal = rule_outcome.root_cause != unknown

    if rule_has_signal and llm_response.root_cause != rule_outcome.root_cause:
        # Conflict: structured-signal evidence disagrees with the LLM's
        # text-derived conclusion. Structured evidence wins (policy #1),
        # but we surface the disagreement and lower confidence (#4, #5).
        uncertainties.append(
            f"LLM proposed root_cause '{llm_response.root_cause}' which conflicts "
            f"with the structured-signal-derived root_cause "
            f"'{rule_outcome.root_cause}'; structured evidence was prioritized."
        )
        final_root_cause = rule_outcome.root_cause
        final_confidence = conf.lower_for_conflict(
            max(rule_outcome.confidence, llm_response.confidence)
        )
        diagnosis = (
            f"{llm_response.diagnosis} (Note: structured transaction/historical "
            f"evidence was prioritized over this interpretation due to a conflict.)"
        )
    elif rule_has_signal:
        # Agreement: structured signal and LLM interpretation align.
        # Treat this as strong multi-signal evidence.
        final_root_cause = rule_outcome.root_cause
        final_confidence = conf.clamp(
            max(rule_outcome.confidence, llm_response.confidence, conf.DEFAULT_STRONG_MULTI)
        )
        diagnosis = llm_response.diagnosis
    else:
        # No structured basis; defer to the LLM's text-derived conclusion,
        # but cap confidence since it rests on unstructured evidence only
        # (never let text alone reach the "explicit structured evidence"
        # band).
        final_root_cause = llm_response.root_cause
        final_confidence = min(llm_response.confidence, conf.STRONG_MULTI_SIGNAL[1])
        diagnosis = llm_response.diagnosis
        if llm_response.root_cause == unknown:
            uncertainties.append("Neither structured signals nor available text were sufficient.")

    return CombinedResult(
        root_cause=final_root_cause,
        confidence=conf.clamp(final_confidence),
        diagnosis=diagnosis,
        evidence=evidence,
        uncertainties=uncertainties,
    )
