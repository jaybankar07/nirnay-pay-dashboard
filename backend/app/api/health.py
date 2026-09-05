"""
Health and Readiness Endpoints for Nirnay Pay (RecoveryOS).
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.kill_switch import KillSwitchState
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Liveness probe: returns HTTP 200 if process is running."""
    return {
        "status": "UP",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "kill_switch": KillSwitchState.get_status()
    }


from sqlalchemy import text


@router.get("/readiness")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe: verifies database connectivity and core system health."""
    db_healthy = False
    try:
        # Simple DB connectivity check
        db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception:
        db_healthy = False

    is_ready = db_healthy

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "READY" if is_ready else "NOT_READY",
            "components": {
                "database": "UP" if db_healthy else "DOWN",
                "kill_switch": KillSwitchState.get_status()
            }
        }
    )
