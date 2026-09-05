"""
Deterministic rule engine -- scenario-specific analysis and root-cause
classification (section 4, "Scenario-specific analysis" ->
"Root-cause classification").

The rule engine is the agent's preferred path whenever strong structured
signals exist (section 4: "Prefer deterministic interpretation when
strong structured signals exist"). It never fabricates evidence: if the
structured signals are absent or don't map cleanly to a taxonomy entry,
it returns an UNKNOWN_* root cause with low confidence and defers to the
LLM stage for any unstructured text that might help.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from . import confidence as conf
from .enums import (
    RootCauseCheckoutAbandonment,
    RootCauseOverdueReceivable,
    RootCausePaymentFailure,
    RootCauseSubscriptionFailure,
    ScenarioType,
    UNKNOWN_ROOT_CAUSE_BY_SCENARIO,
)
from .models import Evidence
from .normalization import NormalizedCase

# Ordered keyword -> root cause mapping for decline codes / failure text.
# Order matters: first match wins. Kept scenario-agnostic since decline
# codes mean roughly the same thing across payment-bearing scenarios.
_DECLINE_CODE_KEYWORDS = [
    (("INSUFFICIENT",), RootCausePaymentFailure.INSUFFICIENT_FUNDS),
    (("EXPIRED",), RootCausePaymentFailure.EXPIRED_PAYMENT_METHOD),
    (("TEMPORARY", "PROCESSING_ERROR", "RETRY", "TRY_AGAIN", "TIMEOUT"),
     RootCausePaymentFailure.TEMPORARY_PROCESSING_FAILURE),
    (("STOLEN", "LOST", "INVALID_CARD", "RESTRICTED", "PICKUP", "FRAUD", "CVC", "CVV"),
     RootCausePaymentFailure.PAYMENT_METHOD_FAILURE),
    (("DO_NOT_HONOR", "DECLINE", "BANK"), RootCausePaymentFailure.BANK_DECLINE),
]


@dataclass
class RuleOutcome:
    """Result of running the deterministic rule engine on a scenario."""

    root_cause: str
    confidence: float
    evidence: List[Evidence] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    # True when the structured evidence alone is strong enough that the
    # agent should skip the LLM stage entirely (RULE mode).
    decisive: bool = False


def _match_decline_code(decline_code: Optional[str]):
    if not decline_code:
        return None
    for keywords, root_cause in _DECLINE_CODE_KEYWORDS:
        if any(kw in decline_code for kw in keywords):
            return root_cause
    return None


def _history_consistency_note(normalized: NormalizedCase) -> Optional[str]:
    """Section 7 example: 0 prior failures + long clean history + a
    'temporary' decline code is *stronger* evidence for a temporary
    processing failure than the decline code alone."""
    if (
        normalized.failed_payment_count == 0
        and normalized.successful_payment_count
        and normalized.successful_payment_count > 0
    ):
        return (
            f"{normalized.successful_payment_count} prior successful payments and "
            f"0 prior failures support a non-chronic, likely transient issue."
        )
    return None


def analyze_payment_failure(normalized: NormalizedCase) -> RuleOutcome:
    unknown = UNKNOWN_ROOT_CAUSE_BY_SCENARIO[ScenarioType.PAYMENT_FAILURE].value
    evidence: List[Evidence] = []
    uncertainties: List[str] = []

    matched_root_cause = _match_decline_code(normalized.decline_code)

    if matched_root_cause is not None:
        evidence.append(
            Evidence(
                signal="decline_code",
                relevance=(
                    f"Decline code '{normalized.decline_code}' maps to "
                    f"{matched_root_cause.value} in the controlled taxonomy."
                ),
            )
        )
        confidence = conf.DEFAULT_EXPLICIT
        history_note = _history_consistency_note(normalized)
        if history_note:
            evidence.append(Evidence(signal="payment_history", relevance=history_note))
            confidence = min(1.0, confidence + 0.02)

        # Conflict check: a large amount at risk combined with an
        # "insufficient funds" style code on a high-LTV, long-tenure
        # customer is still just reported as-is -- no override -- but if
        # failed_payment_count is high while the code claims "temporary",
        # that's a genuine conflict worth flagging.
        if (
            matched_root_cause == RootCausePaymentFailure.TEMPORARY_PROCESSING_FAILURE
            and normalized.failed_payment_count
            and normalized.failed_payment_count >= 3
        ):
            uncertainties.append(
                "Decline code suggests a temporary issue, but repeated prior "
                "failures make a purely transient cause less certain."
            )
            confidence = conf.lower_for_conflict(confidence)

        return RuleOutcome(
            root_cause=matched_root_cause.value,
            confidence=conf.clamp(confidence),
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=True,
        )

    if normalized.decline_code:
        # We have a decline code but it didn't match any known keyword --
        # this is evidence of *something* but not enough to classify.
        evidence.append(
            Evidence(
                signal="decline_code",
                relevance=(
                    f"Decline code '{normalized.decline_code}' was provided but does "
                    "not match a known category in the controlled taxonomy."
                ),
            )
        )
        uncertainties.append("decline_code is present but unrecognized.")
        return RuleOutcome(
            root_cause=unknown,
            confidence=conf.DEFAULT_LIMITED,
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=False,
        )

    uncertainties.append("No decline_code was provided.")
    return RuleOutcome(
        root_cause=unknown,
        confidence=conf.DEFAULT_INSUFFICIENT,
        evidence=evidence,
        uncertainties=uncertainties,
        decisive=False,
    )


def analyze_subscription_failure(normalized: NormalizedCase) -> RuleOutcome:
    unknown = UNKNOWN_ROOT_CAUSE_BY_SCENARIO[ScenarioType.SUBSCRIPTION_FAILURE].value
    evidence: List[Evidence] = []
    uncertainties: List[str] = []
    sub = normalized.subscription_info

    mandate_status = str(sub.get("mandate_status", "")).lower()
    if mandate_status in ("failed", "revoked", "cancelled", "canceled", "invalid"):
        evidence.append(
            Evidence(
                signal="subscription_info.mandate_status",
                relevance=f"Mandate status reported as '{mandate_status}'.",
            )
        )
        return RuleOutcome(
            root_cause=RootCauseSubscriptionFailure.MANDATE_FAILURE.value,
            confidence=conf.DEFAULT_EXPLICIT,
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=True,
        )

    matched_root_cause = _match_decline_code(normalized.decline_code)
    if matched_root_cause in (
        RootCausePaymentFailure.INSUFFICIENT_FUNDS,
        RootCausePaymentFailure.EXPIRED_PAYMENT_METHOD,
        RootCausePaymentFailure.PAYMENT_METHOD_FAILURE,
    ):
        mapped = {
            RootCausePaymentFailure.INSUFFICIENT_FUNDS: RootCauseSubscriptionFailure.INSUFFICIENT_FUNDS,
            RootCausePaymentFailure.EXPIRED_PAYMENT_METHOD: RootCauseSubscriptionFailure.PAYMENT_METHOD_FAILURE,
            RootCausePaymentFailure.PAYMENT_METHOD_FAILURE: RootCauseSubscriptionFailure.PAYMENT_METHOD_FAILURE,
        }[matched_root_cause]
        evidence.append(
            Evidence(
                signal="decline_code",
                relevance=(
                    f"Decline code '{normalized.decline_code}' maps to {mapped.value} "
                    "for a subscription renewal charge."
                ),
            )
        )
        return RuleOutcome(
            root_cause=mapped.value,
            confidence=conf.DEFAULT_EXPLICIT,
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=True,
        )

    renewal_status = str(sub.get("renewal_status", "")).lower()
    if renewal_status == "failed":
        evidence.append(
            Evidence(
                signal="subscription_info.renewal_status",
                relevance="Renewal status explicitly reported as 'failed'.",
            )
        )
        confidence = conf.DEFAULT_STRONG_MULTI
        if not normalized.decline_code:
            uncertainties.append(
                "Renewal failed but no decline_code was provided to explain why."
            )
            confidence = conf.lower_for_missing_data(confidence)
        return RuleOutcome(
            root_cause=RootCauseSubscriptionFailure.RENEWAL_FAILURE.value,
            confidence=conf.clamp(confidence),
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=True,
        )

    if not sub and not normalized.decline_code:
        uncertainties.append("No subscription_info or decline_code was provided.")
        return RuleOutcome(
            root_cause=unknown,
            confidence=conf.DEFAULT_INSUFFICIENT,
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=False,
        )

    uncertainties.append(
        "subscription_info was provided but does not clearly indicate a known "
        "failure category."
    )
    return RuleOutcome(
        root_cause=unknown,
        confidence=conf.DEFAULT_LIMITED,
        evidence=evidence,
        uncertainties=uncertainties,
        decisive=False,
    )


def analyze_checkout_abandonment(normalized: NormalizedCase) -> RuleOutcome:
    unknown = UNKNOWN_ROOT_CAUSE_BY_SCENARIO[ScenarioType.CHECKOUT_ABANDONMENT].value
    evidence: List[Evidence] = []
    uncertainties: List[str] = []
    checkout = normalized.checkout_info

    error_flag = checkout.get("error")
    if error_flag:
        evidence.append(
            Evidence(
                signal="checkout_info.error",
                relevance=f"Checkout session reported an error: {error_flag!r}.",
            )
        )
        return RuleOutcome(
            root_cause=RootCauseCheckoutAbandonment.CHECKOUT_ERROR.value,
            confidence=conf.DEFAULT_EXPLICIT,
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=True,
        )

    last_stage = str(checkout.get("last_stage", "")).lower()
    if last_stage in ("payment", "payment_details", "payment_method"):
        evidence.append(
            Evidence(
                signal="checkout_info.last_stage",
                relevance="Session progressed to the payment stage before abandoning.",
            )
        )
        return RuleOutcome(
            root_cause=RootCauseCheckoutAbandonment.PAYMENT_STAGE_DROPOFF.value,
            confidence=conf.DEFAULT_STRONG_MULTI,
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=True,
        )

    if last_stage in ("price_review", "cart", "shipping_cost", "order_summary") and (
        checkout.get("price_viewed") or last_stage == "price_review"
    ):
        evidence.append(
            Evidence(
                signal="checkout_info.last_stage",
                relevance="Session ended at pricing/cost review, suggesting price friction.",
            )
        )
        return RuleOutcome(
            root_cause=RootCauseCheckoutAbandonment.PRICE_FRICTION.value,
            confidence=conf.DEFAULT_MIXED,
            evidence=evidence,
            uncertainties=["Price friction is inferred from session stage, not confirmed by the customer."],
            decisive=True,
        )

    if last_stage:
        evidence.append(
            Evidence(
                signal="checkout_info.last_stage",
                relevance=f"Session ended at stage '{last_stage}' with no error reported.",
            )
        )
        uncertainties.append(
            "Abandonment stage is known but does not clearly indicate the cause."
        )
        return RuleOutcome(
            root_cause=RootCauseCheckoutAbandonment.USER_ABANDONMENT.value,
            confidence=conf.DEFAULT_MIXED,
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=True,
        )

    uncertainties.append("No checkout_info was provided.")
    return RuleOutcome(
        root_cause=unknown,
        confidence=conf.DEFAULT_INSUFFICIENT,
        evidence=evidence,
        uncertainties=uncertainties,
        decisive=False,
    )


def analyze_overdue_receivable(normalized: NormalizedCase) -> RuleOutcome:
    unknown = UNKNOWN_ROOT_CAUSE_BY_SCENARIO[ScenarioType.OVERDUE_RECEIVABLE].value
    evidence: List[Evidence] = []
    uncertainties: List[str] = []
    receivable = normalized.receivable_info

    if receivable.get("dispute_flag"):
        evidence.append(
            Evidence(
                signal="receivable_info.dispute_flag",
                relevance="Invoice is explicitly flagged as disputed by the customer.",
            )
        )
        return RuleOutcome(
            root_cause=RootCauseOverdueReceivable.CUSTOMER_DISPUTE.value,
            confidence=conf.DEFAULT_EXPLICIT,
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=True,
        )

    if receivable.get("invoice_error"):
        evidence.append(
            Evidence(
                signal="receivable_info.invoice_error",
                relevance="Invoice is flagged as containing an error.",
            )
        )
        return RuleOutcome(
            root_cause=RootCauseOverdueReceivable.INVOICE_ISSUE.value,
            confidence=conf.DEFAULT_EXPLICIT,
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=True,
        )

    days_overdue = receivable.get("days_overdue")
    if isinstance(days_overdue, (int, float)) and days_overdue > 0:
        evidence.append(
            Evidence(
                signal="receivable_info.days_overdue",
                relevance=f"Invoice is {days_overdue} day(s) overdue with no dispute or invoice error flagged.",
            )
        )
        confidence = conf.DEFAULT_STRONG_MULTI
        root_cause = RootCauseOverdueReceivable.PAYMENT_DELAY.value
        if receivable.get("customer_cash_flow_signal") or receivable.get(
            "cash_flow_issue"
        ):
            evidence.append(
                Evidence(
                    signal="receivable_info.cash_flow_issue",
                    relevance="Customer-reported cash flow constraint on record.",
                )
            )
            root_cause = RootCauseOverdueReceivable.CASH_FLOW_DELAY.value
            confidence = conf.DEFAULT_EXPLICIT
        return RuleOutcome(
            root_cause=root_cause,
            confidence=confidence,
            evidence=evidence,
            uncertainties=uncertainties,
            decisive=True,
        )

    uncertainties.append("No receivable_info was provided (e.g. days_overdue, dispute_flag).")
    return RuleOutcome(
        root_cause=unknown,
        confidence=conf.DEFAULT_INSUFFICIENT,
        evidence=evidence,
        uncertainties=uncertainties,
        decisive=False,
    )


_ANALYZERS = {
    ScenarioType.PAYMENT_FAILURE.value: analyze_payment_failure,
    ScenarioType.SUBSCRIPTION_FAILURE.value: analyze_subscription_failure,
    ScenarioType.CHECKOUT_ABANDONMENT.value: analyze_checkout_abandonment,
    ScenarioType.OVERDUE_RECEIVABLE.value: analyze_overdue_receivable,
}


def run_rule_engine(normalized: NormalizedCase) -> RuleOutcome:
    """Dispatch to the scenario-specific deterministic analyzer."""
    analyzer = _ANALYZERS.get(normalized.scenario_type)
    if analyzer is None:
        unknown = UNKNOWN_ROOT_CAUSE_BY_SCENARIO.get(
            ScenarioType.PAYMENT_FAILURE
        ).value
        return RuleOutcome(
            root_cause=unknown,
            confidence=conf.DEFAULT_INSUFFICIENT,
            evidence=[],
            uncertainties=["Unsupported scenario_type reached the rule engine."],
            decisive=False,
        )
    return analyzer(normalized)
