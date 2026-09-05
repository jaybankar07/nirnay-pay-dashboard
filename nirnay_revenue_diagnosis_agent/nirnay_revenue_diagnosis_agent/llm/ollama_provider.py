"""
Ollama Qwen Provider for Agent 1 (Revenue Diagnosis Agent).
Connects to local Ollama instance (qwen2.5:7b) via HTTP API.
"""
from __future__ import annotations

import os
import json
import requests
from typing import Any, Dict

from .base import DiagnosisModel, LLMDiagnosisResponse
from .parsing import parse_llm_payload
from ..exceptions import LLMMalformedResponseError, LLMProviderError, LLMTimeoutError


class OllamaQwenDiagnosisProvider(DiagnosisModel):
    """
    Ollama Provider Adapter for Qwen 2.5:7B.
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
            or 15.0
        )

    def generate_structured_diagnosis(
        self, prompt_context: Dict[str, Any], timeout_seconds: float
    ) -> LLMDiagnosisResponse:
        endpoint = f"{self.base_url}/api/generate"
        effective_timeout = timeout_seconds or self.default_timeout
        scenario_type = prompt_context.get("scenario_type", "PAYMENT_FAILURE")
        system_instructions = prompt_context.get(
            "system_instructions",
            "You are a revenue-risk diagnosis assistant."
        )

        user_prompt = (
            f"Case details:\n{json.dumps(prompt_context, indent=2)}\n\n"
            f"Respond strictly in JSON matching allowed root causes for scenario '{scenario_type}'."
        )

        payload = {
            "model": self.model,
            "system": system_instructions,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=(1.0, effective_timeout)
            )
        except requests.exceptions.Timeout as exc:
            raise LLMTimeoutError(
                f"Ollama provider ({self.model}) timed out after {effective_timeout}s."
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
            raw_text = res_json.get("response", "")
            if not raw_text:
                raise LLMMalformedResponseError("Ollama returned empty response text.")
            
            parsed_data = json.loads(raw_text)
        except Exception as exc:
            raise LLMMalformedResponseError(
                f"Failed to parse JSON response from Ollama: {str(exc)}"
            ) from exc

        # Use authoritative parser to validate root_cause taxonomy, confidence range, evidence, etc.
        return parse_llm_payload(parsed_data, scenario_type)
