from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.compliance_service import ComplianceService
from app.schemas.compliance import ComplianceCheckRequest, ComplianceCheckResponse
from app.schemas.common import StandardResponse

router = APIRouter(tags=["Compliance"])


@router.post("/recovery-cases/{case_id}/compliance-check", response_model=StandardResponse[ComplianceCheckResponse])
def check_compliance(
    case_id: str,
    request: ComplianceCheckRequest,
    merchant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = ComplianceService(db)
    res = service.check_compliance(merchant_id, case_id, request.candidate_actions)
    if "case_id" in res:
        res["case_id"] = str(res["case_id"])
    res["status"] = res.get("result", "APPROVED")
    res["blocking_reason"] = res.get("reason", None)
    return StandardResponse(data=ComplianceCheckResponse(**res))
