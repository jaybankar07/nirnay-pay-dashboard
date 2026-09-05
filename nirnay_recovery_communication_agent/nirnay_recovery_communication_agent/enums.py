"""
Controlled vocabularies used across the agent.

Using plain string-based Enums (rather than free text) keeps the agent
strict about what it accepts, per the "no hallucination / no invented
categories" requirement.
"""

from enum import Enum


class SelectedAction(str, Enum):
    """Authoritative recovery actions. These come from the external
    decision engine and are NEVER chosen by this agent."""

    RETRY = "RETRY"
    GRACE_PERIOD = "GRACE_PERIOD"
    REMINDER = "REMINDER"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    ESCALATE = "ESCALATE"
    WAIT = "WAIT"
    STOP = "STOP"
    BLOCKED = "BLOCKED"

    @classmethod
    def values(cls):
        return {member.value for member in cls}


# Actions that must NEVER be communicated as "recovery in progress".
TERMINAL_NO_ACTION_STATES = {SelectedAction.STOP, SelectedAction.BLOCKED}


class CommunicationPurpose(str, Enum):
    DECISION_EXPLANATION = "DECISION_EXPLANATION"
    CUSTOMER_RECOVERY_MESSAGE = "CUSTOMER_RECOVERY_MESSAGE"
    MERCHANT_EXPLANATION = "MERCHANT_EXPLANATION"

    @classmethod
    def values(cls):
        return {member.value for member in cls}


class Tone(str, Enum):
    PROFESSIONAL = "PROFESSIONAL"
    FRIENDLY = "FRIENDLY"
    CONCISE = "CONCISE"

    @classmethod
    def values(cls):
        return {member.value for member in cls}


class SupportedLanguage(str, Enum):
    """Languages the agent can reliably generate. Anything else falls
    back to English with a fallback indicator set (see section 9)."""

    EN = "en"

    @classmethod
    def values(cls):
        return {member.value for member in cls}


class DiagnosisMode(str, Enum):
    """Retained for downstream/upstream schema compatibility
    (see spec section 2B / DiagnosisResult). This agent does not
    produce diagnoses itself, but may echo an upstream diagnosis_mode
    value if supplied on the input."""

    RULE = "RULE"
    AI = "AI"
    FALLBACK = "FALLBACK"

    @classmethod
    def values(cls):
        return {member.value for member in cls}


# Allowed scenario types. Kept intentionally generic/extensible: unknown
# values are rejected by validation rather than silently accepted.
SUPPORTED_SCENARIO_TYPES = {
    "CARD_DECLINE",
    "INSUFFICIENT_FUNDS",
    "SUBSCRIPTION_RENEWAL_FAILURE",
    "AUTHENTICATION_FAILURE",
    "NETWORK_ERROR",
    "FRAUD_SUSPECTED",
    "GATEWAY_TIMEOUT",
    "BANK_ISSUE",
    "OTHER",
}
