"""
Evaluation Domain Models for Nirnay Pay Track 03.
Provides immutable, additive schema for synthetic evaluation, ground truth, and case-level traceability.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class DatasetSplit(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    HELD_OUT = "HELD_OUT"


class ScenarioType(str, Enum):
    PAYMENT_FAILURE = "PAYMENT_FAILURE"
    CHECKOUT_ABANDONMENT = "CHECKOUT_ABANDONMENT"
    SUBSCRIPTION_FAILURE = "SUBSCRIPTION_FAILURE"
    OVERDUE_RECEIVABLE = "OVERDUE_RECEIVABLE"


class EvaluationOutcome(str, Enum):
    RECOVERED = "RECOVERED"
    NOT_RECOVERED = "NOT_RECOVERED"
    BLOCKED = "BLOCKED"
    STOPPED = "STOPPED"
    ESCALATED = "ESCALATED"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"


class FailureCategory(str, Enum):
    NONE = "NONE"
    DIAGNOSIS_FAILURE = "DIAGNOSIS_FAILURE"
    NO_RECOVERY_OPPORTUNITY = "NO_RECOVERY_OPPORTUNITY"
    COMPLIANCE_BLOCK = "COMPLIANCE_BLOCK"
    RIGHTS_RESTRICTION = "RIGHTS_RESTRICTION"
    INEFFECTIVE_INTERVENTION = "INEFFECTIVE_INTERVENTION"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"
    STOP_RULE_TRIGGERED = "STOP_RULE_TRIGGERED"
    LLM_FALLBACK = "LLM_FALLBACK"


class GroundTruth(BaseModel):
    """
    Objective ground truth conditions for a synthetic evaluation case.
    Determines outcome deterministically when an action is executed in OutcomeEnvironment.
    """
    recovery_opportunity: bool
    effective_actions: List[str]  # e.g. ["RETRY", "RETRY_SMART_SCHEDULE"]
    prohibited_actions: List[str] = Field(default_factory=list) # e.g. ["DISCOUNT_OFFER"]
    max_recoverable_amount_paise: int
    wasted_cost_paise: int = 0
    failure_reason: Optional[str] = None


class EvaluationCase(BaseModel):
    """
    Individual synthetic evaluation case.
    """
    case_id: str
    merchant_id: str
    customer_id: str
    split: DatasetSplit
    scenario_type: ScenarioType
    amount_at_risk_paise: int
    currency: str = "INR"
    failed_payment_count: int = 1
    successful_payment_count: int = 0
    customer_segment: str = "STANDARD"
    tenure_days: int = 30
    reason_code: Optional[str] = None
    unstructured_signals: Dict[str, Any] = Field(default_factory=dict)
    ground_truth: GroundTruth


class CaseEvaluationTrace(BaseModel):
    """
    Full case-level traceability record linking input -> decision -> execution -> outcome -> audit.
    """
    case_id: str
    scenario_type: ScenarioType
    strategy_name: str  # "BASELINE", "NIRNAY_RULES", "NIRNAY_QWEN"
    amount_at_risk_paise: int
    diagnosis_root_cause: Optional[str] = None
    compliance_status: str
    recovery_rights_allowed: bool
    recovery_score: float = 0.0
    selected_action: str
    simulated_execution_status: str
    recovered_amount_paise: int
    outcome: EvaluationOutcome
    failure_category: FailureCategory
    audit_event_id: Optional[str] = None


class StrategyRunResult(BaseModel):
    strategy_name: str
    dataset: DatasetSplit
    total_cases: int
    total_at_risk_paise: int
    recovered_paise: int
    recovery_rate: float
    decision_counts: Dict[str, int]
    outcome_counts: Dict[str, int]
    failure_counts: Dict[str, int]
    traces: List[CaseEvaluationTrace]


class EvaluationComparisonResult(BaseModel):
    evaluation_run_id: str
    evaluation_type: str = "SYNTHETIC_HELD_OUT"
    dataset: DatasetSplit
    generator_seed: int
    timestamp: str
    total_cases: int
    total_at_risk_paise: int
    
    baseline: StrategyRunResult
    nirnay: StrategyRunResult
    
    # Incremental Metrics (unclipped, can be positive or negative)
    incremental_recovered_paise: int
    relative_uplift_pct: float
    
    # AI Ablation (Optional)
    nirnay_rules_only: Optional[StrategyRunResult] = None
