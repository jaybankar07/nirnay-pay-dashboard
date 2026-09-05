from fastapi import APIRouter
from app.api import (
    health,
    merchants,
    recovery_cases,
    detection,
    diagnosis,
    compliance,
    recovery_rights,
    scoring,
    decisions,
    execution,
    audit,
    dashboard,
    batch_runs,
    evaluation,
    admin,
    metrics,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(admin.router)
api_router.include_router(metrics.router)
api_router.include_router(merchants.router)
api_router.include_router(recovery_cases.router)
api_router.include_router(detection.router)
api_router.include_router(diagnosis.router)
api_router.include_router(compliance.router)
api_router.include_router(recovery_rights.router)
api_router.include_router(scoring.router)
api_router.include_router(decisions.router)
api_router.include_router(execution.router)
api_router.include_router(audit.router)
api_router.include_router(dashboard.router)
api_router.include_router(batch_runs.router)
api_router.include_router(evaluation.router)

