from fastapi import APIRouter, Depends, Query, Header
from typing import Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.execution_service import ExecutionService
from app.schemas.execution import ExecuteRequest, ExecuteResponse
from app.schemas.common import StandardResponse

router = APIRouter(tags=["Execution"])


@router.post("/recovery-cases/{case_id}/execute", response_model=StandardResponse[ExecuteResponse])
def execute_recovery_action(
    case_id: str,
    request: ExecuteRequest,
    merchant_id: str = Query(...),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    service = ExecutionService(db)
    res = service.execute_decision(
        merchant_id=merchant_id,
        case_id=case_id,
        decision_id=request.decision_id,
        idempotency_key=idempotency_key,
        endpoint="/api/v1/recovery-cases/execute"
    )
    if "case_id" in res:
        res["case_id"] = str(res["case_id"])
    if "action_id" in res:
        res["action_id"] = str(res["action_id"])
    return StandardResponse(data=ExecuteResponse(**res))
