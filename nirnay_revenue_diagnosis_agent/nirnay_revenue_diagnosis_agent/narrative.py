"""
Generates the human-readable `diagnosis` string for diagnoses produced by
the deterministic rule engine (RULE / FALLBACK modes). AI-mode diagnoses
use the LLM's own natural-language explanation instead (still validated,
never fabricated beyond what the model was given).

Templates only ever describe the evidence that was actually found --
they never assert facts that weren't present in the input.
"""
from __future__ import annotations

from typing import List

from .enums import (
    RootCauseCheckoutAbandonment,
    RootCauseOverdueReceivable,
    RootCausePaymentFailure,
    RootCauseSubscriptionFailure,
    ScenarioType,
)
from .models import Evidence

# NOTE: root-cause string *values* are intentionally reused across
# scenarios (e.g. "INSUFFICIENT_FUNDS" and "PAYMENT_METHOD_FAILURE" appear
# in both PAYMENT_FAILURE and SUBSCRIPTION_FAILURE). Descriptions are
# therefore keyed by (scenario_type, root_cause), never by root_cause
# alone, to avoid cross-scenario collisions.
_DESCRIPTIONS = {
    (ScenarioType.PAYMENT_FAILURE.value, RootCausePaymentFailure.INSUFFICIENT_FUNDS.value): (
        "the payment failed due to insufficient funds on the customer's payment method"
    ),
    (ScenarioType.PAYMENT_FAILURE.value, RootCausePaymentFailure.PAYMENT_METHOD_FAILURE.value): (
        "the payment method itself was rejected (e.g. invalid, restricted, or flagged)"
    ),
    (ScenarioType.PAYMENT_FAILURE.value, RootCausePaymentFailure.BANK_DECLINE.value): (
        "the customer's bank declined the transaction"
    ),
    (ScenarioType.PAYMENT_FAILURE.value, RootCausePaymentFailure.EXPIRED_PAYMENT_METHOD.value): (
        "the payment method on file had expired"
    ),
    (ScenarioType.PAYMENT_FAILURE.value, RootCausePaymentFailure.TEMPORARY_PROCESSING_FAILURE.value): (
        "a temporary processing failure occurred, likely unrelated to the customer's ability to pay"
    ),
    (ScenarioType.PAYMENT_FAILURE.value, RootCausePaymentFailure.UNKNOWN_PAYMENT_FAILURE.value): (
        "the available evidence is insufficient to determine why the payment failed"
    ),
    (ScenarioType.CHECKOUT_ABANDONMENT.value, RootCauseCheckoutAbandonment.USER_ABANDONMENT.value): (
        "the customer abandoned checkout for reasons not further specified by the available signals"
    ),
    (ScenarioType.CHECKOUT_ABANDONMENT.value, RootCauseCheckoutAbandonment.PAYMENT_STAGE_DROPOFF.value): (
        "the customer abandoned checkout specifically at the payment step"
    ),
    (ScenarioType.CHECKOUT_ABANDONMENT.value, RootCauseCheckoutAbandonment.CHECKOUT_ERROR.value): (
        "a technical error in the checkout flow interrupted the customer"
    ),
    (ScenarioType.CHECKOUT_ABANDONMENT.value, RootCauseCheckoutAbandonment.PRICE_FRICTION.value): (
        "the customer appears to have abandoned after reviewing price/cost information"
    ),
    (ScenarioType.CHECKOUT_ABANDONMENT.value, RootCauseCheckoutAbandonment.UNKNOWN_ABANDONMENT.value): (
        "the available evidence is insufficient to determine why checkout was abandoned"
    ),
    (ScenarioType.SUBSCRIPTION_FAILURE.value, RootCauseSubscriptionFailure.PAYMENT_METHOD_FAILURE.value): (
        "the subscription renewal failed because the payment method was rejected"
    ),
    (ScenarioType.SUBSCRIPTION_FAILURE.value, RootCauseSubscriptionFailure.INSUFFICIENT_FUNDS.value): (
        "the subscription renewal failed due to insufficient funds"
    ),
    (ScenarioType.SUBSCRIPTION_FAILURE.value, RootCauseSubscriptionFailure.RENEWAL_FAILURE.value): (
        "the subscription renewal failed for reasons not further specified by the available signals"
    ),
    (ScenarioType.SUBSCRIPTION_FAILURE.value, RootCauseSubscriptionFailure.MANDATE_FAILURE.value): (
        "the payment mandate authorizing recurring charges failed or was revoked"
    ),
    (ScenarioType.SUBSCRIPTION_FAILURE.value, RootCauseSubscriptionFailure.UNKNOWN_SUBSCRIPTION_FAILURE.value): (
        "the available evidence is insufficient to determine why the subscription failed"
    ),
    (ScenarioType.OVERDUE_RECEIVABLE.value, RootCauseOverdueReceivable.PAYMENT_DELAY.value): (
        "the invoice is overdue with no specific dispute or error identified"
    ),
    (ScenarioType.OVERDUE_RECEIVABLE.value, RootCauseOverdueReceivable.CUSTOMER_DISPUTE.value): (
        "the invoice is overdue because the customer has disputed it"
    ),
    (ScenarioType.OVERDUE_RECEIVABLE.value, RootCauseOverdueReceivable.CASH_FLOW_DELAY.value): (
        "the invoice is overdue and there is a signal of customer-side cash flow constraints"
    ),
    (ScenarioType.OVERDUE_RECEIVABLE.value, RootCauseOverdueReceivable.INVOICE_ISSUE.value): (
        "the invoice is overdue and appears to contain an error on the invoice itself"
    ),
    (ScenarioType.OVERDUE_RECEIVABLE.value, RootCauseOverdueReceivable.UNKNOWN_RECEIVABLE_DELAY.value): (
        "the available evidence is insufficient to determine why the receivable is overdue"
    ),
}


def generate_diagnosis_text(
    scenario_type: str, root_cause: str, evidence: List[Evidence], uncertainties: List[str]
) -> str:
    description = _DESCRIPTIONS.get(
        (scenario_type, root_cause), "the available evidence does not map to a known cause"
    )
    text = f"Based on the available evidence, {description}."
    if evidence:
        signal_names = ", ".join(e.signal for e in evidence)
        text += f" Supporting signals: {signal_names}."
    if uncertainties:
        text += " Insufficient evidence." if not evidence else ""
    return text
