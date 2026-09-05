"""
Deterministic fallback templates (section 14).

These are used when:
  - the LLM call fails/times out, or
  - the LLM output fails the safety layer twice in a row.

They must be neutral, safe, non-threatening, and never invent facts.
They are intentionally simple string templates (not LLM-generated) so
they can never be "unsafe" -- they are the ground truth of last resort.
"""

from .enums import SelectedAction

# Keyword(s) the safety layer expects to find for each action so that a
# generated message can be verified to actually reference the approved
# action (section 13, check #1).
ACTION_KEYWORDS = {
    SelectedAction.RETRY: ["retry", "attempt again", "reattempt"],
    SelectedAction.GRACE_PERIOD: ["grace period", "additional time", "extra time"],
    SelectedAction.REMINDER: ["reminder", "pending", "review"],
    SelectedAction.HUMAN_REVIEW: ["review", "our team", "follow up"],
    SelectedAction.ESCALATE: ["escalat", "specialist", "priority"],
    SelectedAction.WAIT: ["wait", "no action is needed", "monitor"],
    SelectedAction.STOP: ["no further", "stopped", "will not"],
    SelectedAction.BLOCKED: ["cannot proceed", "blocked", "not permitted"],
}

_CUSTOMER_FALLBACK = {
    SelectedAction.RETRY: (
        "We were unable to complete your recent payment. We will "
        "automatically retry the payment through our standard recovery "
        "process. No action is required from you right now."
    ),
    SelectedAction.GRACE_PERIOD: (
        "We were unable to complete your recent payment. We have given "
        "you an additional grace period to resolve this before any "
        "further action is taken."
    ),
    SelectedAction.REMINDER: (
        "This is a reminder that your recent payment is still pending. "
        "Please review your payment details when convenient."
    ),
    SelectedAction.HUMAN_REVIEW: (
        "We were unable to complete your recent payment. Our team will "
        "review this case and follow up with you directly."
    ),
    SelectedAction.ESCALATE: (
        "Your case has been escalated to a specialist team for further "
        "review. They will follow up with you directly."
    ),
    SelectedAction.WAIT: (
        "We are currently monitoring your payment status. No action is "
        "needed from you at this time."
    ),
    SelectedAction.STOP: (
        "No further automatic recovery action will be taken on this "
        "payment at this time."
    ),
    SelectedAction.BLOCKED: (
        "We are currently unable to proceed with recovery on this "
        "payment. No further automatic action will be taken at this time."
    ),
}

_MERCHANT_FALLBACK = {
    SelectedAction.RETRY: (
        "This case has been routed to automated retry as the approved "
        "recovery action based on the available case signals."
    ),
    SelectedAction.GRACE_PERIOD: (
        "This case has been given a grace period as the approved "
        "recovery action instead of an active retry or reminder."
    ),
    SelectedAction.REMINDER: (
        "This case has been routed to a customer reminder as the "
        "approved recovery action."
    ),
    SelectedAction.HUMAN_REVIEW: (
        "This case has been routed to human review as the approved "
        "recovery action rather than an automated step."
    ),
    SelectedAction.ESCALATE: (
        "This case has been escalated to a specialist team as the "
        "approved recovery action."
    ),
    SelectedAction.WAIT: (
        "This case is in a monitoring/wait state as the approved "
        "recovery action; no active step is being taken yet."
    ),
    SelectedAction.STOP: (
        "No further automatic recovery action has been approved for "
        "this case."
    ),
    SelectedAction.BLOCKED: (
        "This case is blocked from further recovery action based on the "
        "governing compliance/recovery-rights result supplied to this "
        "agent."
    ),
}


def fallback_customer_message(selected_action: SelectedAction) -> str:
    return _CUSTOMER_FALLBACK.get(
        selected_action,
        "We are reviewing your recent payment. No further automatic "
        "action will be taken until this review is complete.",
    )


def fallback_merchant_summary(selected_action: SelectedAction) -> str:
    return _MERCHANT_FALLBACK.get(
        selected_action,
        "This case's approved recovery action could not be summarized "
        "safely; refer to selected_action and decision_rationale directly.",
    )


def fallback_decision_explanation(selected_action: SelectedAction) -> str:
    return (
        f"The approved recovery action for this case is {selected_action.value}. "
        "This explanation was generated from a safe default template "
        "because a dynamic explanation could not be produced or validated."
    )
