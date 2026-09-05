from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.batch_simulation_service import BatchSimulationService
from app.schemas.batch import BatchRunRequest, BatchRunResponse
from app.schemas.common import StandardResponse

router = APIRouter(tags=["Batch Simulation"])


@router.post("/batch-runs", response_model=StandardResponse[BatchRunResponse])
def run_batch_simulation(request: BatchRunRequest, db: Session = Depends(get_db)):
    service = BatchSimulationService(db)
    res = service.run_batch_simulation(
        merchant_id=request.merchant_id,
        strategy=request.strategy,
        case_ids=request.case_ids
    )
    if "batch_run_id" in res:
        res["batch_run_id"] = str(res["batch_run_id"])
    if "batch_id" in res:
        res["batch_id"] = str(res["batch_id"])
    return StandardResponse(data=BatchRunResponse(**res))
