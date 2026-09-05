"""
Admin and Operations API Router for Nirnay Pay (RecoveryOS).
Provides Emergency Kill Switch management and operational governance.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.kill_switch import KillSwitchState
from app.core.security import SecurityContext

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


class KillSwitchRequest(BaseModel):
    action: str  # "ACTIVATE" or "DEACTIVATE"
    scope: str   # "GLOBAL", "TENANT", "SCENARIO"
    tenant_id: Optional[str] = None
    scenario: Optional[str] = None
    reason: Optional[str] = "Operational safety control toggled"
    user_role: Optional[str] = "ADMIN"


@router.get("/kill-switch")
def get_kill_switch_status():
    """Returns current emergency kill switch status across all scopes."""
    return {
        "success": True,
        "data": KillSwitchState.get_status()
    }


@router.post("/kill-switch")
def update_kill_switch(payload: KillSwitchRequest):
    """Updates emergency kill switch configuration."""
    SecurityContext.check_permission(payload.user_role, "admin:killswitch")

    action = payload.action.upper()
    scope = payload.scope.upper()
    activate = (action == "ACTIVATE")

    if scope == "GLOBAL":
        KillSwitchState.set_global_stop(activate)
    elif scope == "TENANT":
        if not payload.tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required for TENANT scope kill switch")
        KillSwitchState.set_tenant_stop(payload.tenant_id, activate)
    elif scope == "SCENARIO":
        if not payload.scenario:
            raise HTTPException(status_code=400, detail="scenario required for SCENARIO scope kill switch")
        KillSwitchState.set_scenario_stop(payload.scenario, activate)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid kill switch scope '{payload.scope}'. Must be GLOBAL, TENANT, or SCENARIO.")

    return {
        "success": True,
        "message": f"Kill switch {action}D for scope {scope}.",
        "data": KillSwitchState.get_status()
    }
