from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.diagnosis_service import DiagnosisService
from app.schemas.diagnosis import DiagnoseRequest, DiagnoseResponse
from app.schemas.common import StandardResponse

router = APIRouter(tags=["Diagnosis"])


@router.post("/recovery-cases/{case_id}/diagnose", response_model=StandardResponse[DiagnoseResponse])
async def diagnose_case(
    case_id: str,
    request: DiagnoseRequest,
    merchant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = DiagnosisService(db)
    res = await service.diagnose_case(
        merchant_id=merchant_id,
        case_id=case_id,
        support_notes=request.support_notes,
        customer_message=request.customer_message
    )
    if "case_id" in res:
        res["case_id"] = str(res["case_id"])
    return StandardResponse(data=DiagnoseResponse(**res))
