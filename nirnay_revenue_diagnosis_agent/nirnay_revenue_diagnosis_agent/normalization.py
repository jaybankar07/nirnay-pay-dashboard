"""
Input normalization -- stage 1 of the diagnosis pipeline (section 4).

Normalization never invents data. It only standardizes representation
(casing, whitespace) and records which fields are actually present so
later stages can reason about evidence quality honestly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import RecoveryCaseInput


@dataclass
class NormalizedCase:
    original: RecoveryCaseInput

    recovery_case_id: str = ""
    scenario_type: str = ""

    amount_at_risk: Optional[float] = None
    currency: Optional[str] = None

    customer_segment: Optional[str] = None
    customer_tenure: Optional[Any] = None
    customer_lifetime_value: Optional[float] = None

    successful_payment_count: Optional[int] = None
    failed_payment_count: Optional[int] = None

    payment_signals: Dict[str, Any] = field(default_factory=dict)
    decline_code: Optional[str] = None
    failure_reason: Optional[str] = None

    subscription_info: Dict[str, Any] = field(default_factory=dict)
    checkout_info: Dict[str, Any] = field(default_factory=dict)
    receivable_info: Dict[str, Any] = field(default_factory=dict)

    previous_recovery_attempts: List[Dict[str, Any]] = field(default_factory=list)
    previous_outcomes: List[str] = field(default_factory=list)

    customer_messages: List[str] = field(default_factory=list)
    event_metadata: Dict[str, Any] = field(default_factory=dict)

    present_fields: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)

    @property
    def has_history(self) -> bool:
        return (
            (self.successful_payment_count is not None)
            or (self.failed_payment_count is not None)
            or bool(self.previous_recovery_attempts)
            or bool(self.previous_outcomes)
        )

    @property
    def has_text_signals(self) -> bool:
        return bool(self.customer_messages) or bool(self.failure_reason)


def _strip_or_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def normalize(case: RecoveryCaseInput) -> NormalizedCase:
    """Normalize a validated RecoveryCaseInput. Whitespace is trimmed,
    decline codes are upper-cased for consistent matching, and empty
    optional containers default to `{}` / `[]` (never fabricated values).
    """
    present: List[str] = []
    missing: List[str] = []

    def track(name: str, value: Any) -> Any:
        is_present = value is not None and value != {} and value != [] and value != ""
        (present if is_present else missing).append(name)
        return value

    normalized = NormalizedCase(
        original=case,
        recovery_case_id=case.recovery_case_id,
        scenario_type=case.scenario_type,
        amount_at_risk=track("amount_at_risk", case.amount_at_risk),
        currency=track("currency", _strip_or_none(case.currency)),
        customer_segment=track("customer_segment", _strip_or_none(case.customer_segment)),
        customer_tenure=track("customer_tenure", case.customer_tenure),
        customer_lifetime_value=track(
            "customer_lifetime_value", case.customer_lifetime_value
        ),
        successful_payment_count=track(
            "successful_payment_count", case.successful_payment_count
        ),
        failed_payment_count=track("failed_payment_count", case.failed_payment_count),
        payment_signals=track("payment_signals", case.payment_signals) or {},
        decline_code=track(
            "decline_code",
            _strip_or_none(case.decline_code).upper() if case.decline_code else None,
        ),
        failure_reason=track("failure_reason", _strip_or_none(case.failure_reason)),
        subscription_info=track("subscription_info", case.subscription_info) or {},
        checkout_info=track("checkout_info", case.checkout_info) or {},
        receivable_info=track("receivable_info", case.receivable_info) or {},
        previous_recovery_attempts=track(
            "previous_recovery_attempts", case.previous_recovery_attempts
        )
        or [],
        previous_outcomes=track("previous_outcomes", case.previous_outcomes) or [],
        customer_messages=track(
            "customer_messages",
            [m.strip() for m in case.customer_messages if m and m.strip()]
            if case.customer_messages
            else None,
        )
        or [],
        event_metadata=track("event_metadata", case.event_metadata) or {},
        present_fields=[],
        missing_fields=[],
    )
    normalized.present_fields = present
    normalized.missing_fields = missing
    return normalized
