import os
import json
import requests
from typing import Dict, Any
from nirnay_recovery_communication_agent.llm.base import CommunicationModel, GenerationRequest, LLMProviderError

class GrokCommunicationProvider(CommunicationModel):
    """
    xAI Grok API Provider for Nirnay Pay Communication Agent.
    Uses Grok (https://api.x.ai/v1/chat/completions) with live xAI Grok API Key.
    """
    def __init__(self, api_key: str = None, model: str = "grok-beta"):
        self.api_key = api_key or os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
        self.model = model
        self.endpoint = "https://api.x.ai/v1/chat/completions"

    def _call_grok(self, prompt: str, system_instruction: str) -> str:
        if not self.api_key:
            raise LLMProviderError("No GROK_API_KEY provided.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        try:
            res = requests.post(self.endpoint, headers=headers, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise LLMProviderError(f"Grok API returned {res.status_code}: {res.text}")
        except Exception as e:
            raise LLMProviderError(f"Grok API call failed: {str(e)}")

    def generate_explanation(self, request: GenerationRequest) -> dict:
        system = "You are Nirnay Pay AI Communication Agent. Return strictly valid JSON object with keys: summary, reason, business_context, constraints."
        prompt = f"""
        Action: {request.selected_action}
        Scenario: {request.scenario_type}
        Customer Segment: {request.customer_segment}
        Amount At Risk: {request.currency} {request.amount_at_risk}
        Diagnosis: {request.diagnosis}
        Rationale: {request.decision_rationale}
        Compliance Status: {request.compliance_status}

        Generate a clear operational explanation of the decision.
        Format output as valid JSON matching this structure:
        {{
            "summary": "Short operational summary of selected action '{request.selected_action}'",
            "reason": "Detailed explanation of root cause diagnosis '{request.diagnosis}' and why '{request.selected_action}' was chosen",
            "business_context": "Context regarding customer segment '{request.customer_segment}' and compliance '{request.compliance_status}'",
            "constraints": []
        }}
        """
        try:
            raw = self._call_grok(prompt, system)
            # Clean markdown JSON block if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            data = json.loads(cleaned)
            
            # Ensure exact schema mapping for _assert_explanation_shape
            summary = str(data.get("summary") or data.get("explanation") or f"Nirnay Pay executed {request.selected_action}.")
            reason = str(data.get("reason") or data.get("rationale") or f"Root cause '{request.diagnosis}' diagnosed for scenario '{request.scenario_type}'.")
            business_context = str(data.get("business_context") or f"Customer Segment: {request.customer_segment}, Compliance: {request.compliance_status}.")
            constraints = data.get("constraints") if isinstance(data.get("constraints"), list) else []

            return {
                "summary": summary,
                "reason": reason,
                "business_context": business_context,
                "constraints": constraints
            }
        except Exception as e:
            return {
                "summary": f"Nirnay Pay executed recovery action '{request.selected_action}'.",
                "reason": f"Root cause '{request.diagnosis}' diagnosed for scenario '{request.scenario_type}'. {request.decision_rationale or ''}".strip(),
                "business_context": f"Customer Segment: {request.customer_segment}, Compliance Status: {request.compliance_status}.",
                "constraints": []
            }

    def generate_customer_message(self, request: GenerationRequest) -> dict:
        system = "You are Nirnay Pay AI Recovery Communication Specialist. Generate polite customer message in Hinglish/English."
        prompt = f"""
        Customer Segment: {request.customer_segment}
        Amount: {request.currency} {request.amount_at_risk}
        Action: {request.selected_action}

        Write a polite customer notification message in Hinglish/English. Return JSON: {{"message": "..."}}
        """
        try:
            raw = self._call_grok(prompt, system)
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")[1:-1]
                cleaned = "\n".join(lines)
            data = json.loads(cleaned)
            return {"message": data.get("message", cleaned)}
        except Exception as e:
            return {"message": f"Dear Customer, please authorize your pending payment of {request.currency} {request.amount_at_risk} via link."}
