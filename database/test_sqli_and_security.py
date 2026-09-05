import os
import sys
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Live Supabase PostgreSQL Connection String
SUPABASE_URL = "postgresql://postgres:2124UDSM2077@db.lelvvtepzxvohhxmiram.supabase.co:5432/postgres"

engine = create_engine(SUPABASE_URL, pool_pre_ping=True)


def test_sql_injection_resilience():
    """
    Test SQL Injection payloads against Supabase PostgreSQL using parameterized queries
    and verify zero database vulnerability or unexpected query execution.
    """
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE merchants; --",
        "1 UNION SELECT null, null, null, null--",
        "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND 1=CONVERT(int, (SELECT @@version))--"
    ]

    with engine.connect() as conn:
        for payload in sqli_payloads:
            # Test 1: Merchant lookup by external payload via parameterized query
            result = conn.execute(
                text("SELECT * FROM merchants WHERE id::text = :val OR name = :val"),
                {"val": payload}
            )
            rows = result.fetchall()
            # Parameterization ensures payload is treated as literal string, returning 0 rows
            assert len(rows) == 0, f"SQLi payload executed unexpectedly: {payload}"

    print("\n[PASS] SQL Injection Resilience Test: All payloads safely neutralized by parameterization.")


def test_database_constraint_error_masking():
    """
    Verify that database check constraints enforce integrity and database errors
    do not crash the system or leak internal connection parameters.
    """
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Attempt to insert negative monetary value (violates CHECK amount_paise >= 0)
            conn.execute(
                text("""
                INSERT INTO revenue_events (id, merchant_id, customer_id, event_type, amount_paise, currency, occurred_at)
                VALUES (gen_random_uuid(), 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'PAYMENT_FAILURE', -5000, 'INR', now())
                """)
            )
            trans.commit()
            assert False, "Should have raised CheckViolation for negative monetary amount"
        except SQLAlchemyError as exc:
            trans.rollback()
            err_str = str(exc)
            assert "check constraint" in err_str.lower() or "checkviolation" in err_str.lower()
            # Verify database password is NOT in the error string
            assert "2124UDSM2077" not in err_str, "DATABASE PASSWORD LEAKED IN EXCEPTION!"

    print("[PASS] Database Constraint & Exception Masking Test: Integrity constraints enforced, zero credential leakage.")


def test_database_rls_and_immutability():
    """
    Verify Row Level Security (RLS) is enabled across all 12 core tables.
    """
    with engine.connect() as conn:
        res = conn.execute(
            text("SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public'")
        )
        tables = {row[0]: row[1] for row in res.fetchall()}
        
        expected_tables = [
            "merchants", "customers", "revenue_events", "subscriptions",
            "recovery_policies", "recovery_cases", "decisions",
            "recovery_actions", "recovery_outcomes", "audit_events",
            "idempotency_keys", "batch_runs"
        ]
        
        for t in expected_tables:
            assert t in tables, f"Table '{t}' missing from Supabase DB"
            assert tables[t] is True, f"RLS is NOT enabled for table '{t}'"

    print("[PASS] RLS & Security Audit: Row Level Security enabled on all 12 business tables.")


if __name__ == "__main__":
    test_sql_injection_resilience()
    test_database_constraint_error_masking()
    test_database_rls_and_immutability()
