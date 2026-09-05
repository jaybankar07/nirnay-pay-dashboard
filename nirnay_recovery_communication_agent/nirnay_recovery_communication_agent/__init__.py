"""
Nirnay Recovery Communication & Explanation Agent
==================================================

This package is an EXPLANATION / COMMUNICATION layer only.

It receives an ALREADY APPROVED recovery decision (produced by external
deterministic systems: the decision engine, compliance engine, recovery
rights engine, RecoveryScore engine) and turns it into clear, safe,
policy-compliant human communication.

It never decides:
    - whether recovery should happen
    - which action should be taken
    - whether an action is compliant
    - RecoveryScore
    - Recovery Rights

Public surface:
    NirnayCommunicationAgent   -- the agent class
    RecoveryCaseInput          -- validated input schema
    CommunicationResult        -- validated output schema (dict-like)
    ValidationError            -- structured input/consistency errors
    MockCommunicationModel     -- provider-independent test LLM
"""

from .agent import NirnayCommunicationAgent
from .models import (
    RecoveryCaseInput,
    CommunicationPurpose,
    SelectedAction,
    Tone,
)
from .exceptions import (
    NirnayAgentError,
    InputValidationError,
    DecisionConsistencyError,
    IncompleteContextError,
)
from .llm.mock_provider import MockCommunicationModel

__all__ = [
    "NirnayCommunicationAgent",
    "RecoveryCaseInput",
    "CommunicationPurpose",
    "SelectedAction",
    "Tone",
    "NirnayAgentError",
    "InputValidationError",
    "DecisionConsistencyError",
    "IncompleteContextError",
    "MockCommunicationModel",
]

__version__ = "1.0.0"
