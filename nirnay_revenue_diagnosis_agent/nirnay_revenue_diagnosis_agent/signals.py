"""
Signal extraction -- stage 2 of the diagnosis pipeline (section 4).

Converts a NormalizedCase into a flat list of `Signal` objects. Each
signal records its provenance (`structured`, `history`, or `text`) so the
conflict-resolution policy in section 9 can prioritize correctly:

    1. explicit structured transaction signals
    2. verified historical data
    3. customer/support text (contextual only)
"""
from __future__ import annotations

from typing import List

from .enums import ScenarioType
from .models import Signal
from .normalization import NormalizedCase


def extract_signals(normalized: NormalizedCase) -> List[Signal]:
    signals: List[Signal] = []

    # --- Explicit structured transaction signals (highest priority) -----
    if normalized.decline_code:
        signals.append(
            Signal(
                name="decline_code",
                value=normalized.decline_code,
                source="structured",
                relevance="Explicit decline/error code returned by the payment processor.",
            )
        )

    if normalized.payment_signals:
        for key, value in normalized.payment_signals.items():
            signals.append(
                Signal(
                    name=f"payment_signals.{key}",
                    value=value,
                    source="structured",
                    relevance="Structured payment/transaction signal supplied with the case.",
                )
            )

    if normalized.amount_at_risk is not None:
        signals.append(
            Signal(
                name="amount_at_risk",
                value=normalized.amount_at_risk,
                source="structured",
                relevance="Monetary amount currently at risk for this case.",
            )
        )

    if normalized.currency:
        signals.append(
            Signal(
                name="currency",
                value=normalized.currency,
                source="structured",
                relevance="Currency of the at-risk amount.",
            )
        )

    # --- Scenario-specific structured containers ------------------------
    if normalized.scenario_type == ScenarioType.SUBSCRIPTION_FAILURE.value:
        for key, value in normalized.subscription_info.items():
            signals.append(
                Signal(
                    name=f"subscription_info.{key}",
                    value=value,
                    source="structured",
                    relevance="Structured subscription/mandate signal.",
                )
            )
    if normalized.scenario_type == ScenarioType.CHECKOUT_ABANDONMENT.value:
        for key, value in normalized.checkout_info.items():
            signals.append(
                Signal(
                    name=f"checkout_info.{key}",
                    value=value,
                    source="structured",
                    relevance="Structured checkout-session signal.",
                )
            )
    if normalized.scenario_type == ScenarioType.OVERDUE_RECEIVABLE.value:
        for key, value in normalized.receivable_info.items():
            signals.append(
                Signal(
                    name=f"receivable_info.{key}",
                    value=value,
                    source="structured",
                    relevance="Structured receivable/invoice signal.",
                )
            )

    # --- Verified historical data ---------------------------------------
    if normalized.successful_payment_count is not None:
        signals.append(
            Signal(
                name="successful_payment_count",
                value=normalized.successful_payment_count,
                source="history",
                relevance="Count of prior successful payments for this customer.",
            )
        )
    if normalized.failed_payment_count is not None:
        signals.append(
            Signal(
                name="failed_payment_count",
                value=normalized.failed_payment_count,
                source="history",
                relevance="Count of prior failed payments for this customer.",
            )
        )
    if normalized.previous_outcomes:
        signals.append(
            Signal(
                name="previous_outcomes",
                value=normalized.previous_outcomes,
                source="history",
                relevance="Outcomes of previous recovery attempts on this case.",
            )
        )
    if normalized.previous_recovery_attempts:
        signals.append(
            Signal(
                name="previous_recovery_attempts",
                value=normalized.previous_recovery_attempts,
                source="history",
                relevance="Record of previous recovery attempts made on this case.",
            )
        )
    if normalized.customer_tenure is not None:
        signals.append(
            Signal(
                name="customer_tenure",
                value=normalized.customer_tenure,
                source="history",
                relevance="Length of the customer relationship.",
            )
        )
    if normalized.customer_lifetime_value is not None:
        signals.append(
            Signal(
                name="customer_lifetime_value",
                value=normalized.customer_lifetime_value,
                source="history",
                relevance="Historical lifetime value of the customer.",
            )
        )
    if normalized.customer_segment:
        signals.append(
            Signal(
                name="customer_segment",
                value=normalized.customer_segment,
                source="history",
                relevance="Segment classification of the customer.",
            )
        )

    # --- Unstructured / contextual text signals (lowest priority) -------
    if normalized.failure_reason:
        signals.append(
            Signal(
                name="failure_reason",
                value=normalized.failure_reason,
                source="text",
                relevance="Free-text failure reason supplied with the case.",
            )
        )
    for idx, message in enumerate(normalized.customer_messages):
        signals.append(
            Signal(
                name=f"customer_messages[{idx}]",
                value=message,
                source="text",
                relevance="Customer or support message providing contextual evidence.",
            )
        )
    if normalized.event_metadata:
        for key, value in normalized.event_metadata.items():
            signals.append(
                Signal(
                    name=f"event_metadata.{key}",
                    value=value,
                    source="text",
                    relevance="Supplementary event metadata.",
                )
            )

    return signals
