from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.decision_service import DecisionService
from app.schemas.decision import DecideRequest, DecideResponse
from app.schemas.common import StandardResponse

router = APIRouter(tags=["Decisions"])


@router.post("/recovery-cases/{case_id}/decide", response_model=StandardResponse[DecideResponse])
async def decide_action(
    case_id: str,
    request: DecideRequest,
    merchant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = DecisionService(db)
    res = await service.make_decision(
        merchant_id=merchant_id,
        case_id=case_id,
        candidate_actions=request.candidate_actions
    )
    if "case_id" in res:
        res["case_id"] = str(res["case_id"])
    if "decision_id" in res:
        res["decision_id"] = str(res["decision_id"])
    res["mode"] = res.get("decision_mode", "RULE")
    return StandardResponse(data=DecideResponse(**res))
