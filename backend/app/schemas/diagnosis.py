from pydantic import BaseModel
from typing import Optional


class DiagnoseRequest(BaseModel):
    support_notes: Optional[str] = None
    customer_message: Optional[str] = None


class DiagnoseResponse(BaseModel):
    case_id: str
    root_cause: str
    confidence: float
    mode: str
    rationale: str
