from pydantic import BaseModel
from typing import List
from app.utils.enums import BatchStrategy


class BatchRunRequest(BaseModel):
    merchant_id: str
    strategy: BatchStrategy
    case_ids: List[str]


class BatchRunResponse(BaseModel):
    batch_run_id: str
    strategy: str
    total_cases: int
    total_at_risk_paise: int
    recovered_paise: int
    recovery_rate: float
    compliance_blocks: int
    baseline_recovered_paise: int = 0
    nirnay_recovered_paise: int = 0
    incremental_recovered_paise: int = 0
    baseline_recovery_rate: float = 0.0
    nirnay_recovery_rate: float = 0.0
    action_difference_count: int = 0
    outcome_difference_count: int = 0
