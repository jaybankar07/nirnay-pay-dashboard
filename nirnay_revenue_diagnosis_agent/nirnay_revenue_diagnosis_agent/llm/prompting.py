"""
Builds the structured context payload passed into
`DiagnosisModel.generate_structured_diagnosis`.

This module never talks to a network -- it only assembles a plain dict
from already-normalized, already-validated data plus the allowed
taxonomy, so any provider adapter has exactly what it needs (and nothing
fabricated) to reason about ambiguous/unstructured signals.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..enums import ROOT_CAUSE_ENUM_BY_SCENARIO, ScenarioType
from ..models import Signal
from ..normalization import NormalizedCase
from ..rules import RuleOutcome

SYSTEM_INSTRUCTIONS = (
    "You are a revenue-risk diagnosis assistant. Given structured and "
    "unstructured signals about a payment recovery case, identify the most "
    "likely root cause STRICTLY from the provided allowed_root_causes list. "
    "Never invent facts not present in the signals. If the evidence is "
    "insufficient or ambiguous, choose the UNKNOWN_* category for this "
    "scenario and explain the uncertainty. Respond ONLY with a JSON object "
    "matching this shape: {\"root_cause\": str, \"confidence\": float "
    "between 0 and 1, \"diagnosis\": str, \"evidence\": "
    "[{\"signal\": str, \"relevance\": str}], \"uncertainties\": [str]}. "
    "Do not recommend or state any recovery action, compliance decision, or "
    "RecoveryScore -- you only explain the likely cause."
)


def _signals_to_payload(signals: List[Signal]) -> List[Dict[str, Any]]:
    return [
        {"name": s.name, "value": s.value, "source": s.source, "relevance": s.relevance}
        for s in signals
    ]


def build_prompt_context(
    normalized: NormalizedCase,
    signals: List[Signal],
    rule_outcome: RuleOutcome,
) -> Dict[str, Any]:
    scenario_enum = ScenarioType(normalized.scenario_type)
    allowed_root_causes = [rc.value for rc in ROOT_CAUSE_ENUM_BY_SCENARIO[scenario_enum]]

    return {
        "system_instructions": SYSTEM_INSTRUCTIONS,
        "recovery_case_id": normalized.recovery_case_id,
        "scenario_type": normalized.scenario_type,
        "allowed_root_causes": allowed_root_causes,
        "signals": _signals_to_payload(signals),
        "missing_fields": normalized.missing_fields,
        "rule_engine_preliminary": {
            "root_cause": rule_outcome.root_cause,
            "confidence": rule_outcome.confidence,
            "uncertainties": rule_outcome.uncertainties,
        },
    }
