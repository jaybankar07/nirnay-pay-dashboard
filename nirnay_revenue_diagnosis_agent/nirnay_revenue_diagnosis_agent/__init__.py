"""
Nirnay Revenue Diagnosis Agent
==============================

A standalone, provider-independent AI agent that answers exactly one
question: "why is this revenue at risk?"

It does not decide what recovery action to take, does not determine
compliance, does not calculate RecoveryScore, and does not execute
anything -- see the module docstring in `nirnay_agent.agent` for the full
boundary statement.

Typical usage
-------------

    from nirnay_agent import RevenueDiagnosisAgent

    agent = RevenueDiagnosisAgent()  # rule-engine only, no LLM required
    result = agent.diagnose({
        "recovery_case_id": "case_123",
        "scenario_type": "PAYMENT_FAILURE",
        "decline_code": "INSUFFICIENT_FUNDS",
        "successful_payment_count": 12,
        "failed_payment_count": 0,
    })
    print(result.to_dict())

To use an LLM for ambiguous cases, implement `DiagnosisModel` for your
provider of choice and pass it in:

    from nirnay_agent import RevenueDiagnosisAgent
    from nirnay_agent.llm import DiagnosisModel

    class MyProvider(DiagnosisModel):
        name = "my-llm"
        def generate_structured_diagnosis(self, prompt_context, timeout_seconds):
            ...

    agent = RevenueDiagnosisAgent(llm=MyProvider())
"""
from .agent import RevenueDiagnosisAgent
from .config import AgentConfig
from .enums import DiagnosisMode, ScenarioType
from .exceptions import (
    DiagnosisAgentError,
    InputValidationError,
    LLMMalformedResponseError,
    LLMProviderError,
    LLMTimeoutError,
    OutputValidationError,
)
from .models import DiagnosisResult, Evidence, RecoveryCaseInput

__version__ = "1.0.0"

__all__ = [
    "RevenueDiagnosisAgent",
    "AgentConfig",
    "ScenarioType",
    "DiagnosisMode",
    "RecoveryCaseInput",
    "DiagnosisResult",
    "Evidence",
    "DiagnosisAgentError",
    "InputValidationError",
    "OutputValidationError",
    "LLMProviderError",
    "LLMTimeoutError",
    "LLMMalformedResponseError",
]
