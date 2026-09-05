from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.recovery_rights_service import RecoveryRightsService
from app.schemas.recovery_rights import RecoveryRightsRequest, RecoveryRightsResponse
from app.schemas.common import StandardResponse

router = APIRouter(tags=["Recovery Rights"])


@router.post("/recovery-cases/{case_id}/recovery-rights", response_model=StandardResponse[RecoveryRightsResponse])
def apply_recovery_rights(
    case_id: str,
    request: RecoveryRightsRequest,
    merchant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = RecoveryRightsService(db)
    res = service.determine_rights(
        merchant_id=merchant_id,
        case_id=case_id,
        customer_segment=request.customer_segment
    )
    if "case_id" in res:
        res["case_id"] = str(res["case_id"])
    res["recommended_treatment"] = res.get("recovery_right", "RETRY")
    res["business_reason"] = res.get("reason", "Merchant policy applied.")
    return StandardResponse(data=RecoveryRightsResponse(**res))
