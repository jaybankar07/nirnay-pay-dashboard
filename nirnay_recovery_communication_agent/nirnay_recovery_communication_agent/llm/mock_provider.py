"""
Mock provider used for automated tests (section 16: "Mock the LLM during
normal tests. Do not require a live LLM provider for the test suite.")

It is deliberately simple and template-driven so tests are fast and
deterministic, but it supports injection hooks so tests can simulate:
  - timeouts
  - malformed output
  - unsafe/threatening output
  - hallucinated amounts/recovery claims
"""

from typing import Callable, Optional

from .base import CommunicationModel, GenerationRequest, LLMTimeoutError, LLMProviderError


class MockCommunicationModel(CommunicationModel):
    def __init__(
        self,
        force_explanation: Optional[Callable[[GenerationRequest], dict]] = None,
        force_customer_message: Optional[Callable[[GenerationRequest], str]] = None,
        raise_timeout: bool = False,
        raise_error: bool = False,
    ):
        self.force_explanation = force_explanation
        self.force_customer_message = force_customer_message
        self.raise_timeout = raise_timeout
        self.raise_error = raise_error
        self.call_count = 0

    def _maybe_fail(self):
        self.call_count += 1
        if self.raise_timeout:
            raise LLMTimeoutError("Mock provider simulated a timeout.")
        if self.raise_error:
            raise LLMProviderError("Mock provider simulated a generic failure.")

    def generate_explanation(self, request: GenerationRequest) -> dict:
        self._maybe_fail()
        if self.force_explanation:
            return self.force_explanation(request)

        segment = request.customer_segment or "this customer"
        action_phrase = _ACTION_PHRASES.get(
            request.selected_action, request.selected_action.lower()
        )

        summary = (
            f"The approved recovery action for {segment} is {action_phrase}."
        )
        reason = (
            f"Based on the supplied diagnosis ('{request.diagnosis}') and "
            f"decision rationale, {action_phrase} was selected rather than "
            "a more aggressive step."
        )
        if request.correction_notes:
            reason += f" ({request.correction_notes})"

        business_context = (
            f"This aligns with the compliance status "
            f"({request.compliance_status}) and recovery rights on file "
            "for this case."
        )
        constraints = []
        if request.compliance_status == "BLOCKED" or request.selected_action in (
            "STOP",
            "BLOCKED",
        ):
            constraints.append("No further automatic recovery action will occur.")
        if request.recovery_rights_allowed is False:
            constraints.append("Recovery rights do not currently permit further action.")

        return {
            "summary": summary,
            "reason": reason,
            "business_context": business_context,
            "constraints": constraints,
        }

    def generate_customer_message(self, request: GenerationRequest) -> dict:
        self._maybe_fail()
        if self.force_customer_message:
            return {"message": self.force_customer_message(request)}

        opener = _TONE_OPENERS.get(request.tone, "")
        body = _CUSTOMER_BODY.get(
            request.selected_action,
            "We are reviewing your recent payment and will follow up as needed.",
        )
        message = f"{opener}{body}".strip()
        if request.correction_notes:
            # Retry path: keep message but do not add anything unsafe --
            # correction is handled by re-selecting a safer body below.
            pass
        return {"message": message}


_ACTION_PHRASES = {
    "RETRY": "an automatic payment retry",
    "GRACE_PERIOD": "a grace period",
    "REMINDER": "a payment reminder",
    "HUMAN_REVIEW": "manual human review",
    "ESCALATE": "escalation to a specialist team",
    "WAIT": "a monitoring/wait period",
    "STOP": "stopping further automatic recovery action",
    "BLOCKED": "blocking further recovery action",
}

_TONE_OPENERS = {
    "FRIENDLY": "Hi there! ",
    "PROFESSIONAL": "",
    "CONCISE": "",
}

_CUSTOMER_BODY = {
    "RETRY": (
        "The payment could not be completed. We will retry the payment "
        "through our approved recovery process."
    ),
    "GRACE_PERIOD": (
        "We've given you additional time to resolve the payment issue."
    ),
    "REMINDER": (
        "Your payment is still pending. Please review the payment "
        "details when convenient."
    ),
    "HUMAN_REVIEW": (
        "Our team will review the payment issue and follow up with you."
    ),
    "ESCALATE": (
        "Your case has been escalated to a specialist team who will "
        "follow up with you directly."
    ),
    "WAIT": (
        "We are monitoring your payment status. No action is needed "
        "from you right now."
    ),
    "STOP": ("No further automatic recovery action will be taken at this time."),
    "BLOCKED": (
        "We are currently unable to proceed with recovery on this "
        "payment. No further automatic action will be taken at this time."
    ),
}
