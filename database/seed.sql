-- =============================================================================
-- Nirnay Pay (RecoveryOS) — Supabase PostgreSQL Seed DML Data
-- Deterministic Fixed UUID Synthetic Seed Dataset (Valid Hex UUIDs)
-- =============================================================================

-- Clear existing data if re-running seed
TRUNCATE TABLE batch_runs, idempotency_keys, audit_events, recovery_outcomes,
               recovery_actions, decisions, recovery_cases, recovery_policies,
               subscriptions, revenue_events, customers, merchants RESTART IDENTITY CASCADE;

-- 1. Merchants
INSERT INTO merchants (id, name, email) VALUES
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Apex SaaS Technologies', 'finance@apexsast.com');

-- 2. Customers
INSERT INTO customers (id, merchant_id, external_customer_id, name, email, customer_segment, tenure_days, lifetime_value_paise, successful_payment_count, failed_payment_count) VALUES
('c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'EXT_CUST_FIRST_TIME', 'Ananya Sharma', 'ananya@example.com', 'FIRST_TIME', 10, 149900, 1, 1),
('c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'EXT_CUST_LOYAL', 'Rahul Verma', 'rahul@example.com', 'LOYAL', 365, 2499000, 12, 0),
('c3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'EXT_CUST_PREMIUM', 'Enterprise Corp India', 'billing@enterprisecorp.in', 'PREMIUM', 720, 15000000, 24, 0),
('c4eebc99-9c0b-4ef8-bb6d-6bb9bd380a04', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'EXT_CUST_HABITUAL', 'Vikram Singh', 'vikram@example.com', 'HABITUAL_NON_PAYER', 90, 49900, 1, 4);

-- 3. Revenue Events
INSERT INTO revenue_events (id, merchant_id, customer_id, event_type, external_reference, amount_paise, currency, reason_code, occurred_at) VALUES
('e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'PAYMENT_FAILURE', 'PAY_REF_1001', 149900, 'INR', 'TEMPORARY_DECLINE', now() - INTERVAL '2 hours'),
('e2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 'CHECKOUT_ABANDONMENT', 'CART_9002', 499000, 'INR', 'CART_TIMEOUT', now() - INTERVAL '5 hours'),
('e3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 'SUBSCRIPTION_FAILURE', 'SUB_RENEWAL_88', 2500000, 'INR', 'CARD_EXPIRED', now() - INTERVAL '1 day'),
('e4eebc99-9c0b-4ef8-bb6d-6bb9bd380a04', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c4eebc99-9c0b-4ef8-bb6d-6bb9bd380a04', 'OVERDUE_RECEIVABLE', 'INV_2026_09', 750000, 'INR', 'INVOICE_OVERDUE_30D', now() - INTERVAL '30 days');

-- 4. Subscriptions
INSERT INTO subscriptions (id, merchant_id, customer_id, external_subscription_id, status, amount_paise, renewal_at, failed_attempts) VALUES
('11eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 'SUB_EXT_PRO_PLAN', 'PAST_DUE', 2500000, now() + INTERVAL '30 days', 1);

-- 5. Recovery Policies
INSERT INTO recovery_policies (id, merchant_id, policy_name, rules_json, active) VALUES
('21eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Standard Customer LTV Protection Policy', '{"FIRST_TIME": "RETRY", "LOYAL": "GRACE_PERIOD", "PREMIUM": "SOFT_REMINDER", "HABITUAL_NON_PAYER": "ESCALATE"}'::jsonb, true);

-- 6. Recovery Cases
INSERT INTO recovery_cases (id, merchant_id, customer_id, revenue_event_id, status, scenario_type, amount_at_risk_paise, root_cause, diagnosis_confidence) VALUES
('31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'RECOVERED', 'PAYMENT_FAILURE', 149900, 'temporary_payment_failure', 0.92),
('31eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 'e2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 'APPROVED', 'CHECKOUT_ABANDONMENT', 499000, 'abandoned_intent', 0.88),
('31eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 'e3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 'APPROVED', 'SUBSCRIPTION_FAILURE', 2500000, 'card_expired', 0.95),
('31eebc99-9c0b-4ef8-bb6d-6bb9bd380a04', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c4eebc99-9c0b-4ef8-bb6d-6bb9bd380a04', 'e4eebc99-9c0b-4ef8-bb6d-6bb9bd380a04', 'BLOCKED', 'OVERDUE_RECEIVABLE', 750000, 'habitual_delinquency', 0.85);

-- 7. Decisions
INSERT INTO decisions (id, recovery_case_id, diagnosis, compliance_result, recovery_right, recovery_score, selected_action, ai_rationale, ai_confidence, decision_mode, decided_at) VALUES
('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', '31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'temporary_payment_failure', 'APPROVED', 'RETRY', 104930.0, 'RETRY', 'First-time customer with temporary decline qualifies for instant retry.', 0.92, 'AI', now() - INTERVAL '1 hour');

-- 8. Recovery Actions
INSERT INTO recovery_actions (id, decision_id, action_type, channel, attempt_number, status, executed_at) VALUES
('a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'RETRY', 'PAYMENT', 1, 'SUCCESS', now() - INTERVAL '50 minutes');

-- 9. Recovery Outcomes
INSERT INTO recovery_outcomes (id, action_id, recovered, recovered_amount_paise, outcome_code, occurred_at) VALUES
('41eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', true, 149900, 'SIMULATED_RECOVERY_SUCCESS', now() - INTERVAL '50 minutes');

-- 10. Audit Events
INSERT INTO audit_events (id, recovery_case_id, event_type, actor_type, event_data_json, created_at) VALUES
('51eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', '31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'CASE_DETECTED', 'SYSTEM', '{"scenario": "PAYMENT_FAILURE", "amount_paise": 149900}'::jsonb, now() - INTERVAL '2 hours'),
('51eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', '31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'COMPLIANCE_CHECKED', 'RULE_ENGINE', '{"result": "APPROVED"}'::jsonb, now() - INTERVAL '1 hour 50 minutes'),
('51eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', '31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'RECOVERY_RIGHTS_APPLIED', 'RULE_ENGINE', '{"segment": "FIRST_TIME", "treatment": "RETRY"}'::jsonb, now() - INTERVAL '1 hour 45 minutes'),
('51eebc99-9c0b-4ef8-bb6d-6bb9bd380a04', '31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'DECISION_MADE', 'AI', '{"selected_action": "RETRY", "score": 104930.0}'::jsonb, now() - INTERVAL '1 hour'),
('51eebc99-9c0b-4ef8-bb6d-6bb9bd380a05', '31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'ACTION_EXECUTED', 'SYSTEM', '{"recovered": true, "amount_paise": 149900}'::jsonb, now() - INTERVAL '50 minutes');

-- 11. Idempotency Keys
INSERT INTO idempotency_keys (id, merchant_id, endpoint, idempotency_key, response_code, response_json) VALUES
('61eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '/api/v1/recovery-cases/execute', 'IDEM_KEY_SEED_001', 200, '{"success": true, "data": {"status": "SUCCESS"}}'::jsonb);

-- 12. Batch Runs
INSERT INTO batch_runs (id, merchant_id, strategy, total_cases, total_at_risk_paise, recovered_paise, recovery_rate, compliance_blocks) VALUES
('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'BASELINE', 4, 3898800, 149900, 0.0384, 0),
('b2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'NIRNAY_PAY', 4, 3898800, 3148900, 0.8076, 1);
