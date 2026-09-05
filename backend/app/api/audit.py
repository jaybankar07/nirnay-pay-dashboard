from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.audit_service import AuditService
from app.services.recovery_case_service import RecoveryCaseService
from app.schemas.audit import AuditListResponse, AuditItem
from app.schemas.common import StandardResponse

router = APIRouter(tags=["Audit"])


@router.get("/recovery-cases/{case_id}/audit", response_model=StandardResponse[AuditListResponse])
def get_case_audit_trail(
    case_id: str,
    merchant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    # Verify case ownership first (enforce merchant isolation)
    case_service = RecoveryCaseService(db)
    case_service.get_case(merchant_id, case_id)

    audit_service = AuditService(db)
    events = audit_service.get_audit_trail(case_id)
    items = [
        AuditItem(
            event_type=e.event_type.value if hasattr(e.event_type, 'value') else str(e.event_type),
            actor_type=e.actor_type.value if hasattr(e.actor_type, 'value') else str(e.actor_type),
            created_at=e.created_at,
            event_data_json=e.event_data_json
        )
        for e in events
    ]
    return StandardResponse(data=AuditListResponse(items=items))
