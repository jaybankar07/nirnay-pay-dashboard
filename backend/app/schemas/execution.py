from pydantic import BaseModel
from typing import Optional


class ExecuteRequest(BaseModel):
    decision_id: str


class ExecuteResponse(BaseModel):
    action_id: str
    status: str
    recovered: bool
    recovered_amount_paise: int
    action_result: Optional[dict] = None
