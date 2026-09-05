"""
Structured exceptions.

Per spec: invalid input, decision inconsistency, or missing context must
produce a STRUCTURED error rather than an invented/best-guess result.
Each exception carries a machine-readable `.to_dict()` payload so callers
never have to parse free-text error strings.
"""


class NirnayAgentError(Exception):
    """Base class for all agent errors."""

    error_code = "NIRNAY_AGENT_ERROR"

    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.details = details or {}

    def to_dict(self) -> dict:
        payload = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.field:
            payload["field"] = self.field
        if self.details:
            payload["details"] = self.details
        return payload


class InputValidationError(NirnayAgentError):
    """Raised when the input object is malformed or contains
    unsupported/impossible values (section 2B)."""

    error_code = "INVALID_INPUT"


class DecisionConsistencyError(NirnayAgentError):
    """Raised when the supplied decision fields contradict each other,
    e.g. compliance_result is blocked but selected_action implies an
    active recovery action (section 4 - Decision Lock)."""

    error_code = "INCONSISTENT_DECISION"


class IncompleteContextError(NirnayAgentError):
    """Raised when required facts are missing for the requested
    communication_purpose, so the agent refuses to invent them
    (section 11 - No-Hallucination Rule)."""

    error_code = "INCOMPLETE_CONTEXT"


class UnsafeOutputError(NirnayAgentError):
    """Internal signal used by the safety layer when generated content
    fails validation even after a retry. Not normally raised to the
    caller -- it triggers the deterministic fallback template instead."""

    error_code = "UNSAFE_OUTPUT"
