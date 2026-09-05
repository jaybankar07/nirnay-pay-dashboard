import os
import sys
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.main import app
from app.database.session import get_db
from app.models import Merchant, Customer, RevenueEvent, RecoveryCase, RecoveryPolicy
from app.utils.enums import CustomerSegment, RevenueEventType, RecoveryCaseStatus

# Connection URL to Live Supabase PostgreSQL Pooler
SUPABASE_URL = os.getenv(
    "SUPABASE_DATABASE_URL",
    "postgresql://postgres.lelvvtepzxvohhxmiram:2124UDSM2077@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres"
)


@pytest.fixture(scope="module")
def supabase_engine():
    try:
        engine = create_engine(SUPABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            pass
        yield engine
        engine.dispose()
    except Exception as e:
        pytest.skip(f"Supabase database host unreachable: {e}")


@pytest.fixture(scope="module")
def supabase_db(supabase_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=supabase_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def supabase_client(supabase_db):
    def _get_supabase_db():
        yield supabase_db

    app.dependency_overrides[get_db] = _get_supabase_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_backend_with_supabase_live_database(supabase_client, supabase_db):
    """
    Integrated End-to-End Test verifying FastAPI Backend running against
    live Supabase PostgreSQL production database.
    """
    merchant_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    customer_id = "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01"

    print("\n" + "=" * 80)
    print("PART 2: FASTAPI BACKEND + SUPABASE POSTGRESQL INTEGRATED VERIFICATION")
    print("=" * 80)

    # 1. Health Check
    res1 = supabase_client.get("/api/v1/health")
    assert res1.status_code == 200
    assert res1.json()["status"] in ("UP", "healthy")
    print("[PASS] 1. Backend Health Check on Supabase: PASS")

    # 2. Get Merchant from Supabase
    res2 = supabase_client.get(f"/api/v1/merchants/{merchant_id}")
    assert res2.status_code == 200
    assert res2.json()["data"]["name"] == "Apex SaaS Technologies"
    print("[PASS] 2. Fetch Merchant from Supabase: PASS")

    # 3. Detect Revenue Event -> Create Case on Supabase
    res3 = supabase_client.post("/api/v1/detect", json={
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "event_type": "PAYMENT_FAILURE",
        "amount_paise": 149900,
        "reason_code": "CARD_DECLINED"
    })
    assert res3.status_code == 200
    case_id = res3.json()["data"]["case_id"]
    print(f"[PASS] 3. Detect Revenue Event (Created Supabase Case {case_id}): PASS")

    # 4. Diagnose Case via Backend DiagnosisService
    res4 = supabase_client.post(f"/api/v1/recovery-cases/{case_id}/diagnose?merchant_id={merchant_id}", json={
        "support_notes": "Customer mentions expired debit card."
    })
    assert res4.status_code == 200
    assert res4.json()["data"]["root_cause"] is not None
    print("[PASS] 4. Case Diagnosis on Supabase: PASS")

    # 5. Compliance Gate Check
    res5 = supabase_client.post(f"/api/v1/recovery-cases/{case_id}/compliance-check?merchant_id={merchant_id}", json={
        "candidate_actions": ["RETRY", "REMINDER"]
    })
    assert res5.status_code == 200
    assert res5.json()["data"]["result"] == "APPROVED"
    print("[PASS] 5. Compliance Gate Check on Supabase: PASS")

    # 6. Recovery Rights Policy Evaluation from Supabase
    res6 = supabase_client.post(f"/api/v1/recovery-cases/{case_id}/recovery-rights?merchant_id={merchant_id}", json={
        "customer_segment": "FIRST_TIME"
    })
    assert res6.status_code == 200
    assert res6.json()["data"]["recovery_right"] == "RETRY"
    print("[PASS] 6. Recovery Rights Policy Evaluation on Supabase: PASS")

    # 7. Calculate Recovery Score
    res7 = supabase_client.post(f"/api/v1/recovery-cases/{case_id}/score?merchant_id={merchant_id}", json={
        "actions": [
            {"action": "RETRY", "probability_of_recovery": 0.85, "channel_cost_paise": 0}
        ]
    })
    assert res7.status_code == 200
    assert res7.json()["data"]["recommended_action"] == "RETRY"
    print("[PASS] 7. Recovery Score Calculation on Supabase: PASS")

    # 8. Decision Engine Action Selection
    res8 = supabase_client.post(f"/api/v1/recovery-cases/{case_id}/decide?merchant_id={merchant_id}", json={
        "candidate_actions": ["RETRY", "WAIT", "STOP"]
    })
    assert res8.status_code == 200
    decision_id = res8.json()["data"]["decision_id"]
    print(f"[PASS] 8. Decision Engine (Created Supabase Decision {decision_id}): PASS")

    # 9. Bounded Simulation Execution with Supabase SELECT FOR UPDATE & Idempotency Key
    idem_key = f"IDEM_SUPABASE_{uuid.uuid4().hex[:8]}"
    res9 = supabase_client.post(
        f"/api/v1/recovery-cases/{case_id}/execute?merchant_id={merchant_id}",
        json={"decision_id": decision_id},
        headers={"Idempotency-Key": idem_key}
    )
    assert res9.status_code == 200
    assert res9.json()["data"]["status"] == "SUCCESS"
    assert res9.json()["data"]["recovered"] is True
    print("[PASS] 9. Bounded Execution on Supabase (Row Locking + Transaction): PASS")

    # 10. Idempotency Key Duplicate Request on Supabase
    res10 = supabase_client.post(
        f"/api/v1/recovery-cases/{case_id}/execute?merchant_id={merchant_id}",
        json={"decision_id": decision_id},
        headers={"Idempotency-Key": idem_key}
    )
    assert res10.status_code == 200
    assert res10.json()["data"]["action_id"] == res9.json()["data"]["action_id"]
    print("[PASS] 10. Idempotency Key Deduplication on Supabase DB: PASS")

    # 11. Fetch Immutable Audit Trail from Supabase
    res11 = supabase_client.get(f"/api/v1/recovery-cases/{case_id}/audit?merchant_id={merchant_id}")
    assert res11.status_code == 200
    events = [e["event_type"] for e in res11.json()["data"]["items"]]
    assert "CASE_DETECTED" in events
    assert "ACTION_EXECUTED" in events
    print("[PASS] 11. Immutable Audit Trail Retrieval from Supabase: PASS")

    # 12. Dashboard Metrics Aggregation from Supabase
    res12 = supabase_client.get(f"/api/v1/dashboard/summary?merchant_id={merchant_id}")
    assert res12.status_code == 200
    assert res12.json()["data"]["total_cases"] >= 1
    assert res12.json()["data"]["revenue_recovered_paise"] >= 149900
    print("[PASS] 12. Dashboard Metrics Aggregation on Supabase: PASS")

    # 13. Batch Strategy Simulation on Supabase
    res13 = supabase_client.post("/api/v1/batch-runs", json={
        "merchant_id": merchant_id,
        "strategy": "NIRNAY_PAY",
        "case_ids": [case_id]
    })
    assert res13.status_code == 200
    assert res13.json()["data"]["strategy"] == "NIRNAY_PAY"
    print("[PASS] 13. Batch Strategy Simulation on Supabase: PASS")

    print("=" * 80)
