"""
Nirnay Pay Synthetic Evaluation Package.
Export key evaluation classes.
"""
from app.evaluation.models import (
    EvaluationCase,
    GroundTruth,
    DatasetSplit,
    ScenarioType,
    EvaluationOutcome,
    FailureCategory,
    CaseEvaluationTrace,
    StrategyRunResult,
    EvaluationComparisonResult
)
from app.evaluation.dataset import generate_synthetic_dataset, get_split_datasets
from app.evaluation.environment import OutcomeEnvironment
from app.evaluation.baseline_strategy import ConventionalBaselineStrategy
from app.evaluation.evaluator import EvaluationEngine

__all__ = [
    "EvaluationCase",
    "GroundTruth",
    "DatasetSplit",
    "ScenarioType",
    "EvaluationOutcome",
    "FailureCategory",
    "CaseEvaluationTrace",
    "StrategyRunResult",
    "EvaluationComparisonResult",
    "generate_synthetic_dataset",
    "get_split_datasets",
    "OutcomeEnvironment",
    "ConventionalBaselineStrategy",
    "EvaluationEngine",
]
