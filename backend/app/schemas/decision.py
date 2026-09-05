from pydantic import BaseModel
from typing import List, Optional, Dict
from app.utils.enums import ActionType


class DecideRequest(BaseModel):
    candidate_actions: List[ActionType]


class DecideResponse(BaseModel):
    decision_id: str
    compliance_result: str
    recovery_right: str
    recovery_score: float
    selected_action: str
    mode: Optional[str] = "RULE"
    decision_mode: str
    rationale: str
    why_selected: Optional[str] = None
    why_rejected: Optional[Dict[str, str]] = None

