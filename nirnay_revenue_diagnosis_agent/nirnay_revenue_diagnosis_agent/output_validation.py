"""
Final validation of a candidate DiagnosisResult against the strict output
contract (section 6 / 2B), run as the last pipeline stage ("Validation").
"""
from __future__ import annotations

from .enums import DiagnosisMode, ScenarioType, is_valid_root_cause
from .exceptions import OutputValidationError
from .models import DiagnosisResult


def validate_output(result: DiagnosisResult) -> DiagnosisResult:
    if not result.recovery_case_id:
        raise OutputValidationError("recovery_case_id is missing.", field="recovery_case_id")

    try:
        scenario_enum = ScenarioType(result.scenario_type)
    except ValueError:
        raise OutputValidationError(
            "scenario_type is not a supported scenario.", field="scenario_type"
        )

    if not is_valid_root_cause(scenario_enum, result.root_cause):
        raise OutputValidationError(
            f"root_cause '{result.root_cause}' is not part of the controlled "
            f"taxonomy for scenario '{result.scenario_type}'.",
            field="root_cause",
        )

    if not isinstance(result.confidence, (int, float)) or isinstance(result.confidence, bool):
        raise OutputValidationError("confidence must be numeric.", field="confidence")
    if not (0.0 <= float(result.confidence) <= 1.0):
        raise OutputValidationError(
            "confidence must be between 0 and 1.", field="confidence"
        )

    if not result.diagnosis or not result.diagnosis.strip():
        raise OutputValidationError("diagnosis must be a non-empty string.", field="diagnosis")

    try:
        DiagnosisMode(result.diagnosis_mode)
    except ValueError:
        raise OutputValidationError(
            "diagnosis_mode must be one of RULE, AI, FALLBACK.", field="diagnosis_mode"
        )

    for e in result.evidence:
        if not e.signal or not e.relevance:
            raise OutputValidationError(
                "Every evidence item requires a non-empty signal and relevance.",
                field="evidence",
            )

    return result
