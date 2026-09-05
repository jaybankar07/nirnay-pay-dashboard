from pydantic import BaseModel
from typing import Optional
from app.utils.enums import CustomerSegment


class RecoveryRightsRequest(BaseModel):
    customer_segment: Optional[CustomerSegment] = None


class RecoveryRightsResponse(BaseModel):
    recovery_right: str
    recommended_treatment: Optional[str] = "RETRY"
    reason: str
    business_reason: Optional[str] = None
    customer_segment: Optional[str] = "FIRST_TIME"
