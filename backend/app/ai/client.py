import json
import asyncio
from typing import Optional, Dict, Any, Tuple
from app.config import settings
from app.ai.schemas import DiagnosisOutputSchema, DecisionRationaleSchema
from app.ai.prompts import DIAGNOSIS_PROMPT_TEMPLATE, RATIONALE_PROMPT_TEMPLATE
from app.ai.fallback import DeterministicFallback
from app.utils.enums import DecisionMode, RevenueEventType, ActionType
from app.core.logging import logger


class AIClient:
    """
    DEPRECATED: Legacy mock AI client stub.
    Superseded by `app.ai.agent_bridge.AgentBridge`, which orchestrates
    `RevenueDiagnosisAgent` (Ollama Qwen 2.5:7B) and `NirnayCommunicationAgent` (xAI Grok).
    Kept for backward compatibility with legacy unit tests.
    """
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        self.api_key = api_key or settings.LLM_API_KEY
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS

    async def diagnose(
        self,
        support_notes: Optional[str] = None,
        customer_message: Optional[str] = None,
        reason_code: Optional[str] = None,
        scenario_type: RevenueEventType = RevenueEventType.PAYMENT_FAILURE
    ) -> Tuple[str, float, DecisionMode, str]:
        """
        Diagnoses revenue failure.
        Includes 1 retry, Pydantic schema validation, and deterministic fallback on failure.
        """
        if not support_notes and not customer_message:
            # Deterministic route directly if no unstructured text
            return DeterministicFallback.get_fallback_diagnosis(reason_code, scenario_type)

        prompt = DIAGNOSIS_PROMPT_TEMPLATE.format(
            support_notes=support_notes or "N/A",
            customer_message=customer_message or "N/A",
            reason_code=reason_code or "UNKNOWN"
        )

        for attempt in range(2):  # Try initial + 1 retry
            try:
                # In prototype mode or testing, if mock key, simulate bounded structured response
                if self.api_key == "mock-key-for-testing" or not self.api_key:
                    parsed = DiagnosisOutputSchema(
                        root_cause="temporary_payment_failure" if "card" in (support_notes or "").lower() else "unspecified_risk",
                        confidence=0.91,
                        rationale="Mock AI parsed support notes successfully."
                    )
                    return parsed.root_cause, parsed.confidence, DecisionMode.AI, parsed.rationale

                # Simulate/call external API with timeout
                raw_response = await self._call_llm_with_timeout(prompt)
                parsed_json = json.loads(raw_response)
                validated = DiagnosisOutputSchema(**parsed_json)
                return validated.root_cause, validated.confidence, DecisionMode.AI, validated.rationale
            except Exception as e:
                logger.warning(f"AI diagnosis attempt {attempt + 1} failed: {str(e)}")
                if attempt == 0:
                    await asyncio.sleep(0.5)

        logger.error("AI diagnosis failed after retry. Triggering deterministic fallback.")
        return DeterministicFallback.get_fallback_diagnosis(reason_code, scenario_type)

    async def generate_rationale(
        self,
        case_id: str,
        selected_action: ActionType,
        diagnosis: str,
        compliance_result: str,
        recovery_right: str,
        recovery_score: float
    ) -> Tuple[str, float, DecisionMode]:
        """
        Generates concise decision rationale. Supports retry and fallback.
        """
        prompt = RATIONALE_PROMPT_TEMPLATE.format(
            case_id=case_id,
            selected_action=selected_action.value,
            diagnosis=diagnosis or "N/A",
            compliance_result=compliance_result,
            recovery_right=recovery_right,
            recovery_score=recovery_score
        )

        for attempt in range(2):
            try:
                if self.api_key == "mock-key-for-testing" or not self.api_key:
                    validated = DecisionRationaleSchema(
                        rationale=f"Mock AI rationale: {recovery_right} policy and score {recovery_score} favor {selected_action.value}.",
                        confidence=0.89
                    )
                    return validated.rationale, validated.confidence, DecisionMode.AI

                raw_response = await self._call_llm_with_timeout(prompt)
                parsed_json = json.loads(raw_response)
                validated = DecisionRationaleSchema(**parsed_json)
                return validated.rationale, validated.confidence, DecisionMode.AI
            except Exception as e:
                logger.warning(f"AI rationale attempt {attempt + 1} failed: {str(e)}")
                if attempt == 0:
                    await asyncio.sleep(0.5)

        return DeterministicFallback.get_fallback_rationale(selected_action, recovery_right)

    async def _call_llm_with_timeout(self, prompt: str) -> str:
        # Placeholder for real HTTP call to LLM provider (e.g. OpenAI/Gemini)
        # Enforces timeout
        await asyncio.sleep(0.1)
        return json.dumps({
            "root_cause": "temporary_payment_failure",
            "confidence": 0.90,
            "rationale": "Parsed from LLM."
        })
