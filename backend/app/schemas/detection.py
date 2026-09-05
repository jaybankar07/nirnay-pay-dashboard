from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.utils.enums import RevenueEventType


class DetectionRequest(BaseModel):
    merchant_id: str
    customer_id: Optional[str] = None
    event_type: RevenueEventType
    amount_paise: int = Field(..., ge=0)
    reason_code: Optional[str] = None
    occurred_at: Optional[datetime] = None


class DetectionResponse(BaseModel):
    event_id: str
    case_id: str
    status: str
