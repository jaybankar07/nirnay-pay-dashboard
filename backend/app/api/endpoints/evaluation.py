"""
FastAPI Evaluation Router for Nirnay Pay Track 03.
Provides POST /api/v1/evaluation/run for reproducible synthetic held-out evaluation runs.
"""
from fastapi import APIRouter, Query
from app.evaluation.models import DatasetSplit, EvaluationComparisonResult
from app.evaluation.evaluator import EvaluationEngine

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.post("/run", response_model=EvaluationComparisonResult)
def run_synthetic_evaluation(
    dataset: DatasetSplit = Query(DatasetSplit.HELD_OUT, description="Dataset split: HELD_OUT or DEVELOPMENT"),
    seed: int = Query(42, description="Random generator seed for reproducible evaluation")
):
    """
    Executes a same-world synthetic evaluation comparing Conventional Baseline vs Nirnay RecoveryOS.
    Uses real DecisionService & ExecutionService in an isolated context.
    """
    engine = EvaluationEngine(seed=seed)
    result = engine.run_evaluation(split=dataset, include_ai_ablation=True)
    return result
