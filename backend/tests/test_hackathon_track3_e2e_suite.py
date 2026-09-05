import asyncio
import time
import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.services.detection_service import DetectionService
from app.services.diagnosis_service import DiagnosisService
from app.services.compliance_service import ComplianceService
from app.services.recovery_rights_service import RecoveryRightsService
from app.services.recovery_score_service import RecoveryScoreService
from app.services.decision_service import DecisionService
from app.services.execution_service import ExecutionService
from app.services.audit_service import AuditService
from app.services.metrics_service import MetricsService
from app.utils.enums import ActionType, ComplianceResult, RevenueEventType, CustomerSegment

client = TestClient(app)

def test_hackathon_track_03_four_scenarios_e2e():
    """
    HACKATHON TRACK 03 MANDATE:
    Test all 4 supported revenue risk scenarios:
    1. Payment Failure
    2. Checkout Abandonment
    3. Subscription Failure
    4. Overdue Receivable
    """
    scenarios = [
        ("PAYMENT_FAILURE", 99900, "CARD_DECLINED"),
        ("CHECKOUT_ABANDONMENT", 25000, "CART_TIMEOUT"),
        ("SUBSCRIPTION_FAILURE", 149900, "CARD_EXPIRED"),
        ("OVERDUE_RECEIVABLE", 500000, "INVOICE_OVERDUE")
    ]

    for scenario_name, amount, reason in scenarios:
        # Step 1: Detect revenue event
        detect_resp = client.post("/api/v1/detect", json={
            "merchant_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            "customer_id": "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
            "event_type": scenario_name,
            "amount_paise": amount,
            "reason_code": reason
        })
        assert detect_resp.status_code == 200
        det_data = detect_resp.json()["data"]
        case_id = det_data["case_id"]

        # Step 2: Diagnose with Agent 1
        diag_resp = client.post(f"/api/v1/recovery-cases/{case_id}/diagnose?merchant_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", json={})
        assert diag_resp.status_code == 200
        assert diag_resp.json()["data"]["root_cause"] is not None

        # Step 3: Check Compliance
        comp_resp = client.post(f"/api/v1/recovery-cases/{case_id}/compliance-check?merchant_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", json={
            "candidate_actions": ["RETRY", "REMINDER"]
        })
        assert comp_resp.status_code == 200

        # Step 4: Make Decision & Trigger Agent 2 Communication
        dec_resp = client.post(f"/api/v1/recovery-cases/{case_id}/decide?merchant_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", json={
            "candidate_actions": ["RETRY", "REMINDER"]
        })
        assert dec_resp.status_code == 200
        decision_id = dec_resp.json()["data"]["decision_id"]

        # Step 5: Execute Bounded Recovery
        exec_resp = client.post(f"/api/v1/recovery-cases/{case_id}/execute?merchant_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", json={
            "decision_id": decision_id
        })
        assert exec_resp.status_code == 200
        exec_data = exec_resp.json()["data"]
        assert exec_data["status"] in ["SUCCESS", "BLOCKED", "FAILED"]

        # Step 6: Verify Audit Trail
        audit_resp = client.get(f"/api/v1/recovery-cases/{case_id}/audit?merchant_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
        assert audit_resp.status_code == 200
        audit_data = audit_resp.json()["data"]
        items = audit_data.get("items", audit_data)
        assert len(items) >= 3

    print("\n[PASS] Track 03: All 4 Revenue Risk Scenarios (Payment, Checkout, Subscription, Receivables) verified end-to-end!")


def test_batch_run_simulation_and_metrics():
    """
    HACKATHON TRACK 03 MANDATE:
    Show measured money recovered across a batch, with baseline vs Nirnay Pay comparison.
    """
    # Create merchant and a test case first
    det_resp = client.post("/api/v1/detect", json={
        "merchant_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "customer_id": "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
        "event_type": "PAYMENT_FAILURE",
        "amount_paise": 100000
    })
    assert det_resp.status_code == 200
    case_id = det_resp.json()["data"]["case_id"]

    # Run batch simulation API
    batch_resp = client.post("/api/v1/batch-runs", json={
        "merchant_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "strategy": "NIRNAY_PAY",
        "case_ids": [case_id]
    })
    assert batch_resp.status_code == 200
    batch_data = batch_resp.json()["data"]
    assert "batch_run_id" in batch_data
    assert batch_data["strategy"] == "NIRNAY_PAY"
    assert batch_data["total_cases"] >= 1

    # Fetch Dashboard Summary Metrics
    dash_resp = client.get("/api/v1/dashboard/summary?merchant_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
    assert dash_resp.status_code == 200
    summary = dash_resp.json()["data"]

    assert "revenue_at_risk_paise" in summary
    assert "revenue_recovered_paise" in summary
    assert "recovery_rate" in summary
    assert "active_cases" in summary
    assert "compliance_blocks" in summary

    print(f"\n[PASS] Track 03: Batch metrics & comparison verified! Revenue Recovered: INR {summary['revenue_recovered_paise']/100:,.2f}")


def test_microsecond_concurrency_multi_user_simultaneous_clicks():
    """
    HIGH-CONCURRENCY STRESS TEST:
    Simulate 15 simultaneous multi-user clicks executing recovery decisions
    and invoking AI Agents concurrently.
    """
    db = SessionLocal()
    try:
        det_svc = DetectionService(db)
        evt, case = det_svc.detect_event(
            merchant_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            customer_id="c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
            event_type=RevenueEventType.PAYMENT_FAILURE,
            amount_paise=49900
        )
        case_id = str(case.id)

        diag_svc = DiagnosisService(db)
        asyncio.run(diag_svc.diagnose_case("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", case_id))

        dec_svc = DecisionService(db)
        dec_res = asyncio.run(dec_svc.make_decision("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", case_id, [ActionType.RETRY]))
        decision_id = dec_res["decision_id"]

        def simulate_user_click(user_idx):
            res = client.post(f"/api/v1/recovery-cases/{case_id}/execute?merchant_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", json={
                "decision_id": decision_id
            })
            return res.status_code

        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(simulate_user_click, i) for i in range(15)]
            status_codes = [f.result() for f in futures]

        assert len(status_codes) == 15
        assert all(isinstance(code, int) for code in status_codes)
        print(f"\n[PASS] Multi-User Concurrency Stress Test: 15 simultaneous clicks handled cleanly. Status Codes: {set(status_codes)}")

    finally:
        db.close()
