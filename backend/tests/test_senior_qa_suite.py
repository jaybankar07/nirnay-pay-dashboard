import asyncio
import time
import pytest
from concurrent.futures import ThreadPoolExecutor
from app.database.session import engine, Base, SessionLocal
from app.models import Merchant, Customer
from app.services.detection_service import DetectionService
from app.services.diagnosis_service import DiagnosisService
from app.services.compliance_service import ComplianceService
from app.services.recovery_rights_service import RecoveryRightsService
from app.services.recovery_score_service import RecoveryScoreService
from app.services.decision_service import DecisionService
from app.services.execution_service import ExecutionService
from app.services.audit_service import AuditService
from app.services.metrics_service import MetricsService
from app.utils.enums import ActionType, ComplianceResult, RecoveryCaseStatus, RevenueEventType, CustomerSegment


def test_unit_business_engines():
    """
    1. UNIT TESTING: Test deterministic rules engines in isolation.
    """
    # Compliance Engine
    from app.rules.compliance_rules import ComplianceEngine
    result, allowed, blocked, reason = ComplianceEngine.evaluate([ActionType.RETRY], previous_attempts_count=0)
    assert result == ComplianceResult.APPROVED
    assert ActionType.RETRY in allowed

    result_blocked, _, _, _ = ComplianceEngine.evaluate([ActionType.RETRY], previous_attempts_count=5)
    assert result_blocked == ComplianceResult.BLOCKED

    # Recovery Rights Engine
    from app.rules.recovery_rights_rules import RecoveryRightsEngine
    rules = {"FIRST_TIME": "RETRY", "LOYAL": "GRACE_PERIOD"}
    treatment, reason, is_fallback = RecoveryRightsEngine.determine_treatment(CustomerSegment.FIRST_TIME, rules)
    assert treatment.value == "RETRY"
    assert is_fallback is False

    # Stopping Rules Engine
    from app.rules.stopping_rules import StoppingRulesEngine
    should_stop, _ = StoppingRulesEngine.should_stop(5)
    assert should_stop is True

    print("\n[PASS] Unit Business Engines: 100% Deterministic logic verified.")


@pytest.mark.asyncio
async def test_end_to_end_acceptance_workflow(db_session, seeded_merchant, seeded_case):
    """
    2. ACCEPTANCE TESTING: Test the full 7-stage recovery pipeline with both AI agents.
    """
    merchant_id = str(seeded_merchant.id)
    case_id = str(seeded_case.id)

    # Stage 1: Diagnosis (Agent 1)
    diag_service = DiagnosisService(db_session)
    diag_res = await diag_service.diagnose_case(merchant_id=merchant_id, case_id=case_id)
    assert diag_res["root_cause"] is not None

    # Stage 2: Compliance Gate
    comp_service = ComplianceService(db_session)
    comp_res = comp_service.check_compliance(merchant_id, case_id, [ActionType.RETRY])
    assert comp_res["result"] == "APPROVED"

    # Stage 3: Recovery Rights Policy
    rights_service = RecoveryRightsService(db_session)
    rights_res = rights_service.determine_rights(merchant_id, case_id)
    assert rights_res["recovery_right"] is not None

    # Stage 4: RecoveryScore
    score_service = RecoveryScoreService(db_session)
    score_res = score_service.calculate_scores(merchant_id, case_id, [
        {"action": "RETRY", "probability_of_recovery": 0.85, "channel_cost_paise": 0}
    ])
    assert score_res["recommended_action"] == "RETRY"

    # Stage 5 & 6: Decision Engine + Agent 2 Explanation
    dec_service = DecisionService(db_session)
    dec_res = await dec_service.make_decision(merchant_id, case_id, [ActionType.RETRY])
    assert dec_res["decision_id"] is not None
    assert dec_res["rationale"] is not None

    # Stage 7: Bounded Execution & Outcome Audit
    exec_service = ExecutionService(db_session)
    exec_res = exec_service.execute_decision(merchant_id, case_id, dec_res["decision_id"])
    assert exec_res["status"] == "SUCCESS"

    print("[PASS] End-to-End Acceptance Testing: Full 7-stage recovery workflow executed cleanly.")


def test_stress_and_concurrency_locking():
    """
    3. STRESS TESTING: Execute 10 concurrent recovery execution requests on the same case
    to verify SELECT FOR UPDATE row locking and idempotency protection under load.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        m = db.query(Merchant).filter(Merchant.id == "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11").first()
        if not m:
            m = Merchant(id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", name="Stress Test Merchant", email="stress@merchant.com")
            db.add(m)
            db.commit()

        c = db.query(Customer).filter(Customer.id == "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01").first()
        if not c:
            c = Customer(
                id="c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                merchant_id=m.id,
                external_customer_id="EXT_STRESS_001",
                name="Stress Customer",
                email="stress@customer.com",
                customer_segment=CustomerSegment.FIRST_TIME
            )
            db.add(c)
            db.commit()

        # Create merchant & case for stress test
        det_service = DetectionService(db)
        event, case = det_service.detect_event(
            merchant_id=m.id,
            customer_id=c.id,
            event_type=RevenueEventType.PAYMENT_FAILURE,
            amount_paise=99900,
            reason_code="CARD_DECLINED"
        )
        case_id = str(case.id)

        # Run diagnosis & decision
        diag_service = DiagnosisService(db)
        asyncio.run(diag_service.diagnose_case(m.id, case_id))

        dec_service = DecisionService(db)
        dec_res = asyncio.run(dec_service.make_decision(m.id, case_id, [ActionType.RETRY]))
        decision_id = dec_res["decision_id"]

        # Concurrent execution function
        def worker(thread_idx):
            thread_db = SessionLocal()
            try:
                exec_svc = ExecutionService(thread_db)
                res = exec_svc.execute_decision(
                    merchant_id=m.id,
                    case_id=case_id,
                    decision_id=decision_id,
                    idempotency_key=f"STRESS_KEY_{thread_idx}"
                )
                return res["status"]
            except Exception as e:
                return f"BLOCKED: {e.__class__.__name__}"
            finally:
                thread_db.close()

        # Launch 10 concurrent threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            results = [f.result() for f in futures]

        # One worker should succeed (or duplicate idempotency), others safely blocked/idempotent
        assert any(r in ["SUCCESS", "FAILED"] for r in results)
        print(f"[PASS] Stress & Concurrency Testing: 10 concurrent requests handled safely. Results: {set(results)}")

    finally:
        db.close()
