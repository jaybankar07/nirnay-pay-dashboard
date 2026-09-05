import pytest
from app.models.recovery_policy import RecoveryPolicy


def test_full_e2e_recovery_workflow(client, db_session, seeded_merchant):
    merchant_id = seeded_merchant.id

    # 0. Add Merchant Policy (enables explicit RETRY for FIRST_TIME segment)
    policy = RecoveryPolicy(
        merchant_id=merchant_id,
        policy_name="E2E Test Policy",
        rules_json={"FIRST_TIME": "RETRY", "LOYAL": "GRACE_PERIOD"},
        active=True
    )
    db_session.add(policy)
    db_session.commit()

    # 1. Detect Event
    detect_res = client.post("/api/v1/detect", json={
        "merchant_id": merchant_id,
        "event_type": "PAYMENT_FAILURE",
        "amount_paise": 49900,
        "reason_code": "DECLINED"
    })
    assert detect_res.status_code == 200
    case_id = detect_res.json()["data"]["case_id"]

    # 2. Diagnose Case
    diag_res = client.post(f"/api/v1/recovery-cases/{case_id}/diagnose?merchant_id={merchant_id}", json={
        "support_notes": "Customer reports a recently replaced credit card."
    })
    assert diag_res.status_code == 200
    assert diag_res.json()["data"]["root_cause"] is not None

    # 3. Compliance Check
    comp_res = client.post(f"/api/v1/recovery-cases/{case_id}/compliance-check?merchant_id={merchant_id}", json={
        "candidate_actions": ["RETRY", "REMINDER", "ESCALATE"]
    })
    assert comp_res.status_code == 200
    assert comp_res.json()["data"]["result"] == "APPROVED"

    # 4. Recovery Rights
    rights_res = client.post(f"/api/v1/recovery-cases/{case_id}/recovery-rights?merchant_id={merchant_id}", json={
        "customer_segment": "FIRST_TIME"
    })
    assert rights_res.status_code == 200
    assert rights_res.json()["data"]["recovery_right"] == "RETRY"

    # 5. Recovery Score
    score_res = client.post(f"/api/v1/recovery-cases/{case_id}/score?merchant_id={merchant_id}", json={
        "actions": [
            {"action": "RETRY", "probability_of_recovery": 0.85, "channel_cost_paise": 0},
            {"action": "REMINDER", "probability_of_recovery": 0.50, "channel_cost_paise": 100}
        ]
    })
    assert score_res.status_code == 200

    # 6. Decide Action
    decide_res = client.post(f"/api/v1/recovery-cases/{case_id}/decide?merchant_id={merchant_id}", json={
        "candidate_actions": ["RETRY", "WAIT", "REMINDER", "STOP"]
    })
    assert decide_res.status_code == 200
    decision_id = decide_res.json()["data"]["decision_id"]
    assert decide_res.json()["data"]["selected_action"] == "RETRY"

    # 7. Execute Simulation
    exec_res = client.post(
        f"/api/v1/recovery-cases/{case_id}/execute?merchant_id={merchant_id}",
        json={"decision_id": decision_id},
        headers={"Idempotency-Key": f"E2E_KEY_{case_id}"}
    )
    assert exec_res.status_code == 200
    assert exec_res.json()["data"]["status"] == "SUCCESS"
    assert exec_res.json()["data"]["recovered"] is True

    # 8. Verify Audit Trail
    audit_res = client.get(f"/api/v1/recovery-cases/{case_id}/audit?merchant_id={merchant_id}")
    assert audit_res.status_code == 200
    events = [e["event_type"] for e in audit_res.json()["data"]["items"]]
    assert "CASE_DETECTED" in events
    assert "COMPLIANCE_CHECKED" in events
    assert "DECISION_MADE" in events
    assert "ACTION_EXECUTED" in events

    # 9. Verify Dashboard Summary
    dash_res = client.get(f"/api/v1/dashboard/summary?merchant_id={merchant_id}")
    assert dash_res.status_code == 200
    assert dash_res.json()["data"]["revenue_recovered_paise"] == 49900
    assert dash_res.json()["data"]["recovery_rate"] == 1.0
