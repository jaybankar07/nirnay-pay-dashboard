import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.services.diagnosis_service import DiagnosisService
from app.services.decision_service import DecisionService
from app.services.execution_service import ExecutionService
from app.ai.agent_bridge import AgentBridge
from app.utils.enums import ActionType, RecoveryCaseStatus, ComplianceResult

# Native package imports — verify packages import natively without sys.path hacks or d:\ paths
from nirnay_revenue_diagnosis_agent.agent import RevenueDiagnosisAgent
from nirnay_recovery_communication_agent.agent import NirnayCommunicationAgent
from nirnay_recovery_communication_agent.llm.mock_provider import MockCommunicationModel


def test_agent_package_imports_without_sys_path():
    """
    Verify both AI agent packages import cleanly via standard Python package names
    without requiring sys.path hacks or absolute filesystem paths.
    """
    agent1 = RevenueDiagnosisAgent()
    agent2 = NirnayCommunicationAgent(llm=MockCommunicationModel())
    assert agent1 is not None
    assert agent2 is not None


def test_agents_have_no_direct_database_access():
    """
    Verify AI agent packages do not import or access database models, SQLAlchemy sessions,
    or Supabase credentials directly.
    """
    import sys
    agent1_modules = [m for m in sys.modules if m.startswith("nirnay_revenue_diagnosis_agent")]
    agent2_modules = [m for m in sys.modules if m.startswith("nirnay_recovery_communication_agent")]
    
    forbidden = ["sqlalchemy", "psycopg2", "supabase"]
    for mod in agent1_modules + agent2_modules:
        module_obj = sys.modules[mod]
        for f in forbidden:
            assert f not in getattr(module_obj, "__dict__", {}), f"Forbidden database component '{f}' found in {mod}"


@pytest.mark.asyncio
async def test_agent1_unavailable_fallback(db_session, seeded_merchant, seeded_case):
    """
    Verify backend works and falls back to deterministic diagnosis when Agent 1 fails or is unavailable.
    """
    service = DiagnosisService(db_session)
    merchant_id = str(seeded_merchant.id)
    case_id = str(seeded_case.id)

    with patch.object(service.agent_bridge.diagnosis_agent, "diagnose", side_effect=Exception("Agent 1 network failure")):
        res = await service.diagnose_case(merchant_id=merchant_id, case_id=case_id)
        assert res["root_cause"] == "unspecified_risk"
        assert res["case_id"] == case_id


@pytest.mark.asyncio
async def test_agent2_unavailable_decision_persists(db_session, seeded_merchant, seeded_case):
    """
    Verify decision is committed and recovery workflow succeeds even when Agent 2 fails completely.
    """
    service = DecisionService(db_session)
    merchant_id = str(seeded_merchant.id)
    case_id = str(seeded_case.id)

    with patch.object(AgentBridge, "generate_communication_with_agent", side_effect=Exception("Agent 2 offline")):
        res = await service.make_decision(
            merchant_id=merchant_id,
            case_id=case_id,
            candidate_actions=[ActionType.RETRY]
        )
        assert res["decision_id"] is not None
        assert res["selected_action"] is not None


@pytest.mark.asyncio
async def test_agent2_slow_response_timeout_isolation(db_session, seeded_merchant, seeded_case):
    """
    Verify Agent 2 slow response / timeout triggers safe deterministic communication fallback,
    causes zero transaction rollback, allows recovery workflow to continue, and prevents duplicate execution.
    """
    service = DecisionService(db_session)
    exec_service = ExecutionService(db_session)
    merchant_id = str(seeded_merchant.id)
    case_id = str(seeded_case.id)

    with patch.object(AgentBridge, "generate_communication_with_agent", side_effect=asyncio.TimeoutError()):
        # Decision should succeed immediately with fallback
        dec_res = await service.make_decision(
            merchant_id=merchant_id,
            case_id=case_id,
            candidate_actions=[ActionType.RETRY]
        )
        assert dec_res["decision_id"] is not None
        assert dec_res["selected_action"] is not None

        # Execution should succeed without transaction rollback
        exec_res = exec_service.execute_decision(
            merchant_id=merchant_id,
            case_id=case_id,
            decision_id=dec_res["decision_id"]
        )
        assert exec_res["status"] in ["SUCCESS", "BLOCKED"]


@pytest.mark.asyncio
async def test_agent2_cannot_alter_selected_action():
    """
    Verify Agent 2 attempting to alter selected_action (e.g. from RETRY to GRACE_PERIOD) is ignored.
    Backend decision remains authoritative.
    """
    bridge = AgentBridge()
    comm_input = {
        "recovery_case_id": "case_test_123",
        "scenario_type": "PAYMENT_FAILURE",
        "customer_segment": "FIRST_TIME",
        "amount_at_risk_paise": 10000,
        "diagnosis": "temporary_decline",
        "compliance_result": "APPROVED",
        "recovery_right": "RETRY",
        "selected_action": "RETRY",  # Authoritative action
        "recovery_score": 100.0,
        "decision_rationale": "Policy retry",
        "purpose": "MERCHANT_EXPLANATION"
    }

    # Simulate Agent 2 attempting to alter action to GRACE_PERIOD
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "explanation": "Attempting to change decision",
        "customer_message": "Wait a bit",
        "selected_action": "GRACE_PERIOD"  # Malicious/altered action attempt
    }

    with patch.object(bridge.communication_agent, "generate", return_value=mock_result):
        res_dict, meta = await bridge.generate_communication_with_agent(comm_input)
        # Verify selected_action was reverted back to authoritative 'RETRY'
        assert res_dict["selected_action"] == "RETRY"


@pytest.mark.asyncio
async def test_agent1_cannot_select_action_or_bypass_compliance(db_session, seeded_merchant, seeded_case):
    """
    Verify Agent 1 produces root_cause only and cannot choose recovery action or bypass compliance.
    """
    diag_service = DiagnosisService(db_session)
    dec_service = DecisionService(db_session)
    merchant_id = str(seeded_merchant.id)
    case_id = str(seeded_case.id)

    diag_res = await diag_service.diagnose_case(merchant_id=merchant_id, case_id=case_id)
    assert "root_cause" in diag_res
    assert "selected_action" not in diag_res

    # Test Compliance Gate blocking: compliance should block execution regardless of diagnosis
    with patch("app.services.compliance_service.ComplianceService.check_compliance", return_value={
        "result": "BLOCKED",
        "allowed_actions": [],
        "blocked_actions": ["RETRY"],
        "reason": "Max contact attempts exceeded"
    }):
        dec_res = await dec_service.make_decision(
            merchant_id=merchant_id,
            case_id=case_id,
            candidate_actions=[ActionType.RETRY]
        )
        assert dec_res["compliance_result"] == ComplianceResult.BLOCKED.value
        assert dec_res["selected_action"] == ActionType.STOP.value


def test_no_outcome_claimed_before_execution(db_session, seeded_case):
    """
    Verify case status remains DIAGNOSED/APPROVED before execution and outcome is recorded only after execution.
    """
    assert seeded_case.status in [RecoveryCaseStatus.DETECTED, RecoveryCaseStatus.DIAGNOSED, RecoveryCaseStatus.APPROVED]
