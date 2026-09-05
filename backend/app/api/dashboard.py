from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.metrics_service import MetricsService
from app.services.recovery_case_service import RecoveryCaseService
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.recovery_case import CaseListResponse, RecoveryCaseResponse
from app.schemas.common import StandardResponse
from app.utils.enums import RecoveryCaseStatus, RevenueEventType

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/summary", response_model=StandardResponse[DashboardSummaryResponse])
def get_dashboard_summary(
    merchant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = MetricsService(db)
    metrics = service.get_dashboard_summary(merchant_id)
    return StandardResponse(data=DashboardSummaryResponse(**metrics))


@router.get("/dashboard/cases", response_model=StandardResponse[CaseListResponse])
def get_dashboard_cases(
    merchant_id: str = Query(...),
    status: Optional[RecoveryCaseStatus] = Query(None),
    scenario_type: Optional[RevenueEventType] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    service = RecoveryCaseService(db)
    items, total = service.list_cases(merchant_id, status, scenario_type, limit, offset)
    case_responses = [
        RecoveryCaseResponse(
            id=str(c.id),
            status=c.status.value if hasattr(c.status, 'value') else str(c.status),
            scenario_type=c.scenario_type.value if hasattr(c.scenario_type, 'value') else str(c.scenario_type),
            amount_at_risk_paise=c.amount_at_risk_paise,
            root_cause=c.root_cause,
            diagnosis_confidence=c.diagnosis_confidence
        )
        for c in items
    ]
    return StandardResponse(
        data=CaseListResponse(
            items=case_responses,
            total=total,
            limit=limit,
            offset=offset
        )
    )
