"""
Optional real provider backed by the Anthropic API.

This is NOT used by the automated test suite (which uses
MockCommunicationModel per section 16). It is provided so the agent can
be wired to a live model in production without changing `agent.py`.

Requires the `anthropic` package and an API key available via the
ANTHROPIC_API_KEY environment variable. Import is deferred so the rest
of the package has no hard dependency on the `anthropic` SDK.
"""

import json
import os

from .base import CommunicationModel, GenerationRequest, LLMProviderError, LLMTimeoutError

_SYSTEM_PROMPT = """You are a communication-generation component inside a \
regulated fintech recovery system. You NEVER decide recovery actions -- \
you only explain or communicate a decision that has ALREADY been made \
and approved by other systems. You must use ONLY the facts given to you \
in the request. Never invent amounts, dates, deadlines, penalties, \
legal consequences, or claims of payment success/recovery unless they \
are explicitly present in the request. Never use threatening, urgent, \
or manipulative language. Respond ONLY with a single minified JSON \
object matching the requested shape -- no markdown, no commentary."""


class AnthropicCommunicationModel(CommunicationModel):
    def __init__(self, model: str = "claude-sonnet-4-6", timeout_seconds: float = 15.0):
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:
                raise LLMProviderError(
                    "The 'anthropic' package is required for "
                    "AnthropicCommunicationModel."
                ) from e
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise LLMProviderError(
                    "ANTHROPIC_API_KEY is not set in the environment."
                )
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def _call(self, user_prompt: str) -> dict:
        client = self._get_client()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=600,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
                timeout=self.timeout_seconds,
            )
        except Exception as e:  # noqa: BLE001 - normalize any SDK exception
            name = type(e).__name__.lower()
            if "timeout" in name:
                raise LLMTimeoutError(str(e)) from e
            raise LLMProviderError(str(e)) from e

        text_parts = [
            block.text for block in response.content if getattr(block, "type", "") == "text"
        ]
        raw_text = "".join(text_parts).strip()
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise LLMProviderError(f"Model did not return valid JSON: {e}") from e

    def generate_explanation(self, request: GenerationRequest) -> dict:
        prompt = (
            "Given this already-approved recovery decision context:\n"
            f"{json.dumps(request.__dict__)}\n\n"
            "Return a minified JSON object with exactly these keys: "
            'summary, reason, business_context, constraints (a list of '
            "strings). Ground every statement only in the fields above."
        )
        return self._call(prompt)

    def generate_customer_message(self, request: GenerationRequest) -> dict:
        prompt = (
            "Given this already-approved recovery decision context:\n"
            f"{json.dumps(request.__dict__)}\n\n"
            "Return a minified JSON object with exactly one key: message "
            "(a string). Write a short, clear, non-threatening customer "
            "message that matches selected_action exactly, in the "
            "requested tone and language. Ground every statement only in "
            "the fields above."
        )
        return self._call(prompt)
