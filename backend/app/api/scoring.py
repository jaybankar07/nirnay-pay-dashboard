from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.recovery_score_service import RecoveryScoreService
from app.schemas.scoring import ScoreRequest, ScoreResponse
from app.schemas.common import StandardResponse

router = APIRouter(tags=["Scoring"])


@router.post("/recovery-cases/{case_id}/score", response_model=StandardResponse[ScoreResponse])
def calculate_score(
    case_id: str,
    request: ScoreRequest,
    merchant_id: str = Query(...),
    db: Session = Depends(get_db)
):
    service = RecoveryScoreService(db)
    raw_candidates = []
    if request.actions:
        raw_candidates = [c.model_dump() for c in request.actions]
    elif request.candidate_actions:
        raw_candidates = [
            {"action": str(a), "probability_of_recovery": 0.8, "channel_cost_paise": 0}
            for a in request.candidate_actions
        ]
    else:
        raw_candidates = [
            {"action": "RETRY", "probability_of_recovery": 0.8, "channel_cost_paise": 0},
            {"action": "REMINDER", "probability_of_recovery": 0.6, "channel_cost_paise": 500}
        ]
    res = service.calculate_scores(merchant_id, case_id, raw_candidates)
    if "case_id" in res:
        res["case_id"] = str(res["case_id"])
    return StandardResponse(data=ScoreResponse(**res))
