import pytest
from app.utils.enums import RevenueEventType, CustomerSegment, ActionType


def test_health_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] in ("UP", "healthy")


def test_merchant_endpoint(client, seeded_merchant):
    res = client.get(f"/api/v1/merchants/{seeded_merchant.id}")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Test Merchant"


def test_detect_endpoint(client, seeded_merchant):
    payload = {
        "merchant_id": seeded_merchant.id,
        "event_type": "PAYMENT_FAILURE",
        "amount_paise": 49900,
        "reason_code": "DECLINED"
    }
    res = client.post("/api/v1/detect", json=payload)
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "case_id" in res.json()["data"]


def test_recovery_case_crud_endpoints(client, seeded_merchant, seeded_case):
    # Get Case
    res = client.get(f"/api/v1/recovery-cases/{seeded_case.id}?merchant_id={seeded_merchant.id}")
    assert res.status_code == 200
    assert res.json()["data"]["id"] == seeded_case.id

    # List Cases
    res = client.get(f"/api/v1/recovery-cases?merchant_id={seeded_merchant.id}")
    assert res.status_code == 200
    assert res.json()["data"]["total"] >= 1


def test_compliance_and_scoring_endpoints(client, seeded_merchant, seeded_case):
    # Compliance
    comp_res = client.post(
        f"/api/v1/recovery-cases/{seeded_case.id}/compliance-check?merchant_id={seeded_merchant.id}",
        json={"candidate_actions": ["RETRY", "REMINDER"]}
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["data"]["result"] == "APPROVED"

    # Score
    score_res = client.post(
        f"/api/v1/recovery-cases/{seeded_case.id}/score?merchant_id={seeded_merchant.id}",
        json={"actions": [{"action": "RETRY", "probability_of_recovery": 0.8, "channel_cost_paise": 0}]}
    )
    assert score_res.status_code == 200
    assert score_res.json()["data"]["recommended_action"] == "RETRY"


def test_dashboard_endpoints(client, seeded_merchant):
    res = client.get(f"/api/v1/dashboard/summary?merchant_id={seeded_merchant.id}")
    assert res.status_code == 200
    assert "revenue_at_risk_paise" in res.json()["data"]
    assert "revenue_recovered_paise" in res.json()["data"]

    cases_res = client.get(f"/api/v1/dashboard/cases?merchant_id={seeded_merchant.id}")
    assert cases_res.status_code == 200
