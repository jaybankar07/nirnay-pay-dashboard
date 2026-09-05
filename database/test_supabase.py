import os
import pytest
import psycopg2

SUPABASE_DB_URL = os.getenv(
    "SUPABASE_DATABASE_URL",
    "postgresql://postgres:2124UDSM2077@db.lelvvtepzxvohhxmiram.supabase.co:5432/postgres"
)

EXPECTED_TABLES = [
    "merchants", "customers", "revenue_events", "subscriptions",
    "recovery_cases", "recovery_policies", "decisions", "recovery_actions",
    "recovery_outcomes", "audit_events", "idempotency_keys", "batch_runs"
]


def get_connection():
    return psycopg2.connect(SUPABASE_DB_URL)


def test_supabase_all_12_tables_exist():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    for expected in EXPECTED_TABLES:
        assert expected in tables, f"Missing required table: {expected}"

    # Ensure NO unexpected business tables exist
    unexpected = [t for t in tables if t not in EXPECTED_TABLES and not t.startswith("spatial_")]
    assert len(unexpected) == 0, f"Found unauthorized business tables in schema: {unexpected}"


def test_supabase_negative_money_rejected():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Attempt to insert negative amount in revenue_events
        cursor.execute("""
            INSERT INTO revenue_events (merchant_id, customer_id, event_type, amount_paise, occurred_at)
            VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'PAYMENT_FAILURE', -500, now());
        """)
        conn.commit()
        pytest.fail("Database permitted negative money amount_paise!")
    except psycopg2.IntegrityError:
        conn.rollback()
    finally:
        conn.close()


def test_supabase_invalid_customer_segment_rejected():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO customers (merchant_id, external_customer_id, customer_segment)
            VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'EXT_INVALID', 'INVALID_SEGMENT');
        """)
        conn.commit()
        pytest.fail("Database permitted invalid customer_segment enum value!")
    except psycopg2.IntegrityError:
        conn.rollback()
    finally:
        conn.close()


def test_supabase_duplicate_idempotency_key_rejected():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO idempotency_keys (merchant_id, endpoint, idempotency_key, response_code, response_json)
            VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/api/v1/recovery-cases/execute', 'IDEM_KEY_SEED_001', 200, '{}'::jsonb);
        """)
        conn.commit()
        pytest.fail("Database permitted duplicate idempotency key!")
    except psycopg2.IntegrityError:
        conn.rollback()
    finally:
        conn.close()


def test_supabase_duplicate_customer_external_id_rejected():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO customers (merchant_id, external_customer_id, customer_segment)
            VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'EXT_CUST_FIRST_TIME', 'FIRST_TIME');
        """)
        conn.commit()
        pytest.fail("Database permitted duplicate customer external ID for same merchant!")
    except psycopg2.IntegrityError:
        conn.rollback()
    finally:
        conn.close()


def test_supabase_seed_data_loaded():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM merchants;")
    m_count = cursor.fetchone()[0]
    assert m_count >= 1

    cursor.execute("SELECT COUNT(*) FROM customers;")
    c_count = cursor.fetchone()[0]
    assert c_count >= 4

    cursor.execute("SELECT COUNT(*) FROM recovery_cases;")
    cases_count = cursor.fetchone()[0]
    assert cases_count >= 4

    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
