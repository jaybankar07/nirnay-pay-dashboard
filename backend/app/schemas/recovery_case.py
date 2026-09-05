from pydantic import BaseModel, Field
from typing import Optional, List
from app.utils.enums import RevenueEventType, RecoveryCaseStatus


class CreateCaseRequest(BaseModel):
    merchant_id: str
    customer_id: Optional[str] = None
    revenue_event_id: str
    scenario_type: RevenueEventType
    amount_at_risk_paise: int = Field(..., ge=0)


class RecoveryCaseResponse(BaseModel):
    id: str
    case_id: Optional[str] = None
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = "Customer"
    customer_segment: Optional[str] = "REGULAR"
    status: str
    scenario_type: str
    scenario: Optional[str] = None
    amount_at_risk_paise: int
    amount_at_risk: Optional[float] = 0.0
    root_cause: Optional[str] = None
    diagnosis_confidence: Optional[float] = None
    diagnosis: Optional[dict] = None
    compliance: Optional[dict] = None
    recovery_rights: Optional[dict] = None
    score: Optional[dict] = None
    decision: Optional[dict] = None
    action_result: Optional[dict] = None
    is_executable: Optional[bool] = True
    executable_action: Optional[str] = "RETRY"
    created_at: Optional[str] = None


class CaseListResponse(BaseModel):
    items: List[RecoveryCaseResponse]
    total: int
    limit: int
    offset: int
