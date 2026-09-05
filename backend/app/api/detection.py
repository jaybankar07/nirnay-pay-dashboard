from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.detection_service import DetectionService
from app.schemas.detection import DetectionRequest, DetectionResponse
from app.schemas.common import StandardResponse

router = APIRouter(tags=["Detection"])


@router.post("/detect", response_model=StandardResponse[DetectionResponse])
def detect_revenue_event(request: DetectionRequest, db: Session = Depends(get_db)):
    service = DetectionService(db)
    event, case = service.detect_event(
        merchant_id=request.merchant_id,
        customer_id=request.customer_id,
        event_type=request.event_type,
        amount_paise=request.amount_paise,
        reason_code=request.reason_code,
        occurred_at=request.occurred_at
    )
    return StandardResponse(
        data=DetectionResponse(
            event_id=str(event.id),
            case_id=str(case.id),
            status=case.status.value if hasattr(case.status, 'value') else str(case.status)
        )
    )
