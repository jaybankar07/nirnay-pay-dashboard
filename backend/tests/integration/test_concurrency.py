import pytest
import asyncio
from app.models.decision import Decision
from app.services.execution_service import ExecutionService
from app.utils.enums import ComplianceResult, RecoveryRightTreatment, ActionType, DecisionMode


def test_concurrency_execution_locking(db_session, seeded_merchant, seeded_case):
    decision = Decision(
        recovery_case_id=seeded_case.id,
        compliance_result=ComplianceResult.APPROVED,
        recovery_right=RecoveryRightTreatment.RETRY,
        recovery_score=80.0,
        selected_action=ActionType.RETRY,
        decision_mode=DecisionMode.RULE
    )
    db_session.add(decision)
    db_session.commit()

    service = ExecutionService(db_session)
    res = service.execute_decision(seeded_merchant.id, seeded_case.id, decision.id)
    assert res["status"] == "SUCCESS"
