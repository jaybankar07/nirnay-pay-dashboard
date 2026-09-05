import pytest
from app.services.execution_service import ExecutionService
from app.models.decision import Decision
from app.utils.enums import ComplianceResult, RecoveryRightTreatment, ActionType, DecisionMode
from app.core.exceptions import ExecutionBlockedError


def test_execution_service_success(db_session, seeded_merchant, seeded_case):
    # Create decision for case
    decision = Decision(
        recovery_case_id=seeded_case.id,
        compliance_result=ComplianceResult.APPROVED,
        recovery_right=RecoveryRightTreatment.RETRY,
        recovery_score=100.0,
        selected_action=ActionType.RETRY,
        decision_mode=DecisionMode.RULE
    )
    db_session.add(decision)
    db_session.commit()

    service = ExecutionService(db_session)
    res = service.execute_decision(
        merchant_id=seeded_merchant.id,
        case_id=seeded_case.id,
        decision_id=decision.id
    )

    assert res["status"] == "SUCCESS"
    assert res["recovered"] is True
    assert res["recovered_amount_paise"] == seeded_case.amount_at_risk_paise


def test_execution_service_blocks_stop_action(db_session, seeded_merchant, seeded_case):
    decision = Decision(
        recovery_case_id=seeded_case.id,
        compliance_result=ComplianceResult.APPROVED,
        recovery_right=RecoveryRightTreatment.STOP,
        recovery_score=0.0,
        selected_action=ActionType.STOP,
        decision_mode=DecisionMode.RULE
    )
    db_session.add(decision)
    db_session.commit()

    service = ExecutionService(db_session)
    with pytest.raises(ExecutionBlockedError):
        service.execute_decision(
            merchant_id=seeded_merchant.id,
            case_id=seeded_case.id,
            decision_id=decision.id
        )
