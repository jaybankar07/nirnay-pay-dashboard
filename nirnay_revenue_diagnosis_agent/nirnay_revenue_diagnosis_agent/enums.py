"""
Controlled vocabularies for the Nirnay Revenue Diagnosis Agent.

These are deliberately closed enumerations (not free text) so that
downstream systems (decision engines, RecoveryScore engines, compliance
engines, etc.) can rely on a stable, finite contract.
"""
from __future__ import annotations

from enum import Enum


class ScenarioType(str, Enum):
    PAYMENT_FAILURE = "PAYMENT_FAILURE"
    CHECKOUT_ABANDONMENT = "CHECKOUT_ABANDONMENT"
    SUBSCRIPTION_FAILURE = "SUBSCRIPTION_FAILURE"
    OVERDUE_RECEIVABLE = "OVERDUE_RECEIVABLE"


class DiagnosisMode(str, Enum):
    RULE = "RULE"
    AI = "AI"
    FALLBACK = "FALLBACK"


class RootCausePaymentFailure(str, Enum):
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    PAYMENT_METHOD_FAILURE = "PAYMENT_METHOD_FAILURE"
    BANK_DECLINE = "BANK_DECLINE"
    EXPIRED_PAYMENT_METHOD = "EXPIRED_PAYMENT_METHOD"
    TEMPORARY_PROCESSING_FAILURE = "TEMPORARY_PROCESSING_FAILURE"
    UNKNOWN_PAYMENT_FAILURE = "UNKNOWN_PAYMENT_FAILURE"


class RootCauseCheckoutAbandonment(str, Enum):
    USER_ABANDONMENT = "USER_ABANDONMENT"
    PAYMENT_STAGE_DROPOFF = "PAYMENT_STAGE_DROPOFF"
    CHECKOUT_ERROR = "CHECKOUT_ERROR"
    PRICE_FRICTION = "PRICE_FRICTION"
    UNKNOWN_ABANDONMENT = "UNKNOWN_ABANDONMENT"


class RootCauseSubscriptionFailure(str, Enum):
    PAYMENT_METHOD_FAILURE = "PAYMENT_METHOD_FAILURE"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    RENEWAL_FAILURE = "RENEWAL_FAILURE"
    MANDATE_FAILURE = "MANDATE_FAILURE"
    UNKNOWN_SUBSCRIPTION_FAILURE = "UNKNOWN_SUBSCRIPTION_FAILURE"


class RootCauseOverdueReceivable(str, Enum):
    PAYMENT_DELAY = "PAYMENT_DELAY"
    CUSTOMER_DISPUTE = "CUSTOMER_DISPUTE"
    CASH_FLOW_DELAY = "CASH_FLOW_DELAY"
    INVOICE_ISSUE = "INVOICE_ISSUE"
    UNKNOWN_RECEIVABLE_DELAY = "UNKNOWN_RECEIVABLE_DELAY"


# Mapping from scenario -> controlled root-cause enum for that scenario.
ROOT_CAUSE_ENUM_BY_SCENARIO = {
    ScenarioType.PAYMENT_FAILURE: RootCausePaymentFailure,
    ScenarioType.CHECKOUT_ABANDONMENT: RootCauseCheckoutAbandonment,
    ScenarioType.SUBSCRIPTION_FAILURE: RootCauseSubscriptionFailure,
    ScenarioType.OVERDUE_RECEIVABLE: RootCauseOverdueReceivable,
}

# The "unknown" fallback root cause for each scenario, used whenever
# evidence is insufficient to classify with confidence.
UNKNOWN_ROOT_CAUSE_BY_SCENARIO = {
    ScenarioType.PAYMENT_FAILURE: RootCausePaymentFailure.UNKNOWN_PAYMENT_FAILURE,
    ScenarioType.CHECKOUT_ABANDONMENT: RootCauseCheckoutAbandonment.UNKNOWN_ABANDONMENT,
    ScenarioType.SUBSCRIPTION_FAILURE: RootCauseSubscriptionFailure.UNKNOWN_SUBSCRIPTION_FAILURE,
    ScenarioType.OVERDUE_RECEIVABLE: RootCauseOverdueReceivable.UNKNOWN_RECEIVABLE_DELAY,
}


def is_valid_root_cause(scenario_type: ScenarioType, root_cause: str) -> bool:
    """Return True if root_cause is a member of the controlled taxonomy for
    the given scenario_type."""
    enum_cls = ROOT_CAUSE_ENUM_BY_SCENARIO.get(scenario_type)
    if enum_cls is None:
        return False
    try:
        enum_cls(root_cause)
        return True
    except ValueError:
        return False
