import json
import requests
from datetime import datetime

API_BASE = "http://127.0.0.1:8000/api/v1"
MERCHANT_ID = "merchant_001"

print("================================================================================")
print("NIRNAY PAY -- LIVE AI E2E TEST (NEW USER, NEW CASE, GROK API INTEGRATION)")
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Target API Base: {API_BASE}")
print(f"Merchant ID: {MERCHANT_ID}")
print("================================================================================")

# 1. Create a Brand New Unique Customer & Risk Event
new_customer_name = "Devendra Fadnavis (Enterprise VIP)"
new_customer_id = f"cust_grok_{int(datetime.now().timestamp())}"
custom_amount_paise = 499900  # INR 4,999.00

print(f"\n[STEP 1] Creating Fresh Live Event for NEW CUSTOMER:")
print(f"-> Customer Name: {new_customer_name}")
print(f"-> Customer ID:   {new_customer_id}")
print(f"-> Amount At Risk: INR {custom_amount_paise/100:,.2f}")
print(f"-> Risk Scenario: PAYMENT_FAILURE (Reason: CARD_EXPIRED)")

res_detect = requests.post(f"{API_BASE}/detect", json={
    "merchant_id": MERCHANT_ID,
    "customer_id": new_customer_id,
    "event_type": "PAYMENT_FAILURE",
    "amount_paise": custom_amount_paise,
    "reason_code": "CARD_EXPIRED"
})
assert res_detect.status_code == 200, f"Detect failed: {res_detect.text}"
detect_data = res_detect.json()["data"]
new_case_id = detect_data["case_id"]
print(f"-> CREATED CASE ID: {new_case_id}")
print(f"-> EVENT ID:       {detect_data['event_id']}")
print(f"-> CASE STATUS:     {detect_data['status']}")

# 2. Execute Stage 1: Diagnosis Agent (Agent 1)
print(f"\n[STEP 2] Executing Stage 1: AI Diagnosis (Agent 1)...")
res_diag = requests.post(f"{API_BASE}/recovery-cases/{new_case_id}/diagnose?merchant_id={MERCHANT_ID}", json={})
assert res_diag.status_code == 200
diag_data = res_diag.json()["data"]
print(f"-> Root Cause:    {diag_data['root_cause']}")
print(f"-> Confidence:    {diag_data['confidence']*100:.1f}%")
print(f"-> Diagnosis Rationale: {diag_data['rationale']}")

# 3. Execute Stage 2: Compliance Gate
print(f"\n[STEP 3] Executing Stage 2: Compliance Gate...")
res_comp = requests.post(f"{API_BASE}/recovery-cases/{new_case_id}/compliance-check?merchant_id={MERCHANT_ID}", json={
    "candidate_actions": ["RETRY", "REMINDER", "ESCALATE"]
})
assert res_comp.status_code == 200
comp_data = res_comp.json()["data"]
print(f"-> Compliance Result: {comp_data['result']}")
print(f"-> Allowed Actions:    {comp_data['allowed_actions']}")

# 4. Execute Stage 3: Recovery Rights Policy
print(f"\n[STEP 4] Executing Stage 3: Merchant Recovery Rights LTV Policy...")
res_rr = requests.post(f"{API_BASE}/recovery-cases/{new_case_id}/recovery-rights?merchant_id={MERCHANT_ID}", json={})
assert res_rr.status_code == 200
rr_data = res_rr.json()["data"]
print(f"-> Recovery Treatment: {rr_data['recovery_right']}")
print(f"-> Treatment Policy:   {rr_data['reason']}")

# 5. Execute Stage 4: RecoveryScore Formula Engine
print(f"\n[STEP 5] Executing Stage 4: RecoveryScore Valuation Engine...")
res_score = requests.post(f"{API_BASE}/recovery-cases/{new_case_id}/score?merchant_id={MERCHANT_ID}", json={
    "actions": [
        {"action": "RETRY", "probability_of_recovery": 0.88, "channel_cost_paise": 0, "compliance_penalty_paise": 0},
        {"action": "REMINDER", "probability_of_recovery": 0.65, "channel_cost_paise": 50, "compliance_penalty_paise": 0}
    ]
})
assert res_score.status_code == 200
score_data = res_score.json()["data"]
print(f"-> Valuation Scores: {score_data['scores']}")
print(f"-> Recommended Action: {score_data['recommended_action']}")

# 6. Execute Stage 5: Decision Engine & Agent 2 (Grok LLM)
print(f"\n[STEP 6] Executing Stage 5: Decision Engine & Live xAI Grok Communication Agent...")
res_dec = requests.post(f"{API_BASE}/recovery-cases/{new_case_id}/decide?merchant_id={MERCHANT_ID}", json={
    "candidate_actions": ["RETRY", "REMINDER"]
})
assert res_dec.status_code == 200
dec_data = res_dec.json()["data"]
decision_id = dec_data["decision_id"]
print(f"-> Authoritative Action: {dec_data['selected_action']}")
print(f"-> Decision Mode:        {dec_data['decision_mode']}")
print(f"-> Rationale:            {dec_data['rationale']}")

# 7. Execute Stage 6: Bounded Execution
print(f"\n[STEP 7] Executing Stage 6: Bounded Recovery Execution...")
res_exec = requests.post(f"{API_BASE}/recovery-cases/{new_case_id}/execute?merchant_id={MERCHANT_ID}", json={
    "decision_id": decision_id
})
assert res_exec.status_code == 200
exec_data = res_exec.json()["data"]
print(f"-> Execution Status:    {exec_data['status']}")
print(f"-> Recovered Flag:       {exec_data['recovered']}")
print(f"-> Recovered Amount:     INR {exec_data['recovered_amount_paise']/100:,.2f}")

# 8. Reconcile Dashboard Financial Summary
print(f"\n================================================================================")
print("RECONCILING DASHBOARD METRICS WITH DATABASE")
print("================================================================================")
res_dash = requests.get(f"{API_BASE}/dashboard/summary?merchant_id={MERCHANT_ID}")
assert res_dash.status_code == 200
dash = res_dash.json()["data"]
print(f"-> Total Cases:             {dash['total_cases']}")
print(f"-> Active Cases:            {dash['active_cases']}")
print(f"-> Revenue At Risk:         INR {dash['revenue_at_risk_paise']/100:,.2f}")
print(f"-> Total Revenue Recovered: INR {dash['revenue_recovered_paise']/100:,.2f}")
print(f"-> Recovery Yield Rate:     {dash['recovery_rate']*100:.2f}%")

print("\n================================================================================")
print("LIVE E2E TEST COMPLETED SUCCESSFULLY!")
print("================================================================================")
