"""
Ollama Qwen Provider for Agent 2 (Communication Agent).
Connects to local Ollama instance (qwen2.5:7b) via HTTP API.
"""
from __future__ import annotations

import os
import json
import requests
from typing import Any, Dict

from .base import CommunicationModel, GenerationRequest, LLMProviderError, LLMTimeoutError


class OllamaQwenCommunicationProvider(CommunicationModel):
    """
    Ollama Provider Adapter for Qwen 2.5:7B (Communication Agent).
    """

    name = "ollama-qwen2.5:7b"

    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        default_timeout: float = None,
    ):
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or "http://127.0.0.1:11434"
        ).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or "qwen2.5:7b"
        self.default_timeout = float(
            default_timeout
            or os.getenv("OLLAMA_TIMEOUT")
            or 3.0
        )

    def generate_explanation(self, request: GenerationRequest) -> dict:
        endpoint = f"{self.base_url}/api/generate"
        system = (
            "You are Nirnay Pay AI Communication Specialist. Return strictly a JSON object "
            "with keys: 'summary' (str), 'reason' (str), 'business_context' (str), 'constraints' (list of str). "
            "Do not include markdown code block formatting or extra commentary."
        )

        user_prompt = f"""
        Action: {request.selected_action}
        Scenario: {request.scenario_type}
        Customer Segment: {request.customer_segment}
        Amount At Risk: {request.currency} {request.amount_at_risk}
        Diagnosis: {request.diagnosis}
        Rationale: {request.decision_rationale}
        Compliance Status: {request.compliance_status}

        Generate operational explanation JSON matching:
        {{
            "summary": "Operational summary of selected action '{request.selected_action}'",
            "reason": "Detailed business explanation of diagnosis '{request.diagnosis}'",
            "business_context": "Context on customer segment '{request.customer_segment}' and compliance status '{request.compliance_status}'",
            "constraints": []
        }}
        """

        payload = {
            "model": self.model,
            "system": system,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.3}
        }

        try:
            response = requests.post(
                endpoint, json=payload, timeout=(1.0, self.default_timeout)
            )
        except requests.exceptions.Timeout as exc:
            raise LLMTimeoutError(
                f"Ollama provider ({self.model}) timed out after {self.default_timeout}s."
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise LLMProviderError(
                f"Ollama connection error to {endpoint}: {str(exc)}"
            ) from exc

        if response.status_code != 200:
            raise LLMProviderError(
                f"Ollama API returned HTTP status {response.status_code}: {response.text}"
            )

        try:
            res_json = response.json()
            raw_text = res_json.get("response", "").strip()
            if not raw_text:
                raise LLMProviderError("Ollama returned empty response text.")
            
            # Clean markdown JSON block if present
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()

            data = json.loads(raw_text)
            if not isinstance(data, dict):
                raise LLMProviderError("Ollama response is not a JSON object.")
            
            return data
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                f"Failed to parse JSON response from Ollama: {str(exc)}"
            ) from exc

    def generate_customer_message(self, request: GenerationRequest) -> dict:
        endpoint = f"{self.base_url}/api/generate"
        system = (
            "You are Nirnay Pay AI Recovery Communication Specialist. "
            "Write a polite customer notification message. Return JSON: {\"message\": \"...\"}"
        )

        user_prompt = f"""
        Customer Segment: {request.customer_segment}
        Amount: {request.currency} {request.amount_at_risk}
        Action: {request.selected_action}

        Write a polite customer notification message in Hinglish/English. Return JSON: {{"message": "..."}}
        """

        payload = {
            "model": self.model,
            "system": system,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.3}
        }

        try:
            response = requests.post(
                endpoint, json=payload, timeout=(1.0, self.default_timeout)
            )
            if response.status_code == 200:
                raw_text = response.json().get("response", "").strip()
                if raw_text.startswith("```"):
                    lines = raw_text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    raw_text = "\n".join(lines).strip()
                data = json.loads(raw_text)
                return {"message": data.get("message", raw_text)}
            else:
                raise LLMProviderError(f"Ollama API returned HTTP {response.status_code}")
        except Exception as exc:
            raise LLMProviderError(f"Ollama customer message generation failed: {str(exc)}")
