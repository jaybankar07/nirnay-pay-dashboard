"""
Provider-independent LLM abstraction (section 12).

The agent must not be tightly coupled to any single LLM vendor. Any
concrete provider (Anthropic, OpenAI, a local model, etc.) plugs in by
implementing `DiagnosisModel`. The agent only ever talks to this
interface, and every response coming back through it is validated before
use (`nirnay_agent.llm.parsing`).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LLMDiagnosisResponse:
    """The raw (not-yet-validated) shape a provider adapter should return
    from `generate_structured_diagnosis`. Providers are expected to map
    their own response format into this shape."""

    root_cause: str
    confidence: float
    diagnosis: str
    evidence: List[Dict[str, str]] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    raw_provider_payload: Optional[Dict[str, Any]] = None


class DiagnosisModel(ABC):
    """Abstract interface every LLM provider adapter must implement.

    Concrete interface (as sketched in the spec):

        DiagnosisModel
            |
            v
        generate_structured_diagnosis(input) -> LLMDiagnosisResponse
    """

    #: Human-readable provider/model identifier used only for telemetry.
    name: str = "unnamed-provider"

    @abstractmethod
    def generate_structured_diagnosis(
        self, prompt_context: Dict[str, Any], timeout_seconds: float
    ) -> LLMDiagnosisResponse:
        """Synchronously request a structured diagnosis from the provider.

        Implementations should raise `nirnay_agent.exceptions.LLMTimeoutError`
        on timeout and `nirnay_agent.exceptions.LLMMalformedResponseError`
        (or let a parsing error propagate) on a response that cannot be
        parsed into `LLMDiagnosisResponse`. Any other provider/transport
        failure should be raised as `nirnay_agent.exceptions.LLMProviderError`.
        """
        raise NotImplementedError

    async def generate_structured_diagnosis_async(
        self, prompt_context: Dict[str, Any], timeout_seconds: float
    ) -> LLMDiagnosisResponse:
        """Async variant. Default implementation delegates to the sync
        method so providers only need to implement one path; providers
        with native async transports should override this directly."""
        return self.generate_structured_diagnosis(prompt_context, timeout_seconds)
