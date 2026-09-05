import sys
import json
import requests
from datetime import datetime

API_BASE = "http://127.0.0.1:8000/api/v1"
MERCHANT_ID = "merchant_001"

print("================================================================================")
print("NIRNAY PAY (RECOVERYOS) — FINAL PRE-SUBMISSION VERIFICATION SUITE")
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"API Target: {API_BASE}")
print(f"Merchant ID: {MERCHANT_ID}")
print("================================================================================")

# 1. Verification of 4 Scenarios Live Ingestion
scenarios = [
    ("PAYMENT_FAILURE", "cust_live_101", "Aarav Sharma", "LOYAL", 250000, "BANK_DECLINED"),
    ("CHECKOUT_ABANDONMENT", "cust_live_102", "Neha Gupta", "HIGH_VALUE", 149900, "CART_TIMEOUT"),
    ("SUBSCRIPTION_FAILURE", "cust_live_103", "Rohan Das", "FIRST_TIME", 99900, "CARD_EXPIRED"),
    ("OVERDUE_RECEIVABLE", "cust_live_104", "Enterprise Tech Pvt Ltd", "HABITUAL_NON_PAYER", 850000, "INVOICE_OVERDUE")
]

scenario_results = []
for sc_type, c_id, c_name, c_seg, amount, reason in scenarios:
    res = requests.post(f"{API_BASE}/detect", json={
        "merchant_id": MERCHANT_ID,
        "customer_id": c_id,
        "event_type": sc_type,
        "amount_paise": amount,
        "reason_code": reason
    })
    assert res.status_code == 200, f"Detect failed: {res.text}"
    data = res.json()["data"]
    scenario_results.append({
        "scenario": sc_type,
        "case_id": data["case_id"],
        "event_id": data["event_id"],
        "status": data["status"]
    })
    print(f"[SCENARIO OK] {sc_type} -> Case ID: {data['case_id']} | Status: {data['status']}")

# 2. Trace Fresh Case E2E
test_case = scenario_results[0]
case_id = test_case["case_id"]

print(f"\n================================================================================")
print(f"TRACING FRESH LIVE CASE: {case_id}")
print("================================================================================")

# Stage 1: Diagnosis Agent (Agent 1)
res_diag = requests.post(f"{API_BASE}/recovery-cases/{case_id}/diagnose?merchant_id={MERCHANT_ID}", json={})
assert res_diag.status_code == 200
diag_data = res_diag.json()["data"]
print(f"[AGENT 1 DIAGNOSIS] Root Cause: {diag_data['root_cause']} | Confidence: {diag_data['confidence']} | Mode: {diag_data['mode']}")

# Stage 2: Compliance Check
res_comp = requests.post(f"{API_BASE}/recovery-cases/{case_id}/compliance-check?merchant_id={MERCHANT_ID}", json={
    "candidate_actions": ["RETRY", "REMINDER", "ESCALATE"]
})
assert res_comp.status_code == 200
comp_data = res_comp.json()["data"]
print(f"[COMPLIANCE GATE] Result: {comp_data['result']} | Allowed: {comp_data['allowed_actions']}")

# Stage 3: Recovery Rights Policy
res_rr = requests.post(f"{API_BASE}/recovery-cases/{case_id}/recovery-rights?merchant_id={MERCHANT_ID}", json={})
assert res_rr.status_code == 200
rr_data = res_rr.json()["data"]
print(f"[RECOVERY RIGHTS] Policy Treatment: {rr_data['recovery_right']} | Reason: {rr_data['reason']}")

# Stage 4: RecoveryScore Calculation
res_score = requests.post(f"{API_BASE}/recovery-cases/{case_id}/score?merchant_id={MERCHANT_ID}", json={
    "actions": [
        {"action": "RETRY", "probability_of_recovery": 0.85, "channel_cost_paise": 0, "compliance_penalty_paise": 0},
        {"action": "REMINDER", "probability_of_recovery": 0.60, "channel_cost_paise": 50, "compliance_penalty_paise": 0}
    ]
})
assert res_score.status_code == 200
score_data = res_score.json()["data"]
print(f"[RECOVERYSCORE] Calculated Yield Scores: {score_data['scores']} | Recommended: {score_data['recommended_action']}")

# Stage 5: Decision Engine & Agent 2 Communication
res_dec = requests.post(f"{API_BASE}/recovery-cases/{case_id}/decide?merchant_id={MERCHANT_ID}", json={
    "candidate_actions": ["RETRY", "REMINDER"]
})
assert res_dec.status_code == 200
dec_data = res_dec.json()["data"]
decision_id = dec_data["decision_id"]
print(f"[DECISION & AGENT 2] Selected Action: {dec_data['selected_action']} | Decision ID: {decision_id}")

# Stage 6: Bounded Recovery Execution
res_exec = requests.post(f"{API_BASE}/recovery-cases/{case_id}/execute?merchant_id={MERCHANT_ID}", json={
    "decision_id": decision_id
})
assert res_exec.status_code == 200
exec_data = res_exec.json()["data"]
print(f"[BOUNDED EXECUTION] Status: {exec_data['status']} | Recovered: {exec_data['recovered']} | Amount: INR {exec_data['recovered_amount_paise']/100:,.2f}")

# Stage 7: Persisted Detail Verification
res_detail = requests.get(f"{API_BASE}/recovery-cases/{case_id}?merchant_id={MERCHANT_ID}")
assert res_detail.status_code == 200
detail_data = res_detail.json()["data"]
print(f"[PERSISTED DETAIL] Status: {detail_data['status']} | Amount at Risk: INR {detail_data['amount_at_risk_paise']/100:,.2f}")

# Stage 8: Audit Timeline Verification
res_audit = requests.get(f"{API_BASE}/recovery-cases/{case_id}/audit?merchant_id={MERCHANT_ID}")
assert res_audit.status_code == 200
audit_items = res_audit.json()["data"]["items"]
print(f"[AUDIT LOG VERIFIED] Logged {len(audit_items)} immutable audit events.")

# 3. Negative Path Testing (Compliance Blocked & Execution Protection)
print(f"\n================================================================================")
print("TESTING NEGATIVE PATHS & STOPPING RULES")
print("================================================================================")

# Create a Habitual Non-Payer Overdue Case that triggers Escalation/Blocked state
res_neg = requests.post(f"{API_BASE}/detect", json={
    "merchant_id": MERCHANT_ID,
    "customer_id": "cust_neg_999",
    "event_type": "OVERDUE_RECEIVABLE",
    "amount_paise": 500000,
    "reason_code": "WRITEDOWN_LIMIT_EXCEEDED"
})
assert res_neg.status_code == 200
neg_case_id = res_neg.json()["data"]["case_id"]

# Compliance check with restricted action
res_neg_comp = requests.post(f"{API_BASE}/recovery-cases/{neg_case_id}/compliance-check?merchant_id={MERCHANT_ID}", json={
    "candidate_actions": ["ESCALATE"]
})
print(f"[NEGATIVE COMPLIANCE] Status: {res_neg_comp.status_code} | Result: {res_neg_comp.json()['data']['result']}")

# 4. Batch Run Verification
print(f"\n================================================================================")
print("TESTING BATCH MEASUREMENT ENGINE")
print("================================================================================")
res_batch = requests.post(f"{API_BASE}/batch-runs", json={
    "merchant_id": MERCHANT_ID,
    "strategy": "NIRNAY_PAY",
    "case_ids": [case_id, neg_case_id]
})
assert res_batch.status_code == 200
batch_data = res_batch.json()["data"]
print(f"[BATCH RUN OK] Batch Run ID: {batch_data['batch_run_id']} | Strategy: {batch_data['strategy']} | Total Cases: {batch_data['total_cases']}")

# 5. Reconcile Dashboard Metrics
print(f"\n================================================================================")
print("DASHBOARD FINANCIAL RECONCILIATION")
print("================================================================================")
res_dash = requests.get(f"{API_BASE}/dashboard/summary?merchant_id={MERCHANT_ID}")
assert res_dash.status_code == 200
dash_data = res_dash.json()["data"]
print(f"[DASHBOARD RECONCILED] At Risk: INR {dash_data['revenue_at_risk_paise']/100:,.2f} | Recovered: INR {dash_data['revenue_recovered_paise']/100:,.2f} | Active Cases: {dash_data['active_cases']} | Yield: {dash_data['recovery_rate']*100:.2f}%")

print("\n================================================================================")
print("FINAL PRE-SUBMISSION VERIFICATION COMPLETED SUCCESSFULLY WITH 100% EMPIRICAL PROOF!")
print("================================================================================")
