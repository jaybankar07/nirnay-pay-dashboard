"""
Provider-independent LLM abstraction (section 12).

Any concrete provider (Anthropic, OpenAI, local model, mock/test double)
implements this interface. The agent only ever talks to
`CommunicationModel`, never to a specific vendor SDK, so providers can
be swapped without touching agent logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class LLMTimeoutError(Exception):
    """Raised by a provider when a call does not complete in time."""


class LLMProviderError(Exception):
    """Raised by a provider for any other generation failure."""


@dataclass
class GenerationRequest:
    """Everything a provider needs to produce text -- and NOTHING more.
    Only fields explicitly present on the validated input are included,
    so a provider (or its prompt) cannot reach for facts that were never
    supplied (section 11 - No-Hallucination Rule)."""

    purpose: str  # CommunicationPurpose value
    selected_action: str
    scenario_type: str
    customer_segment: str
    amount_at_risk: float
    currency: str
    diagnosis: str
    diagnosis_confidence: float
    decision_rationale: str
    compliance_status: str
    recovery_rights_allowed: bool
    recovery_outcome_status: str
    tone: str
    language: str
    correction_notes: str = None  # populated only on retry, section 13


class CommunicationModel(ABC):
    """Abstract provider-independent interface.

    Concrete providers must implement both generation methods. A single
    `generate_explanation` is reused for both DECISION_EXPLANATION and
    MERCHANT_EXPLANATION purposes (they differ by audience/framing,
    encoded in the request), while `generate_customer_message` is used
    for CUSTOMER_RECOVERY_MESSAGE.
    """

    @abstractmethod
    def generate_explanation(self, request: GenerationRequest) -> dict:
        """Returns a dict with explanation-shaped fields (raw, pre-safety-check)."""
        raise NotImplementedError

    @abstractmethod
    def generate_customer_message(self, request: GenerationRequest) -> dict:
        """Returns a dict with {'message': str} (raw, pre-safety-check)."""
        raise NotImplementedError
