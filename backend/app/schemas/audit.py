from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class AuditItem(BaseModel):
    event_type: str
    actor_type: str
    created_at: datetime
    event_data_json: Optional[Dict[str, Any]] = None


class AuditListResponse(BaseModel):
    items: List[AuditItem]
