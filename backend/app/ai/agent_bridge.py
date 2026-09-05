import os
import time
import asyncio
from typing import Dict, Any, Tuple
from app.config import settings
from app.core.logging import logger

# Verified Package Imports — No sys.path hacks, No d:\ filesystem paths
from nirnay_revenue_diagnosis_agent.agent import RevenueDiagnosisAgent
from nirnay_revenue_diagnosis_agent.config import AgentConfig
from nirnay_revenue_diagnosis_agent.llm.ollama_provider import OllamaQwenDiagnosisProvider
from nirnay_recovery_communication_agent.agent import NirnayCommunicationAgent
from nirnay_recovery_communication_agent.llm.mock_provider import MockCommunicationModel
from nirnay_recovery_communication_agent.llm.grok_provider import GrokCommunicationProvider
from nirnay_recovery_communication_agent.llm.ollama_provider import OllamaQwenCommunicationProvider

SCENARIO_MAP = {
    "PAYMENT_FAILURE": "CARD_DECLINE",
    "RECURRING_BILLING_FAILURE": "SUBSCRIPTION_RENEWAL_FAILURE",
    "SUBSCRIPTION_CANCELLED": "OTHER",
    "INVOLUNTARY_CHURN_RISK": "OTHER"
}


class AgentBridge:
    def __init__(self, timeout_seconds: int = 3):
        self.timeout_seconds = timeout_seconds or settings.LLM_TIMEOUT_SECONDS
        
        # Initialize Agent 1 (Qwen 2.5)
        logger.info("Initializing RevenueDiagnosisAgent with Ollama Qwen 2.5:7B LLM Provider.")
        ollama_diag_provider = OllamaQwenDiagnosisProvider(default_timeout=float(self.timeout_seconds))
        agent_config = AgentConfig(llm_timeout_seconds=float(self.timeout_seconds))
        self.diagnosis_agent = RevenueDiagnosisAgent(llm=ollama_diag_provider, config=agent_config)

        # Initialize Agent 2 (Qwen/Grok)
        grok_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
        if grok_key:
            logger.info("Initializing NirnayCommunicationAgent with live xAI Grok LLM Provider.")
            comm_provider = GrokCommunicationProvider(api_key=grok_key)
            provider_name = "grok-beta"
        else:
            logger.info("Initializing NirnayCommunicationAgent with local Ollama Qwen 2.5:7B LLM Provider.")
            comm_provider = OllamaQwenCommunicationProvider(default_timeout=float(self.timeout_seconds))
            provider_name = "ollama-qwen2.5:7b"

        self.communication_agent = NirnayCommunicationAgent(llm=comm_provider, provider_name=provider_name)


    async def diagnose_case_with_agent(self, case_input: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Invokes RevenueDiagnosisAgent.
        Returns:
            (result_dict, metadata_dict)
        """
        start_time = time.time()
        fallback_used = False
        validation_status = "SUCCESS"
        retry_count = 0

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self.diagnosis_agent.diagnose, case_input),
                timeout=self.timeout_seconds
            )
            result_dict = result.to_dict() if hasattr(result, "to_dict") else dict(result)
            if result_dict.get("diagnosis_mode") == "FALLBACK":
                fallback_used = True
        except asyncio.TimeoutError:
            logger.warning("DiagnosisAgent timed out. Triggering fallback.")
            fallback_used = True
            validation_status = "TIMEOUT_FALLBACK"
            result_dict = {
                "root_cause": "unspecified_risk",
                "confidence": 0.5,
                "diagnosis_mode": "FALLBACK",
                "narrative": "DiagnosisAgent timed out. Defaulted to deterministic fallback."
            }
        except Exception as exc:
            logger.error(f"DiagnosisAgent failed: {str(exc)}. Triggering fallback.")
            fallback_used = True
            validation_status = f"ERROR_FALLBACK: {exc.__class__.__name__}"
            result_dict = {
                "root_cause": "unspecified_risk",
                "confidence": 0.5,
                "diagnosis_mode": "FALLBACK",
                "narrative": f"DiagnosisAgent error: {str(exc)}"
            }

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        metadata = {
            "agent_name": "RevenueDiagnosisAgent",
            "fallback_used": fallback_used,
            "validation_status": validation_status,
            "latency_ms": elapsed_ms,
            "retry_count": retry_count
        }

        return result_dict, metadata

    async def generate_communication_with_agent(self, comm_input: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Invokes NirnayCommunicationAgent.
        Returns:
            (communication_result_dict, metadata_dict)
        Authoritative Rule: selected_action is read-only.
        Any attempt by Agent 2 to alter selected_action is ignored.
        """
        start_time = time.time()
        fallback_used = False
        validation_status = "SUCCESS"
        retry_count = 0
        authoritative_action = comm_input.get("selected_action")

        # Map scenario_type to Agent 2 supported scenario enum if needed
        input_payload = dict(comm_input)
        raw_scenario = input_payload.get("scenario_type")
        if raw_scenario in SCENARIO_MAP:
            input_payload["scenario_type"] = SCENARIO_MAP[raw_scenario]

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self.communication_agent.generate, input_payload),
                timeout=self.timeout_seconds
            )
            res_dict = result.to_dict() if hasattr(result, "to_dict") else dict(result)

            # Ignore any selected_action alteration attempt
            if "selected_action" in res_dict and res_dict["selected_action"] != authoritative_action:
                logger.warning(f"CommunicationAgent attempted to alter action to {res_dict['selected_action']}. Reverting to authoritative {authoritative_action}.")
                res_dict["selected_action"] = authoritative_action

            if res_dict.get("fallback_used"):
                fallback_used = True

        except asyncio.TimeoutError:
            logger.warning("CommunicationAgent timed out. Using safe fallback template.")
            fallback_used = True
            validation_status = "TIMEOUT_FALLBACK"
            res_dict = {
                "explanation": f"Nirnay Pay executed {authoritative_action} in accordance with risk policy.",
                "customer_message": f"Your transaction requires attention. Action taken: {authoritative_action}.",
                "selected_action": authoritative_action
            }
        except Exception as exc:
            logger.error(f"CommunicationAgent failed: {str(exc)}. Using safe fallback template.")
            fallback_used = True
            validation_status = f"ERROR_FALLBACK: {exc.__class__.__name__}"
            res_dict = {
                "explanation": f"Nirnay Pay executed {authoritative_action} in accordance with risk policy.",
                "customer_message": f"Your transaction requires attention. Action taken: {authoritative_action}.",
                "selected_action": authoritative_action
            }

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        metadata = {
            "agent_name": "NirnayCommunicationAgent",
            "fallback_used": fallback_used,
            "validation_status": validation_status,
            "latency_ms": elapsed_ms,
            "retry_count": retry_count
        }

        return res_dict, metadata
