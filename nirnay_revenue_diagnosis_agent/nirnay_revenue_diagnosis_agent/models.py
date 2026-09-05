"""
Core data models for the Nirnay Revenue Diagnosis Agent.

Deliberately implemented with the standard library (dataclasses) rather
than a third-party validation library so the agent has zero external
runtime dependencies and can be dropped into any host application.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional

from .enums import DiagnosisMode, ScenarioType

SCHEMA_VERSION = "1.0"

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


@dataclass
class RecoveryCaseInput:
    """Structured recovery-case context supplied by the caller.

    Every field is optional except `recovery_case_id` and `scenario_type`,
    which are the minimum information required to produce any diagnosis at
    all (we need to know *which case* this is and *which scenario*
    taxonomy applies). All other fields degrade gracefully to `None` /
    empty and the agent reasons only over whatever evidence is present.
    """

    recovery_case_id: str
    scenario_type: str

    amount_at_risk: Optional[float] = None
    currency: Optional[str] = None

    customer_segment: Optional[str] = None
    customer_tenure: Optional[Any] = None
    customer_lifetime_value: Optional[float] = None

    successful_payment_count: Optional[int] = None
    failed_payment_count: Optional[int] = None

    # Free-form structured transaction/payment signals, e.g.
    # {"processor": "stripe", "network_result": "do_not_honor", ...}
    payment_signals: Optional[Dict[str, Any]] = None

    decline_code: Optional[str] = None
    failure_reason: Optional[str] = None

    subscription_info: Optional[Dict[str, Any]] = None
    checkout_info: Optional[Dict[str, Any]] = None
    receivable_info: Optional[Dict[str, Any]] = None

    previous_recovery_attempts: Optional[List[Dict[str, Any]]] = None
    previous_outcomes: Optional[List[str]] = None

    # Unstructured signals: raw customer or support agent text.
    customer_messages: Optional[List[str]] = None

    event_metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def field_names(cls) -> List[str]:
        return [f.name for f in fields(cls)]

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]) -> "RecoveryCaseInput":
        """Build an instance from an untyped dict, ignoring unknown keys.

        This performs no validation -- it is a shape/coercion step only.
        Validation happens in `nirnay_agent.validation`.
        """
        known = cls.field_names()
        kwargs = {k: v for k, v in raw.items() if k in known}
        return cls(**kwargs)


@dataclass
class Evidence:
    """A single piece of evidence supporting (or contextualizing) a
    diagnosis. `signal` names the underlying data point, `relevance`
    explains -- in plain language -- why it matters to the diagnosis."""

    signal: str
    relevance: str

    def to_dict(self) -> Dict[str, str]:
        return {"signal": self.signal, "relevance": self.relevance}


@dataclass
class DiagnosisResult:
    """The strict, validated output contract. See section 6 / 2B of the
    specification. No fields beyond these may ever be emitted."""

    schema_version: str
    recovery_case_id: str
    scenario_type: str
    root_cause: str
    confidence: float
    diagnosis: str
    evidence: List[Evidence] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    diagnosis_mode: str = DiagnosisMode.FALLBACK.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "recovery_case_id": self.recovery_case_id,
            "scenario_type": self.scenario_type,
            "root_cause": self.root_cause,
            "confidence": round(float(self.confidence), 4),
            "diagnosis": self.diagnosis,
            "evidence": [e.to_dict() for e in self.evidence],
            "uncertainties": list(self.uncertainties),
            "diagnosis_mode": self.diagnosis_mode,
        }


@dataclass
class Signal:
    """An internal, normalized unit of evidence extracted from the input
    before scenario-specific reasoning runs. `source` distinguishes
    strong structured signals from softer unstructured/text signals so the
    conflict-resolution policy (section 9) can prioritize correctly."""

    name: str
    value: Any
    source: str  # "structured" | "text" | "history"
    relevance: str


def is_valid_currency(code: str) -> bool:
    return bool(_CURRENCY_RE.match(code))
