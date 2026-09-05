"""
Mock LLM provider adapter.

Used by the test suite (section 16: "Mock the LLM in normal tests. The
test suite must not require a live LLM provider.") and available for
local development without any real provider credentials.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ..exceptions import LLMMalformedResponseError, LLMProviderError, LLMTimeoutError
from .base import DiagnosisModel, LLMDiagnosisResponse


class MockDiagnosisModel(DiagnosisModel):
    """A configurable fake provider.

    Modes:
        "success"   -> returns `fixed_response` (or the result of
                       `response_fn(prompt_context)` if provided)
        "timeout"   -> always raises LLMTimeoutError
        "error"     -> always raises LLMProviderError
        "malformed" -> returns a payload that fails validation
        "flaky"     -> raises on the first `fail_times` calls, then
                       succeeds (used to test retry behavior)
    """

    name = "mock-provider"

    def __init__(
        self,
        mode: str = "success",
        fixed_response: Optional[LLMDiagnosisResponse] = None,
        response_fn: Optional[Callable[[Dict[str, Any]], LLMDiagnosisResponse]] = None,
        fail_times: int = 1,
    ):
        self.mode = mode
        self.fixed_response = fixed_response
        self.response_fn = response_fn
        self.fail_times = fail_times
        self.call_count = 0

    def generate_structured_diagnosis(
        self, prompt_context: Dict[str, Any], timeout_seconds: float
    ) -> LLMDiagnosisResponse:
        self.call_count += 1

        if self.mode == "timeout":
            raise LLMTimeoutError(
                f"Mock provider timed out after {timeout_seconds}s."
            )
        if self.mode == "error":
            raise LLMProviderError("Mock provider transport failure.")
        if self.mode == "malformed":
            raise LLMMalformedResponseError("Mock provider returned malformed output.")
        if self.mode == "flaky" and self.call_count <= self.fail_times:
            raise LLMProviderError("Mock provider transient failure.")

        if self.response_fn is not None:
            return self.response_fn(prompt_context)
        if self.fixed_response is not None:
            return self.fixed_response

        raise LLMMalformedResponseError(
            "MockDiagnosisModel in 'success' mode requires fixed_response or response_fn."
        )
