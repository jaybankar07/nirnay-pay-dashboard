from pydantic import BaseModel
from typing import List, Optional
from app.utils.enums import ActionType


class ComplianceCheckRequest(BaseModel):
    candidate_actions: List[ActionType]


class ComplianceCheckResponse(BaseModel):
    result: str
    status: Optional[str] = "APPROVED"
    allowed_actions: List[str]
    blocked_actions: List[str]
    reason: Optional[str] = None
    blocking_reason: Optional[str] = None
