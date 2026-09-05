"""
Structured exceptions for the Nirnay Revenue Diagnosis Agent.

All validation and internal failures are raised as subclasses of
DiagnosisAgentError so callers can catch a single base type, while still
being able to introspect a structured, machine-readable payload via
`to_dict()`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class DiagnosisAgentError(Exception):
    """Base class for all structured errors raised by the agent."""

    error_code: str = "AGENT_ERROR"

    def __init__(self, message: str, field: Optional[str] = None, **extra: Any):
        super().__init__(message)
        self.message = message
        self.field = field
        self.extra = extra

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.field is not None:
            payload["field"] = self.field
        payload.update(self.extra)
        return payload


class InputValidationError(DiagnosisAgentError):
    """Raised when the incoming RecoveryCaseInput fails validation.

    This is the exception used for the cases described in section 2B
    (unsupported scenario_type, negative amounts, malformed decline codes,
    impossible payment counts, invalid field types, etc).
    """

    error_code = "INVALID_INPUT"


class OutputValidationError(DiagnosisAgentError):
    """Raised when a candidate DiagnosisResult (rule-based, LLM-derived, or
    fallback) fails schema/contract validation before being returned to the
    caller. This should never leak to the external caller in normal
    operation -- it signals an internal bug and the agent will attempt a
    safe deterministic fallback instead of raising it outward, except when
    even the fallback cannot be validated, in which case it is raised.
    """

    error_code = "INVALID_OUTPUT"


class LLMProviderError(DiagnosisAgentError):
    """Raised internally by LLM provider adapters on failure (timeout,
    transport error, malformed response, etc). The agent catches this
    internally and triggers the fallback pipeline -- it should not
    propagate to the external caller.
    """

    error_code = "LLM_PROVIDER_ERROR"


class LLMTimeoutError(LLMProviderError):
    error_code = "LLM_TIMEOUT"


class LLMMalformedResponseError(LLMProviderError):
    error_code = "LLM_MALFORMED_RESPONSE"
