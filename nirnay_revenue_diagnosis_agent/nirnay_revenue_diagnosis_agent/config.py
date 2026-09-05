"""
Agent configuration (section 14: timeouts/retries).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    #: Per-attempt LLM timeout, in seconds.
    llm_timeout_seconds: float = 3.0

    #: Maximum number of retries after the first attempt fails (i.e. total
    #: attempts = 1 + max_retries). Spec default is 1 retry.
    max_retries: int = 0

    #: Base backoff, in seconds, before the first retry. Doubles per retry
    #: (exponential backoff), capped by `max_backoff_seconds`.
    base_backoff_seconds: float = 0.25
    max_backoff_seconds: float = 2.0

    #: Rule-engine confidence at/above which a `decisive` rule outcome is
    #: trusted outright and the LLM stage is skipped entirely (RULE mode).
    rule_decisive_confidence_threshold: float = 0.75

    #: If True, the agent will call the LLM even when the rule engine was
    #: decisive but confidence is below 1.0, to see if unstructured text
    #: corroborates or adds nuance -- off by default to keep RULE-mode
    #: cases fast and fully deterministic.
    always_consult_llm: bool = False
