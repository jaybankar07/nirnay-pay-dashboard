import os
import psycopg2
import time

SUPABASE_DB_URLS = [
    "postgresql://postgres:2124UDSM2077@db.lelvvtepzxvohhxmiram.supabase.co:5432/postgres",
    "postgresql://postgres.lelvvtepzxvohhxmiram:2124UDSM2077@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres",
    "postgresql://postgres.lelvvtepzxvohhxmiram:2124UDSM2077@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
    "postgresql://postgres.lelvvtepzxvohhxmiram:2124UDSM2077@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
]


def get_working_connection():
    for url in SUPABASE_DB_URLS:
        try:
            conn = psycopg2.connect(url, connect_timeout=5)
            conn.autocommit = True
            print(f"[CONNECTED] Connected using URL: {url.split('@')[1]}")
            return conn
        except Exception as e:
            continue
    raise Exception("Could not connect to Supabase PostgreSQL using any connection string!")


def run_database_query_audit():
    print("=" * 80)
    print("PART 1: SUPABASE POSTGRESQL PRODUCTION QUERY & SCALABILITY AUDIT")
    print("=" * 80)

    conn = get_working_connection()
    cursor = conn.cursor()

    report = []

    def audit_sql(query_name, sql, params=None, expect_error=False):
        start_time = time.time()
        try:
            cursor.execute(sql, params)
            elapsed_ms = (time.time() - start_time) * 1000
            if cursor.description:
                rows = cursor.fetchall()
                row_count = len(rows)
            else:
                row_count = cursor.rowcount
            
            if expect_error:
                report.append({"name": query_name, "status": "FAIL", "latency_ms": round(elapsed_ms, 2), "details": "Expected constraint error but query succeeded!"})
            else:
                report.append({"name": query_name, "status": "PASS", "latency_ms": round(elapsed_ms, 2), "details": f"Fetched/Affected {row_count} rows"})
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            if expect_error:
                report.append({"name": query_name, "status": "PASS", "latency_ms": round(elapsed_ms, 2), "details": f"Correctly rejected with error: {type(e).__name__}"})
            else:
                report.append({"name": query_name, "status": "FAIL", "latency_ms": round(elapsed_ms, 2), "details": str(e)})

    # --- Query 1: Merchants Lookup ---
    audit_sql("1. Select Merchants", "SELECT id, name, email FROM merchants WHERE id = %s;", ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',))

    # --- Query 2: Customer LTV & Segment Lookup ---
    audit_sql("2. Select Customers by Segment", "SELECT id, external_customer_id, customer_segment, lifetime_value_paise FROM customers WHERE merchant_id = %s AND customer_segment = %s;", ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'LOYAL'))

    # --- Query 3: Revenue Events Filtering ---
    audit_sql("3. Select Revenue Events by Type & Date", "SELECT id, amount_paise, event_type, occurred_at FROM revenue_events WHERE merchant_id = %s AND event_type = %s ORDER BY occurred_at DESC;", ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'PAYMENT_FAILURE'))

    # --- Query 4: Subscriptions Past Due ---
    audit_sql("4. Select Past-Due Subscriptions", "SELECT id, external_subscription_id, amount_paise FROM subscriptions WHERE merchant_id = %s AND status = %s;", ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'PAST_DUE'))

    # --- Query 5: Recovery Policies JSONB Query ---
    audit_sql("5. Query Policy rules_json JSONB Field", "SELECT id, rules_json->>'FIRST_TIME' AS first_time_rule FROM recovery_policies WHERE merchant_id = %s AND active = true;", ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',))

    # --- Query 6: Recovery Cases Multi-Table JOIN ---
    audit_sql("6. Join Recovery Cases with Customers & Events", """
        SELECT rc.id, rc.status, rc.amount_at_risk_paise, c.name AS customer_name, re.event_type
        FROM recovery_cases rc
        JOIN customers c ON rc.customer_id = c.id
        JOIN revenue_events re ON rc.revenue_event_id = re.id
        WHERE rc.merchant_id = %s;
    """, ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',))

    # --- Query 7: Decisions & RecoveryScore Query ---
    audit_sql("7. Select Decisions & AI Rationale", """
        SELECT d.id, d.recovery_score, d.selected_action, d.decision_mode, d.ai_rationale
        FROM decisions d
        JOIN recovery_cases rc ON d.recovery_case_id = rc.id
        WHERE rc.merchant_id = %s;
    """, ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',))

    # --- Query 8: Actions Executed ---
    audit_sql("8. Select Executed Actions", """
        SELECT ra.id, ra.action_type, ra.channel, ra.status, ra.executed_at
        FROM recovery_actions ra
        JOIN decisions d ON ra.decision_id = d.id
        JOIN recovery_cases rc ON d.recovery_case_id = rc.id
        WHERE rc.merchant_id = %s;
    """, ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',))

    # --- Query 9: Authoritative Revenue Recovered Metric (SUM) ---
    audit_sql("9. Authoritative Revenue Recovered SUM Metric", """
        SELECT COALESCE(SUM(ro.recovered_amount_paise), 0) AS total_recovered_paise
        FROM recovery_outcomes ro
        JOIN recovery_actions ra ON ro.action_id = ra.id
        JOIN decisions d ON ra.decision_id = d.id
        JOIN recovery_cases rc ON d.recovery_case_id = rc.id
        WHERE rc.merchant_id = %s AND ro.recovered = true;
    """, ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',))

    # --- Query 10: Audit Events Timeline ---
    audit_sql("10. Select Immutable Audit Trail Timeline", """
        SELECT ae.id, ae.event_type, ae.actor_type, ae.event_data_json, ae.created_at
        FROM audit_events ae
        WHERE ae.recovery_case_id = %s
        ORDER BY ae.created_at ASC;
    """, ('31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01',))

    # --- Query 11: Idempotency Key Lookup ---
    audit_sql("11. Idempotency Key Lookup", """
        SELECT response_code, response_json FROM idempotency_keys
        WHERE merchant_id = %s AND endpoint = %s AND idempotency_key = %s;
    """, ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/api/v1/recovery-cases/execute', 'IDEM_KEY_SEED_001'))

    # --- Query 12: Batch Strategy Performance Comparison ---
    audit_sql("12. Select Batch Strategy Performance", """
        SELECT strategy, total_cases, total_at_risk_paise, recovered_paise, recovery_rate, compliance_blocks
        FROM batch_runs
        WHERE merchant_id = %s ORDER BY created_at ASC;
    """, ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',))

    # --- Query 13: Integrity Check — Reject Foreign Key Cascade Delete on Merchant ---
    audit_sql("13. Restrict Cascade Delete on Merchant", "DELETE FROM merchants WHERE id = %s;", ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',), expect_error=True)

    # --- Query 14: Scalability Query Execution Plan (EXPLAIN ANALYZE) ---
    audit_sql("14. EXPLAIN ANALYZE Dashboard Case Query", """
        EXPLAIN ANALYZE SELECT rc.id, rc.status, rc.amount_at_risk_paise, rc.created_at
        FROM recovery_cases rc
        WHERE rc.merchant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND rc.status = 'DETECTED';
    """)

    cursor.close()
    conn.close()

    print("\n" + "-" * 80)
    print("QUERY AUDIT RESULTS")
    print("-" * 80)
    for res in report:
        print(f"[{res['status']}] {res['name']} | Latency: {res['latency_ms']}ms | Details: {res['details']}")
    print("-" * 80)

    # Assert no query failed unexpectedly
    failed = [r for r in report if r["status"] == "FAIL"]
    assert len(failed) == 0, f"Database query failures detected: {failed}"


if __name__ == "__main__":
    run_database_query_audit()
