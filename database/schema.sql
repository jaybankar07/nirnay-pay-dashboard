-- =============================================================================
-- Nirnay Pay (RecoveryOS) — Supabase PostgreSQL Production DDL Schema
-- Strict 12 Business Tables Only
-- =============================================================================

-- Enable extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing tables in reverse dependency order if resetting
DROP TABLE IF EXISTS batch_runs CASCADE;
DROP TABLE IF EXISTS idempotency_keys CASCADE;
DROP TABLE IF EXISTS audit_events CASCADE;
DROP TABLE IF EXISTS recovery_outcomes CASCADE;
DROP TABLE IF EXISTS recovery_actions CASCADE;
DROP TABLE IF EXISTS decisions CASCADE;
DROP TABLE IF EXISTS recovery_cases CASCADE;
DROP TABLE IF EXISTS recovery_policies CASCADE;
DROP TABLE IF EXISTS subscriptions CASCADE;
DROP TABLE IF EXISTS revenue_events CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS merchants CASCADE;

-- -----------------------------------------------------------------------------
-- 1. TABLE: merchants
-- -----------------------------------------------------------------------------
CREATE TABLE merchants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 2. TABLE: customers
-- -----------------------------------------------------------------------------
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    external_customer_id TEXT NOT NULL,
    name TEXT,
    email TEXT,
    customer_segment TEXT NOT NULL CHECK (customer_segment IN ('FIRST_TIME', 'LOYAL', 'PREMIUM', 'HABITUAL_NON_PAYER')),
    tenure_days INTEGER NOT NULL DEFAULT 0 CHECK (tenure_days >= 0),
    lifetime_value_paise BIGINT NOT NULL DEFAULT 0 CHECK (lifetime_value_paise >= 0),
    successful_payment_count INTEGER NOT NULL DEFAULT 0 CHECK (successful_payment_count >= 0),
    failed_payment_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_payment_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_customers_merchant_external_id UNIQUE (merchant_id, external_customer_id)
);

-- -----------------------------------------------------------------------------
-- 3. TABLE: revenue_events
-- -----------------------------------------------------------------------------
CREATE TABLE revenue_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type IN ('PAYMENT_FAILURE', 'CHECKOUT_ABANDONMENT', 'SUBSCRIPTION_FAILURE', 'OVERDUE_RECEIVABLE')),
    external_reference TEXT,
    amount_paise BIGINT NOT NULL CHECK (amount_paise >= 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    reason_code TEXT,
    metadata_json JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 4. TABLE: subscriptions
-- -----------------------------------------------------------------------------
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    external_subscription_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'PAST_DUE', 'CANCELLED', 'EXPIRED')),
    amount_paise BIGINT NOT NULL CHECK (amount_paise >= 0),
    renewal_at TIMESTAMPTZ,
    failed_attempts INTEGER NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_subscriptions_merchant_ext_id UNIQUE (merchant_id, external_subscription_id)
);

-- -----------------------------------------------------------------------------
-- 5. TABLE: recovery_policies
-- -----------------------------------------------------------------------------
CREATE TABLE recovery_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    policy_name TEXT NOT NULL,
    rules_json JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 6. TABLE: recovery_cases
-- -----------------------------------------------------------------------------
CREATE TABLE recovery_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    revenue_event_id UUID NOT NULL REFERENCES revenue_events(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'DETECTED' CHECK (status IN ('DETECTED', 'DIAGNOSED', 'IN_REVIEW', 'APPROVED', 'EXECUTED', 'STOPPED', 'RECOVERED', 'FAILED', 'BLOCKED')),
    scenario_type TEXT NOT NULL CHECK (scenario_type IN ('PAYMENT_FAILURE', 'CHECKOUT_ABANDONMENT', 'SUBSCRIPTION_FAILURE', 'OVERDUE_RECEIVABLE')),
    amount_at_risk_paise BIGINT NOT NULL CHECK (amount_at_risk_paise >= 0),
    root_cause TEXT,
    diagnosis_confidence NUMERIC CHECK (diagnosis_confidence IS NULL OR (diagnosis_confidence >= 0 AND diagnosis_confidence <= 1)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 7. TABLE: decisions
-- -----------------------------------------------------------------------------
CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recovery_case_id UUID NOT NULL REFERENCES recovery_cases(id) ON DELETE RESTRICT,
    diagnosis TEXT,
    compliance_result TEXT NOT NULL CHECK (compliance_result IN ('APPROVED', 'BLOCKED')),
    recovery_right TEXT NOT NULL CHECK (recovery_right IN ('RETRY', 'GRACE_PERIOD', 'SOFT_REMINDER', 'ESCALATE', 'HUMAN_REVIEW', 'STOP')),
    recovery_score NUMERIC NOT NULL DEFAULT 0.0,
    selected_action TEXT NOT NULL CHECK (selected_action IN ('RETRY', 'WAIT', 'REMINDER', 'ESCALATE', 'HUMAN_REVIEW', 'STOP')),
    ai_rationale TEXT,
    ai_confidence NUMERIC CHECK (ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)),
    decision_mode TEXT NOT NULL DEFAULT 'RULE' CHECK (decision_mode IN ('AI', 'RULE', 'FALLBACK')),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 8. TABLE: recovery_actions
-- -----------------------------------------------------------------------------
CREATE TABLE recovery_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES decisions(id) ON DELETE RESTRICT,
    action_type TEXT NOT NULL CHECK (action_type IN ('RETRY', 'WAIT', 'REMINDER', 'ESCALATE', 'HUMAN_REVIEW', 'STOP')),
    channel TEXT CHECK (channel IS NULL OR channel IN ('PAYMENT', 'WHATSAPP', 'EMAIL', 'SMS', 'CALL', 'MANUAL', 'SYSTEM', 'HUMAN')),
    attempt_number INTEGER NOT NULL DEFAULT 1 CHECK (attempt_number > 0),
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SUCCESS', 'FAILED', 'BLOCKED')),
    scheduled_at TIMESTAMPTZ,
    executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 9. TABLE: recovery_outcomes
-- -----------------------------------------------------------------------------
CREATE TABLE recovery_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_id UUID NOT NULL REFERENCES recovery_actions(id) ON DELETE RESTRICT,
    recovered BOOLEAN NOT NULL DEFAULT false,
    recovered_amount_paise BIGINT NOT NULL DEFAULT 0 CHECK (recovered_amount_paise >= 0),
    outcome_code TEXT NOT NULL,
    failure_reason TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_recovered_amount_logic CHECK (recovered = true OR recovered_amount_paise = 0)
);

-- -----------------------------------------------------------------------------
-- 10. TABLE: audit_events (Append-only immutable trail)
-- -----------------------------------------------------------------------------
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recovery_case_id UUID NOT NULL REFERENCES recovery_cases(id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type IN ('CASE_DETECTED', 'DIAGNOSIS_COMPLETED', 'COMPLIANCE_CHECKED', 'RECOVERY_RIGHTS_APPLIED', 'SCORE_CALCULATED', 'DECISION_MADE', 'ACTION_EXECUTED', 'ACTION_FAILED', 'CASE_STOPPED', 'AUDIT_CREATED')),
    actor_type TEXT NOT NULL CHECK (actor_type IN ('SYSTEM', 'RULE_ENGINE', 'RULE', 'AI', 'MERCHANT', 'HUMAN', 'HUMAN_REVIEW')),
    event_data_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 11. TABLE: idempotency_keys
-- -----------------------------------------------------------------------------
CREATE TABLE idempotency_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    endpoint TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    response_code INTEGER NOT NULL,
    response_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_idempotency_merchant_endpoint_key UNIQUE (merchant_id, endpoint, idempotency_key)
);

-- -----------------------------------------------------------------------------
-- 12. TABLE: batch_runs
-- -----------------------------------------------------------------------------
CREATE TABLE batch_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    strategy TEXT NOT NULL CHECK (strategy IN ('BASELINE', 'NIRNAY_PAY')),
    total_cases INTEGER NOT NULL CHECK (total_cases >= 0),
    total_at_risk_paise BIGINT NOT NULL CHECK (total_at_risk_paise >= 0),
    recovered_paise BIGINT NOT NULL CHECK (recovered_paise >= 0),
    recovery_rate NUMERIC NOT NULL CHECK (recovery_rate >= 0 AND recovery_rate <= 1),
    compliance_blocks INTEGER NOT NULL CHECK (compliance_blocks >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- customers
CREATE INDEX idx_customers_merchant_ext ON customers (merchant_id, external_customer_id);

-- revenue_events
CREATE INDEX idx_revenue_events_merchant_type ON revenue_events (merchant_id, event_type);
CREATE INDEX idx_revenue_events_merchant_occurred ON revenue_events (merchant_id, occurred_at);
CREATE INDEX idx_revenue_events_customer_occurred ON revenue_events (customer_id, occurred_at);

-- recovery_cases
CREATE INDEX idx_recovery_cases_merchant_status ON recovery_cases (merchant_id, status);
CREATE INDEX idx_recovery_cases_merchant_scenario ON recovery_cases (merchant_id, scenario_type);
CREATE INDEX idx_recovery_cases_merchant_created ON recovery_cases (merchant_id, created_at);
CREATE INDEX idx_recovery_cases_customer_status ON recovery_cases (customer_id, status);

-- decisions
CREATE INDEX idx_decisions_case ON decisions (recovery_case_id);

-- recovery_actions
CREATE INDEX idx_recovery_actions_decision ON recovery_actions (decision_id);
CREATE INDEX idx_recovery_actions_status ON recovery_actions (status);
CREATE INDEX idx_recovery_actions_executed ON recovery_actions (executed_at);

-- recovery_outcomes
CREATE INDEX idx_recovery_outcomes_action ON recovery_outcomes (action_id);

-- audit_events
CREATE INDEX idx_audit_events_case_created ON audit_events (recovery_case_id, created_at);
CREATE INDEX idx_audit_events_type_created ON audit_events (event_type, created_at);

-- batch_runs
CREATE INDEX idx_batch_runs_merchant_created ON batch_runs (merchant_id, created_at);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) CONFIGURATION
-- =============================================================================

ALTER TABLE merchants ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE revenue_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recovery_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE recovery_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recovery_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recovery_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE idempotency_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_runs ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'service_role_all') THEN
        CREATE POLICY service_role_all ON merchants FOR ALL USING (true);
        CREATE POLICY service_role_all ON customers FOR ALL USING (true);
        CREATE POLICY service_role_all ON revenue_events FOR ALL USING (true);
        CREATE POLICY service_role_all ON subscriptions FOR ALL USING (true);
        CREATE POLICY service_role_all ON recovery_policies FOR ALL USING (true);
        CREATE POLICY service_role_all ON recovery_cases FOR ALL USING (true);
        CREATE POLICY service_role_all ON decisions FOR ALL USING (true);
        CREATE POLICY service_role_all ON recovery_actions FOR ALL USING (true);
        CREATE POLICY service_role_all ON recovery_outcomes FOR ALL USING (true);
        CREATE POLICY service_role_all ON audit_events FOR ALL USING (true);
        CREATE POLICY service_role_all ON idempotency_keys FOR ALL USING (true);
        CREATE POLICY service_role_all ON batch_runs FOR ALL USING (true);
    END IF;
END $$;
