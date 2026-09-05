"""
Validation layer.

Two distinct kinds of validation happen here, matching the spec:

1. Structural / input validation (section 2B): types, ranges, allowed
   enums. Failure => InputValidationError. This never tries to "repair"
   bad data.

2. Decision-lock consistency validation (section 4): confirms the
   already-approved decision is internally coherent (e.g. a BLOCKED
   compliance result cannot pair with an "active recovery" action).
   Failure => DecisionConsistencyError.

Neither validator invents or infers missing values.
"""

from typing import Optional

from .enums import (
    CommunicationPurpose,
    SelectedAction,
    Tone,
    TERMINAL_NO_ACTION_STATES,
    SUPPORTED_SCENARIO_TYPES,
)
from .exceptions import InputValidationError, DecisionConsistencyError
from .models import RecoveryCaseInput


def validate_input(case: RecoveryCaseInput) -> None:
    """Raises InputValidationError on the first structural problem found."""

    # --- required identity fields -------------------------------------------------
    if not case.recovery_case_id or not isinstance(case.recovery_case_id, str):
        raise InputValidationError(
            "recovery_case_id is required and must be a non-empty string.",
            field="recovery_case_id",
        )

    if not case.scenario_type or not isinstance(case.scenario_type, str):
        raise InputValidationError(
            "scenario_type is required and must be a string.",
            field="scenario_type",
        )
    if case.scenario_type not in SUPPORTED_SCENARIO_TYPES:
        raise InputValidationError(
            "Unsupported scenario_type.", field="scenario_type"
        )

    # --- amount_at_risk -------------------------------------------------------------
    if case.amount_at_risk is not None:
        if isinstance(case.amount_at_risk, bool) or not isinstance(
            case.amount_at_risk, (int, float)
        ):
            raise InputValidationError(
                "amount_at_risk must be numeric.", field="amount_at_risk"
            )
        if case.amount_at_risk < 0:
            raise InputValidationError(
                "amount_at_risk cannot be negative.", field="amount_at_risk"
            )

    if case.currency is not None:
        if not isinstance(case.currency, str) or not (2 <= len(case.currency) <= 6):
            raise InputValidationError(
                "currency must be a short currency code string (e.g. INR, USD).",
                field="currency",
            )

    # --- diagnosis_confidence --------------------------------------------------------
    if case.diagnosis_confidence is not None:
        if not isinstance(case.diagnosis_confidence, (int, float)) or isinstance(
            case.diagnosis_confidence, bool
        ):
            raise InputValidationError(
                "diagnosis_confidence must be numeric.",
                field="diagnosis_confidence",
            )
        if not (0.0 <= case.diagnosis_confidence <= 1.0):
            raise InputValidationError(
                "diagnosis_confidence must be between 0.0 and 1.0.",
                field="diagnosis_confidence",
            )

    # --- recovery_score ---------------------------------------------------------------
    if case.recovery_score is not None:
        if not isinstance(case.recovery_score, (int, float)) or isinstance(
            case.recovery_score, bool
        ):
            raise InputValidationError(
                "recovery_score must be numeric.", field="recovery_score"
            )

    # --- payment-count style fields, if present in extras (spec 2B example) -------
    for key in ("successful_payment_count", "failed_payment_count", "retry_count"):
        val = case.extra.get(key)
        if val is not None:
            if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                raise InputValidationError(
                    f"{key} must be a non-negative integer.", field=key
                )

    # --- decline codes, if present -----------------------------------------------------
    decline_codes = case.extra.get("decline_codes")
    if decline_codes is not None:
        if not isinstance(decline_codes, list) or not all(
            isinstance(c, str) and c.strip() for c in decline_codes
        ):
            raise InputValidationError(
                "decline_codes must be a list of non-empty strings.",
                field="decline_codes",
            )

    # --- selected_action ------------------------------------------------------------------
    if not case.selected_action or not isinstance(case.selected_action, str):
        raise InputValidationError(
            "selected_action is required and must be a string.",
            field="selected_action",
        )
    if case.selected_action not in SelectedAction.values():
        raise InputValidationError(
            "selected_action is not a recognized action. The agent cannot "
            "invent or reinterpret an unrecognized decision.",
            field="selected_action",
        )

    # --- compliance_result / recovery_rights must exist (may be empty dict, but present)
    if case.compliance_result is None:
        raise InputValidationError(
            "compliance_result is required.", field="compliance_result"
        )
    if not isinstance(case.compliance_result, dict):
        raise InputValidationError(
            "compliance_result must be an object.", field="compliance_result"
        )

    if case.recovery_rights is None:
        raise InputValidationError(
            "recovery_rights is required.", field="recovery_rights"
        )
    if not isinstance(case.recovery_rights, dict):
        raise InputValidationError(
            "recovery_rights must be an object.", field="recovery_rights"
        )

    # --- communication_purpose --------------------------------------------------------
    if (
        not case.communication_purpose
        or case.communication_purpose not in CommunicationPurpose.values()
    ):
        raise InputValidationError(
            "communication_purpose is required and must be one of "
            f"{sorted(CommunicationPurpose.values())}.",
            field="communication_purpose",
        )

    # --- requested_tone -----------------------------------------------------------------
    if case.requested_tone and case.requested_tone not in Tone.values():
        raise InputValidationError(
            f"requested_tone must be one of {sorted(Tone.values())}.",
            field="requested_tone",
        )

    # --- recovery_outcome shape, if present ---------------------------------------------
    if case.recovery_outcome is not None:
        if not isinstance(case.recovery_outcome, dict):
            raise InputValidationError(
                "recovery_outcome must be an object.", field="recovery_outcome"
            )
        status = case.recovery_outcome.get("status")
        if status is not None and status not in (
            "SUCCESS",
            "FAILED",
            "PENDING",
            "UNKNOWN",
        ):
            raise InputValidationError(
                "recovery_outcome.status must be one of SUCCESS, FAILED, "
                "PENDING, UNKNOWN.",
                field="recovery_outcome.status",
            )


def validate_decision_lock(case: RecoveryCaseInput) -> None:
    """Cross-field consistency checks. The agent does not re-derive the
    decision -- it only refuses to communicate a self-contradictory one."""

    selected_action = SelectedAction(case.selected_action)
    compliance = case.compliance_result or {}
    rights = case.recovery_rights or {}

    compliance_status = compliance.get("status")
    rights_allowed = rights.get("allowed")

    # Rule: if compliance explicitly blocked the case, selected_action must
    # be a terminal / no-action state.
    if compliance_status == "BLOCKED" and selected_action not in TERMINAL_NO_ACTION_STATES:
        raise DecisionConsistencyError(
            "compliance_result is BLOCKED but selected_action implies an "
            "active recovery action. Refusing to generate communication "
            "for a self-contradictory decision.",
            field="selected_action",
            details={
                "compliance_status": compliance_status,
                "selected_action": selected_action.value,
            },
        )

    # Rule: if recovery_rights explicitly say recovery is not allowed,
    # selected_action must be a terminal / no-action state.
    if rights_allowed is False and selected_action not in TERMINAL_NO_ACTION_STATES:
        raise DecisionConsistencyError(
            "recovery_rights.allowed is False but selected_action implies "
            "an active recovery action.",
            field="selected_action",
            details={"selected_action": selected_action.value},
        )

    # Rule: BLOCKED action must be paired with a non-approved compliance
    # result -- an approved compliance result should not produce a BLOCKED
    # communication (that would misrepresent compliance's own finding).
    if selected_action == SelectedAction.BLOCKED and compliance_status == "APPROVED":
        raise DecisionConsistencyError(
            "selected_action is BLOCKED but compliance_result is APPROVED. "
            "Decision inputs are inconsistent.",
            field="compliance_result",
        )

    # Rule: recovery_outcome claiming SUCCESS is only coherent for actions
    # that represent an actual attempted transaction (RETRY) or a closed
    # case; it can never coexist with BLOCKED.
    if case.recovery_outcome:
        outcome_status = case.recovery_outcome.get("status")
        if outcome_status == "SUCCESS" and selected_action == SelectedAction.BLOCKED:
            raise DecisionConsistencyError(
                "recovery_outcome reports SUCCESS but selected_action is "
                "BLOCKED. Inputs are inconsistent.",
                field="recovery_outcome",
            )


def require_context(case: RecoveryCaseInput, required_fields: list) -> Optional[str]:
    """Returns the name of the first missing required field, or None.
    Used to raise IncompleteContextError without inventing facts."""

    for f in required_fields:
        value = getattr(case, f, None)
        if value is None or value == "":
            return f
    return None
