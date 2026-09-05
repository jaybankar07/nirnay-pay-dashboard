"""
Parsing and validation of raw LLM provider output (section 12: "Validate
every LLM response.").

A provider adapter may hand back a plain dict (e.g. parsed JSON) instead
of an `LLMDiagnosisResponse`; this module is the single choke point that
turns that untrusted payload into a validated `LLMDiagnosisResponse`, or
raises `LLMMalformedResponseError` if it cannot.
"""
from __future__ import annotations

from typing import Any, Dict

from ..enums import ScenarioType, is_valid_root_cause
from ..exceptions import LLMMalformedResponseError
from .base import LLMDiagnosisResponse


def parse_llm_payload(
    payload: Dict[str, Any], scenario_type: str
) -> LLMDiagnosisResponse:
    if not isinstance(payload, dict):
        raise LLMMalformedResponseError("LLM payload must be an object.")

    root_cause = payload.get("root_cause")
    if not isinstance(root_cause, str) or not root_cause:
        raise LLMMalformedResponseError("LLM payload missing valid 'root_cause'.")

    try:
        scenario_enum = ScenarioType(scenario_type)
    except ValueError:
        raise LLMMalformedResponseError("LLM payload scenario_type is unsupported.")

    if not is_valid_root_cause(scenario_enum, root_cause):
        raise LLMMalformedResponseError(
            f"LLM returned root_cause '{root_cause}' outside the controlled "
            f"taxonomy for scenario '{scenario_type}'."
        )

    confidence = payload.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise LLMMalformedResponseError("LLM payload missing numeric 'confidence'.")
    confidence = float(confidence)
    if not (0.0 <= confidence <= 1.0):
        raise LLMMalformedResponseError("LLM payload 'confidence' out of range [0,1].")

    diagnosis = payload.get("diagnosis")
    if not isinstance(diagnosis, str) or not diagnosis.strip():
        raise LLMMalformedResponseError("LLM payload missing valid 'diagnosis'.")

    evidence_raw = payload.get("evidence", [])
    if not isinstance(evidence_raw, list):
        raise LLMMalformedResponseError("LLM payload 'evidence' must be a list.")
    evidence = []
    for item in evidence_raw:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("signal"), str)
            or not isinstance(item.get("relevance"), str)
        ):
            raise LLMMalformedResponseError(
                "LLM payload 'evidence' items must have string 'signal' and 'relevance'."
            )
        evidence.append({"signal": item["signal"], "relevance": item["relevance"]})

    uncertainties_raw = payload.get("uncertainties", [])
    if not isinstance(uncertainties_raw, list) or not all(
        isinstance(u, str) for u in uncertainties_raw
    ):
        raise LLMMalformedResponseError(
            "LLM payload 'uncertainties' must be a list of strings."
        )

    return LLMDiagnosisResponse(
        root_cause=root_cause,
        confidence=confidence,
        diagnosis=diagnosis.strip(),
        evidence=evidence,
        uncertainties=list(uncertainties_raw),
        raw_provider_payload=payload,
    )
