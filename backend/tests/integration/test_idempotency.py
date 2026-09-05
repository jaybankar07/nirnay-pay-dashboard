import pytest
from app.models.decision import Decision
from app.services.execution_service import ExecutionService
from app.utils.enums import ComplianceResult, RecoveryRightTreatment, ActionType, DecisionMode


def test_idempotency_key_prevents_duplicate_execution(db_session, seeded_merchant, seeded_case):
    decision = Decision(
        recovery_case_id=seeded_case.id,
        compliance_result=ComplianceResult.APPROVED,
        recovery_right=RecoveryRightTreatment.RETRY,
        recovery_score=50.0,
        selected_action=ActionType.RETRY,
        decision_mode=DecisionMode.RULE
    )
    db_session.add(decision)
    db_session.commit()

    service = ExecutionService(db_session)
    idempotency_key = "IDEM_KEY_UNIQUE_12345"

    # First Execution
    res_1 = service.execute_decision(
        merchant_id=seeded_merchant.id,
        case_id=seeded_case.id,
        decision_id=decision.id,
        idempotency_key=idempotency_key
    )

    # Second Execution with SAME key
    res_2 = service.execute_decision(
        merchant_id=seeded_merchant.id,
        case_id=seeded_case.id,
        decision_id=decision.id,
        idempotency_key=idempotency_key
    )

    assert res_1["action_id"] == res_2["action_id"]
    assert res_1["recovered_amount_paise"] == res_2["recovered_amount_paise"]
