"""
Data models.

Plain dataclasses are used (no external schema-validation dependency
required) so the agent has zero mandatory third-party dependencies.
`RecoveryCaseInput.from_dict` performs structural coercion; deeper
semantic validation lives in `validation.py`.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from .enums import CommunicationPurpose, SelectedAction, Tone


@dataclass
class RecoveryCaseInput:
    # --- identity / case context -------------------------------------------------
    recovery_case_id: str
    scenario_type: str
    customer_segment: Optional[str] = None
    amount_at_risk: Optional[float] = None
    currency: Optional[str] = "INR"

    # --- upstream diagnosis (already computed elsewhere) -------------------------
    diagnosis: Optional[str] = None
    diagnosis_confidence: Optional[float] = None

    # --- upstream governance (already computed elsewhere, authoritative) --------
    recovery_rights: Optional[dict] = None
    compliance_result: Optional[dict] = None
    allowed_actions: Optional[list] = field(default_factory=list)
    selected_action: str = None
    recovery_score: Optional[float] = None
    decision_mode: Optional[str] = None
    decision_rationale: Optional[str] = None
    recovery_outcome: Optional[dict] = None

    # --- communication request ----------------------------------------------------
    requested_language: str = "en"
    requested_tone: str = Tone.PROFESSIONAL.value
    communication_purpose: str = None

    # --- optional raw passthrough for anything the caller supplied that this
    # schema does not explicitly model (never used to invent facts) -------------
    extra: dict = field(default_factory=dict)

    @staticmethod
    def from_dict(payload: dict) -> "RecoveryCaseInput":
        if not isinstance(payload, dict):
            from .exceptions import InputValidationError

            raise InputValidationError(
                "Input payload must be a JSON object.", field="__root__"
            )

        known_fields = {f for f in RecoveryCaseInput.__dataclass_fields__}
        kwargs = {k: v for k, v in payload.items() if k in known_fields}
        extra = {k: v for k, v in payload.items() if k not in known_fields}
        kwargs["extra"] = extra
        return RecoveryCaseInput(**kwargs)

    def to_dict(self) -> dict:
        return {
            "recovery_case_id": self.recovery_case_id,
            "scenario_type": self.scenario_type,
            "customer_segment": self.customer_segment,
            "amount_at_risk": self.amount_at_risk,
            "currency": self.currency,
            "diagnosis": self.diagnosis,
            "diagnosis_confidence": self.diagnosis_confidence,
            "recovery_rights": self.recovery_rights,
            "compliance_result": self.compliance_result,
            "allowed_actions": self.allowed_actions,
            "selected_action": self.selected_action,
            "recovery_score": self.recovery_score,
            "decision_mode": self.decision_mode,
            "decision_rationale": self.decision_rationale,
            "recovery_outcome": self.recovery_outcome,
            "requested_language": self.requested_language,
            "requested_tone": self.requested_tone,
            "communication_purpose": self.communication_purpose,
        }


@dataclass
class CommunicationResult:
    """Envelope returned by the agent for a successful generation.
    The `payload` dict shape depends on `type` per the spec's Output
    Types section (3 distinct shapes)."""

    type: str
    payload: dict
    fallback_used: bool = False
    language_fallback: bool = False
    request_id: str = None

    def to_dict(self) -> dict:
        out = dict(self.payload)
        out["type"] = self.type
        out["_meta"] = {
            "request_id": self.request_id,
            "fallback_used": self.fallback_used,
            "language_fallback": self.language_fallback,
        }
        return out
