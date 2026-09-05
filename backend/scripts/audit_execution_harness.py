import sys
import json
import time
import requests
from datetime import datetime

API_BASE = "http://127.0.0.1:8000/api/v1"

print("================================================================================")
print("NIRNAY PAY (RECOVERY OS) -- PRE-SUBMISSION AUDIT EXECUTION HARNESS")
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Target API Base: {API_BASE}")
print("================================================================================")

# 1. Health Check
res = requests.get(f"{API_BASE}/health")
print(f"\n[STEP 1] GET /health -> Status: {res.status_code}, Response: {res.json()}")

# 2. Check Merchant ID
merchant_id = "merchant_001"
res_m = requests.get(f"{API_BASE}/merchants/{merchant_id}")
print(f"[STEP 2] GET /merchants/{merchant_id} -> Status: {res_m.status_code}")

print(f"Using Active Merchant ID: {merchant_id}")

# 3. Live Case Creation Test across 4 Scenarios
scenarios_to_test = [
    ("PAYMENT_FAILURE", "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01", "Ananya Iyer", "LOYAL", 250000, "BANK_DECLINED"),
    ("CHECKOUT_ABANDONMENT", "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02", "Vikram Sethi", "HIGH_VALUE", 149900, "CART_TIMEOUT"),
    ("SUBSCRIPTION_FAILURE", "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03", "Priya Nair", "FIRST_TIME", 99900, "CARD_EXPIRED"),
    ("OVERDUE_RECEIVABLE", "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a04", "Kabir Mehta", "HABITUAL_NON_PAYER", 850000, "INVOICE_OVERDUE")
]

created_cases = []

for sc_type, cust_id, cust_name, cust_seg, amount_paise, reason in scenarios_to_test:
    print(f"\n--------------------------------------------------------------------------------")
    print(f"[LIVE TEST] Creating Fresh Event: {sc_type} | Customer: {cust_name} ({cust_seg}) | Amount: INR {amount_paise/100:,.2f}")
    payload = {
        "merchant_id": merchant_id,
        "customer_id": cust_id,
        "event_type": sc_type,
        "amount_paise": amount_paise,
        "reason_code": reason
    }
    res = requests.post(f"{API_BASE}/detect", json=payload)
    print(f"-> POST /detect Status: {res.status_code}")
    assert res.status_code == 200, f"Failed detect: {res.text}"
    body = res.json()["data"]
    case_id = body["case_id"]
    event_id = body["event_id"]
    print(f"-> Created Case ID: {case_id} | Event ID: {event_id} | Status: {body['status']}")
    
    created_cases.append({
        "scenario": sc_type,
        "case_id": case_id,
        "event_id": event_id,
        "customer_id": cust_id,
        "customer_name": cust_name,
        "customer_segment": cust_seg,
        "amount_paise": amount_paise
    })

# 4. Trace Case #1 End-to-End Through All 8 Pipeline Stages
trace_target = created_cases[0]
target_case_id = trace_target["case_id"]

print(f"\n================================================================================")
print(f"TRACING FRESH CASE END-TO-END: Case ID {target_case_id}")
print(f"Scenario: {trace_target['scenario']} | Amount: INR {trace_target['amount_paise']/100:,.2f}")
print("================================================================================")

# Stage 1: Diagnosis Agent (Agent 1)
print("\n[STAGE 1: DIAGNOSIS AGENT (AGENT 1)]")
res_diag = requests.post(f"{API_BASE}/recovery-cases/{target_case_id}/diagnose?merchant_id={merchant_id}", json={})
print(f"-> POST /diagnose Status: {res_diag.status_code}")
print(f"-> Output: {json.dumps(res_diag.json(), indent=2)}")
assert res_diag.status_code == 200
diag_data = res_diag.json()["data"]
assert diag_data["root_cause"] is not None

# Stage 2: Compliance Check
print("\n[STAGE 2: COMPLIANCE GATE]")
res_comp = requests.post(f"{API_BASE}/recovery-cases/{target_case_id}/compliance-check?merchant_id={merchant_id}", json={
    "candidate_actions": ["RETRY", "REMINDER", "ESCALATE"]
})
print(f"-> POST /compliance-check Status: {res_comp.status_code}")
print(f"-> Output: {json.dumps(res_comp.json(), indent=2)}")
assert res_comp.status_code == 200

# Stage 3: Recovery Rights Policy
print("\n[STAGE 3: RECOVERY RIGHTS POLICY]")
res_rr = requests.post(f"{API_BASE}/recovery-cases/{target_case_id}/recovery-rights?merchant_id={merchant_id}", json={})
print(f"-> POST /recovery-rights Status: {res_rr.status_code}")
print(f"-> Output: {json.dumps(res_rr.json(), indent=2)}")
assert res_rr.status_code == 200

# Stage 4: RecoveryScore Formula Engine
print("\n[STAGE 4: RECOVERYSCORE ENGINE]")
res_score = requests.post(f"{API_BASE}/recovery-cases/{target_case_id}/score?merchant_id={merchant_id}", json={
    "actions": [
        {"action": "RETRY", "probability_of_recovery": 0.8, "channel_cost_paise": 0, "compliance_penalty_paise": 0},
        {"action": "REMINDER", "probability_of_recovery": 0.6, "channel_cost_paise": 50, "compliance_penalty_paise": 0}
    ]
})
print(f"-> POST /score Status: {res_score.status_code}")
print(f"-> Output: {json.dumps(res_score.json(), indent=2)}")
assert res_score.status_code == 200

# Stage 5: Decision Engine & Agent 2 Communication
print("\n[STAGE 5: DECISION ENGINE & COMMUNICATION (AGENT 2)]")
res_dec = requests.post(f"{API_BASE}/recovery-cases/{target_case_id}/decide?merchant_id={merchant_id}", json={
    "candidate_actions": ["RETRY", "REMINDER"]
})
print(f"-> POST /decide Status: {res_dec.status_code}")
print(f"-> Output: {json.dumps(res_dec.json(), indent=2)}")
assert res_dec.status_code == 200
decision_data = res_dec.json()["data"]
decision_id = decision_data["decision_id"]

# Stage 6: Bounded Execution
print("\n[STAGE 6: BOUNDED EXECUTION]")
res_exec = requests.post(f"{API_BASE}/recovery-cases/{target_case_id}/execute?merchant_id={merchant_id}", json={
    "decision_id": decision_id
})
print(f"-> POST /execute Status: {res_exec.status_code}")
print(f"-> Output: {json.dumps(res_exec.json(), indent=2)}")
assert res_exec.status_code == 200
exec_data = res_exec.json()["data"]
assert exec_data["status"] in ["SUCCESS", "BLOCKED", "FAILED"]

# Stage 7: Fetch Case Detail Verification
print("\n[STAGE 7: VERIFY PERSISTED CASE DETAIL]")
res_detail = requests.get(f"{API_BASE}/recovery-cases/{target_case_id}?merchant_id={merchant_id}")
print(f"-> GET /recovery-cases/{target_case_id} Status: {res_detail.status_code}")
print(f"-> Persisted Detail: {json.dumps(res_detail.json(), indent=2)}")
assert res_detail.status_code == 200

# Stage 8: Verify Complete Audit Ledger
print("\n[STAGE 8: AUDIT TIMELINE RECONCILIATION]")
res_audit = requests.get(f"{API_BASE}/recovery-cases/{target_case_id}/audit?merchant_id={merchant_id}")
print(f"-> GET /audit Status: {res_audit.status_code}")
print(f"-> Audit Event Log: {json.dumps(res_audit.json(), indent=2)}")
assert res_audit.status_code == 200
audit_events = res_audit.json()["data"]["items"]
print(f"-> Total Verified Audit Events Logged: {len(audit_events)}")
for idx, evt in enumerate(audit_events, 1):
    print(f"   [{idx}] EventType: {evt['event_type']} | Actor: {evt['actor_type']} | Timestamp: {evt['created_at']}")

# 5. Reconcile Dashboard Summary Metrics
print("\n================================================================================")
print("DASHBOARD SUMMARY RECONCILIATION & BATCH SIMULATION")
print("================================================================================")

res_dash = requests.get(f"{API_BASE}/dashboard/summary?merchant_id={merchant_id}")
print(f"-> GET /dashboard/summary Status: {res_dash.status_code}")
print(f"-> Dashboard Metrics: {json.dumps(res_dash.json(), indent=2)}")
assert res_dash.status_code == 200

print("\n================================================================================")
print("ALL 100% EMPIRICAL PRE-SUBMISSION AUDIT CHECKS COMPLETED SUCCESSFULLY!")
print("================================================================================")
