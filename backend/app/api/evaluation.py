"""
FastAPI Evaluation Router for Nirnay Pay Track 03.
Provides POST /api/v1/evaluation/run for reproducible synthetic held-out evaluation runs.
"""
from fastapi import APIRouter, Query
from app.evaluation.models import DatasetSplit, EvaluationComparisonResult
from app.evaluation.evaluator import EvaluationEngine

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

_EVAL_CACHE = {}

@router.post("/run", response_model=EvaluationComparisonResult)
def run_synthetic_evaluation(
    dataset: DatasetSplit = Query(DatasetSplit.HELD_OUT, description="Dataset split: HELD_OUT or DEVELOPMENT"),
    seed: int = Query(42, description="Random generator seed for reproducible evaluation")
):
    """
    Executes a same-world synthetic evaluation comparing Conventional Baseline vs Nirnay RecoveryOS.
    Uses real DecisionService & ExecutionService in an isolated context.
    Caches evaluation results in memory for instant dashboard retrieval.
    """
    cache_key = (dataset.value if hasattr(dataset, 'value') else str(dataset), seed)
    if cache_key in _EVAL_CACHE:
        return _EVAL_CACHE[cache_key]

    engine = EvaluationEngine(seed=seed)
    result = engine.run_evaluation(split=dataset, include_ai_ablation=True)
    _EVAL_CACHE[cache_key] = result
    return result
