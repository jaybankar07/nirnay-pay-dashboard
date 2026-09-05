from pydantic import BaseModel, Field
from typing import List, Optional, Any
from app.utils.enums import ActionType


class ActionCandidateItem(BaseModel):
    action: ActionType
    probability_of_recovery: float = Field(0.5, ge=0.0, le=1.0)
    channel_cost_paise: int = Field(0, ge=0)
    compliance_penalty_paise: int = Field(0, ge=0)


class ScoreRequest(BaseModel):
    actions: Optional[List[ActionCandidateItem]] = None
    candidate_actions: Optional[List[Any]] = None


class ActionScoreItem(BaseModel):
    action: str
    score: float


class ScoreResponse(BaseModel):
    scores: List[ActionScoreItem]
    recommended_action: str
    expected_recovery_probability: Optional[float] = 0.8
    amount_at_risk: Optional[float] = 0.0
    channel_cost: Optional[float] = 0.0
    compliance_penalty: Optional[float] = 0.0
    score: Optional[float] = 0.0

