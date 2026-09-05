import pytest
import uuid
from app.models import Merchant, Customer, RevenueEvent, RecoveryCase, Decision
from app.utils.enums import (
    CustomerSegment, RevenueEventType, RecoveryCaseStatus,
    ComplianceResult, RecoveryRightTreatment, ActionType, DecisionMode
)


def test_audit_all_16_endpoints_happy_and_failure_paths(client, db_session):
    """
    Comprehensive End-to-End Audit Test Suite for all 16 API Endpoints.
    Tests:
    1. Happy path (Success 200/201, standard JSON payload format)
    2. Failure path (400/404/403/422 status codes, stable error codes, NO stack traces exposed)
    """

    # --- Setup Test Seed Data in DB ---
    merchant = Merchant(id="m_audit_001", name="Audit Merchant", email="audit@merchant.com")
    customer = Customer(id="c_audit_001", merchant_id="m_audit_001", external_customer_id="EXT_AUDIT", name="Audit User", customer_segment=CustomerSegment.FIRST_TIME)
    revenue_event = RevenueEvent(id="e_audit_001", merchant_id="m_audit_001", customer_id="c_audit_001", event_type=RevenueEventType.PAYMENT_FAILURE, amount_paise=49900)
    case = RecoveryCase(id="rc_audit_001", merchant_id="m_audit_001", customer_id="c_audit_001", revenue_event_id="e_audit_001", status=RecoveryCaseStatus.DETECTED, scenario_type=RevenueEventType.PAYMENT_FAILURE, amount_at_risk_paise=49900)
    decision = Decision(id="d_audit_001", recovery_case_id="rc_audit_001", compliance_result=ComplianceResult.APPROVED, recovery_right=RecoveryRightTreatment.RETRY, recovery_score=100.0, selected_action=ActionType.RETRY, decision_mode=DecisionMode.RULE)
    
    db_session.add_all([merchant, customer, revenue_event, case, decision])
    db_session.commit()

    report = []

    # Helper function to audit responses
    def record_audit(ep_name, method, url, request_payload, resp, expected_status, is_failure_test=False):
        status_ok = resp.status_code == expected_status
        data = resp.json()
        
        # Check standard envelope format
        if not is_failure_test:
            format_ok = (data.get("success") is True and "data" in data) or ("status" in data) or ("metrics" in url)
        else:
            format_ok = data.get("success") is False and "error" in data and "code" in data["error"] and "message" in data["error"]
        
        # Check security: NO Python stack trace keywords
        text_resp = resp.text
        has_stack_trace = "Traceback (most recent call last)" in text_resp or "File \"" in text_resp or "site-packages" in text_resp

        result_status = "PASS" if (status_ok and format_ok and not has_stack_trace) else "FAIL"

        report.append({
            "endpoint": ep_name,
            "method": method,
            "url": url,
            "test_type": "NEGATIVE / FAILURE" if is_failure_test else "HAPPY PATH",
            "http_status": resp.status_code,
            "expected_status": expected_status,
            "error_code": data.get("error", {}).get("code") if is_failure_test else "N/A",
            "has_stack_trace": has_stack_trace,
            "result": result_status
        })

        assert status_ok, f"[{ep_name}] Expected status {expected_status}, got {resp.status_code}: {text_resp}"
        assert format_ok, f"[{ep_name}] Invalid JSON envelope structure: {data}"
        assert not has_stack_trace, f"[{ep_name}] SECURITY VIOLATION: Exposed stack trace in response!"

    # -------------------------------------------------------------------------
    # 1. GET /api/v1/health
    # -------------------------------------------------------------------------
    r1_happy = client.get("/api/v1/health")
    record_audit("1. Health Check", "GET", "/api/v1/health", None, r1_happy, 200)

    # =========================================================================
    # 2. GET /api/v1/merchants/{merchant_id}
    # =========================================================================
    r2_happy = client.get(f"/api/v1/merchants/{merchant.id}")
    record_audit("2. Get Merchant", "GET", f"/api/v1/merchants/{merchant.id}", None, r2_happy, 200)

    r2_fail = client.get("/api/v1/merchants/non_existent_m_99999")
    record_audit("2. Get Merchant (Not Found)", "GET", "/api/v1/merchants/non_existent_m_99999", None, r2_fail, 404, is_failure_test=True)

    # =========================================================================
    # 3. POST /api/v1/recovery-cases
    # =========================================================================
    r3_happy = client.post("/api/v1/recovery-cases", json={
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "revenue_event_id": revenue_event.id,
        "scenario_type": "PAYMENT_FAILURE",
        "amount_at_risk_paise": 10000
    })
    record_audit("3. Create Case", "POST", "/api/v1/recovery-cases", {}, r3_happy, 201)

    r3_fail = client.post("/api/v1/recovery-cases", json={
        "merchant_id": merchant.id,
        "revenue_event_id": revenue_event.id,
        "scenario_type": "PAYMENT_FAILURE",
        "amount_at_risk_paise": -500  # Negative amount failure
    })
    record_audit("3. Create Case (Validation Error)", "POST", "/api/v1/recovery-cases", {}, r3_fail, 422, is_failure_test=True)

    # =========================================================================
    # 4. GET /api/v1/recovery-cases
    # =========================================================================
    r4_happy = client.get(f"/api/v1/recovery-cases?merchant_id={merchant.id}")
    record_audit("4. List Cases", "GET", f"/api/v1/recovery-cases?merchant_id={merchant.id}", None, r4_happy, 200)

    r4_fail = client.get("/api/v1/recovery-cases")  # Missing required merchant_id
    record_audit("4. List Cases (Missing Merchant ID)", "GET", "/api/v1/recovery-cases", None, r4_fail, 422, is_failure_test=True)

    # =========================================================================
    # 5. GET /api/v1/recovery-cases/{case_id}
    # =========================================================================
    r5_happy = client.get(f"/api/v1/recovery-cases/{case.id}?merchant_id={merchant.id}")
    record_audit("5. Get Case Details", "GET", f"/api/v1/recovery-cases/{case.id}", None, r5_happy, 200)

    r5_fail = client.get(f"/api/v1/recovery-cases/invalid_case_id_999?merchant_id={merchant.id}")
    record_audit("5. Get Case Details (Case Not Found)", "GET", "/api/v1/recovery-cases/invalid_case_id_999", None, r5_fail, 404, is_failure_test=True)

    # =========================================================================
    # 6. POST /api/v1/detect
    # =========================================================================
    r6_happy = client.post("/api/v1/detect", json={
        "merchant_id": merchant.id,
        "customer_id": customer.id,
        "event_type": "CHECKOUT_ABANDONMENT",
        "amount_paise": 25000,
        "reason_code": "CART_TIMEOUT"
    })
    record_audit("6. Detect Event", "POST", "/api/v1/detect", {}, r6_happy, 200)

    r6_fail = client.post("/api/v1/detect", json={
        "merchant_id": "non_existent_merchant",
        "event_type": "CHECKOUT_ABANDONMENT",
        "amount_paise": 25000
    })
    record_audit("6. Detect Event (Merchant Not Found)", "POST", "/api/v1/detect", {}, r6_fail, 404, is_failure_test=True)

    # =========================================================================
    # 7. POST /api/v1/recovery-cases/{case_id}/diagnose
    # =========================================================================
    r7_happy = client.post(f"/api/v1/recovery-cases/{case.id}/diagnose?merchant_id={merchant.id}", json={
        "support_notes": "Customer mentions expired debit card."
    })
    record_audit("7. Diagnose Case", "POST", f"/api/v1/recovery-cases/{case.id}/diagnose", {}, r7_happy, 200)

    r7_fail = client.post(f"/api/v1/recovery-cases/non_existent_case/diagnose?merchant_id={merchant.id}", json={})
    record_audit("7. Diagnose Case (Case Not Found)", "POST", "/api/v1/recovery-cases/non_existent_case/diagnose", {}, r7_fail, 404, is_failure_test=True)

    # =========================================================================
    # 8. POST /api/v1/recovery-cases/{case_id}/compliance-check
    # =========================================================================
    r8_happy = client.post(f"/api/v1/recovery-cases/{case.id}/compliance-check?merchant_id={merchant.id}", json={
        "candidate_actions": ["RETRY", "REMINDER"]
    })
    record_audit("8. Compliance Check", "POST", f"/api/v1/recovery-cases/{case.id}/compliance-check", {}, r8_happy, 200)

    r8_fail = client.post(f"/api/v1/recovery-cases/{case.id}/compliance-check?merchant_id={merchant.id}", json={
        "candidate_actions": ["INVALID_ACTION_NAME"]
    })
    record_audit("8. Compliance Check (Invalid Action Enum)", "POST", f"/api/v1/recovery-cases/{case.id}/compliance-check", {}, r8_fail, 422, is_failure_test=True)

    # =========================================================================
    # 9. POST /api/v1/recovery-cases/{case_id}/recovery-rights
    # =========================================================================
    r9_happy = client.post(f"/api/v1/recovery-cases/{case.id}/recovery-rights?merchant_id={merchant.id}", json={
        "customer_segment": "LOYAL"
    })
    record_audit("9. Recovery Rights", "POST", f"/api/v1/recovery-cases/{case.id}/recovery-rights", {}, r9_happy, 200)

    r9_fail = client.post(f"/api/v1/recovery-cases/{case.id}/recovery-rights?merchant_id={merchant.id}", json={
        "customer_segment": "UNKNOWN_SEGMENT"
    })
    record_audit("9. Recovery Rights (Invalid Segment Enum)", "POST", f"/api/v1/recovery-cases/{case.id}/recovery-rights", {}, r9_fail, 422, is_failure_test=True)

    # =========================================================================
    # 10. POST /api/v1/recovery-cases/{case_id}/score
    # =========================================================================
    r10_happy = client.post(f"/api/v1/recovery-cases/{case.id}/score?merchant_id={merchant.id}", json={
        "actions": [
            {"action": "RETRY", "probability_of_recovery": 0.85, "channel_cost_paise": 0}
        ]
    })
    record_audit("10. Recovery Score", "POST", f"/api/v1/recovery-cases/{case.id}/score", {}, r10_happy, 200)

    r10_fail = client.post(f"/api/v1/recovery-cases/{case.id}/score?merchant_id={merchant.id}", json={
        "actions": [
            {"action": "RETRY", "probability_of_recovery": 1.5}  # Probability > 1.0 failure
        ]
    })
    record_audit("10. Recovery Score (Invalid Probability Range)", "POST", f"/api/v1/recovery-cases/{case.id}/score", {}, r10_fail, 422, is_failure_test=True)

    # =========================================================================
    # 11. POST /api/v1/recovery-cases/{case_id}/decide
    # =========================================================================
    r11_happy = client.post(f"/api/v1/recovery-cases/{case.id}/decide?merchant_id={merchant.id}", json={
        "candidate_actions": ["RETRY", "WAIT", "REMINDER"]
    })
    record_audit("11. Decide Action", "POST", f"/api/v1/recovery-cases/{case.id}/decide", {}, r11_happy, 200)

    r11_fail = client.post(f"/api/v1/recovery-cases/non_existent_case/decide?merchant_id={merchant.id}", json={
        "candidate_actions": ["RETRY"]
    })
    record_audit("11. Decide Action (Case Not Found)", "POST", "/api/v1/recovery-cases/non_existent_case/decide", {}, r11_fail, 404, is_failure_test=True)

    # =========================================================================
    # 12. POST /api/v1/recovery-cases/{case_id}/execute
    # =========================================================================
    r12_happy = client.post(f"/api/v1/recovery-cases/{case.id}/execute?merchant_id={merchant.id}", json={
        "decision_id": decision.id
    })
    record_audit("12. Execute Action", "POST", f"/api/v1/recovery-cases/{case.id}/execute", {}, r12_happy, 200)

    r12_fail = client.post(f"/api/v1/recovery-cases/{case.id}/execute?merchant_id={merchant.id}", json={
        "decision_id": "non_existent_decision_id"
    })
    record_audit("12. Execute Action (Decision Not Found)", "POST", f"/api/v1/recovery-cases/{case.id}/execute", {}, r12_fail, 404, is_failure_test=True)

    # =========================================================================
    # 13. GET /api/v1/recovery-cases/{case_id}/audit
    # =========================================================================
    r13_happy = client.get(f"/api/v1/recovery-cases/{case.id}/audit?merchant_id={merchant.id}")
    record_audit("13. Get Audit Log", "GET", f"/api/v1/recovery-cases/{case.id}/audit", None, r13_happy, 200)

    r13_fail = client.get(f"/api/v1/recovery-cases/{case.id}/audit?merchant_id=wrong_merchant_id")
    record_audit("13. Get Audit Log (Merchant Isolation 404)", "GET", f"/api/v1/recovery-cases/{case.id}/audit", None, r13_fail, 404, is_failure_test=True)

    # =========================================================================
    # 14. GET /api/v1/dashboard/summary
    # =========================================================================
    r14_happy = client.get(f"/api/v1/dashboard/summary?merchant_id={merchant.id}")
    record_audit("14. Dashboard Summary", "GET", f"/api/v1/dashboard/summary?merchant_id={merchant.id}", None, r14_happy, 200)

    r14_fail = client.get("/api/v1/dashboard/summary")  # Missing merchant_id
    record_audit("14. Dashboard Summary (Missing Merchant ID)", "GET", "/api/v1/dashboard/summary", None, r14_fail, 422, is_failure_test=True)

    # =========================================================================
    # 15. GET /api/v1/dashboard/cases
    # =========================================================================
    r15_happy = client.get(f"/api/v1/dashboard/cases?merchant_id={merchant.id}")
    record_audit("15. Dashboard Cases", "GET", f"/api/v1/dashboard/cases?merchant_id={merchant.id}", None, r15_happy, 200)

    r15_fail = client.get("/api/v1/dashboard/cases?merchant_id=m_audit_001&limit=1000")  # Limit exceeds max 100
    record_audit("15. Dashboard Cases (Limit Exceeds Max)", "GET", "/api/v1/dashboard/cases", None, r15_fail, 422, is_failure_test=True)

    # =========================================================================
    # 16. POST /api/v1/batch-runs
    # =========================================================================
    r16_happy = client.post("/api/v1/batch-runs", json={
        "merchant_id": merchant.id,
        "strategy": "NIRNAY_PAY",
        "case_ids": [case.id]
    })
    record_audit("16. Batch Simulation", "POST", "/api/v1/batch-runs", {}, r16_happy, 200)

    r16_fail = client.post("/api/v1/batch-runs", json={
        "merchant_id": merchant.id,
        "strategy": "NIRNAY_PAY",
        "case_ids": []  # Empty case_ids validation error
    })
    record_audit("16. Batch Simulation (Empty Case List)", "POST", "/api/v1/batch-runs", {}, r16_fail, 422, is_failure_test=True)

    print("\n\n" + "="*80)
    print("END-TO-END API AUDIT REPORT")
    print("="*80)
    for entry in report:
        print(f"[{entry['result']}] {entry['method']} {entry['url']} | Test: {entry['test_type']} | Status: {entry['http_status']} (Expected {entry['expected_status']}) | Code: {entry['error_code']} | StackTraceExposed: {entry['has_stack_trace']}")
    print("="*80)
