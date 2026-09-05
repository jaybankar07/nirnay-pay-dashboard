import os
import sys
import random
from datetime import datetime, timezone, timedelta

# Ensure backend app is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import SessionLocal, engine, Base
from app.models import (
    Merchant, Customer, RevenueEvent, Subscription, RecoveryCase,
    RecoveryPolicy, Decision, RecoveryAction, RecoveryOutcome, AuditEvent
)
from app.utils.enums import (
    CustomerSegment, RevenueEventType, SubscriptionStatus,
    RecoveryCaseStatus, ComplianceResult, RecoveryRightTreatment,
    ActionType, ChannelType, ActionStatus, DecisionMode, AuditEventType, ActorType
)


def seed_database():
    random.seed(42)  # Fixed seed for reproducibility

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Merchant).filter(Merchant.id == "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11").first():
            print("Database already seeded. Skipping.")
            return

        print("Seeding synthetic data...")

        # 1. Create Demo Merchant
        merchant = Merchant(
            id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            name="Apex SaaS Technologies",
            email="finance@apexsast.com"
        )
        db.add(merchant)
        db.commit()

        # 2. Create Merchant Recovery Policy (Configurable Recovery Rights)
        policy_rules = {
            "FIRST_TIME": "RETRY",
            "LOYAL": "GRACE_PERIOD",
            "PREMIUM": "SOFT_REMINDER",
            "HABITUAL_NON_PAYER": "ESCALATE"
        }
        policy = RecoveryPolicy(
            id="21eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
            merchant_id=merchant.id,
            policy_name="Standard Customer LTV Protection Policy",
            rules_json=policy_rules,
            active=True
        )
        db.add(policy)

        # 3. Create Synthetic Customers across 4 Customer Segments
        customers = [
            Customer(
                id="c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                merchant_id=merchant.id,
                external_customer_id="EXT_CUST_FIRST_TIME",
                name="Ananya Sharma",
                email="ananya@example.com",
                customer_segment=CustomerSegment.FIRST_TIME,
                tenure_days=10,
                lifetime_value_paise=149900,
                successful_payment_count=1,
                failed_payment_count=1
            ),
            Customer(
                id="c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02",
                merchant_id=merchant.id,
                external_customer_id="EXT_CUST_LOYAL",
                name="Rahul Verma",
                email="rahul@example.com",
                customer_segment=CustomerSegment.LOYAL,
                tenure_days=365,
                lifetime_value_paise=2499000,
                successful_payment_count=12,
                failed_payment_count=0
            ),
            Customer(
                id="c3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03",
                merchant_id=merchant.id,
                external_customer_id="EXT_CUST_PREMIUM",
                name="Enterprise Corp India",
                email="billing@enterprisecorp.in",
                customer_segment=CustomerSegment.PREMIUM,
                tenure_days=720,
                lifetime_value_paise=15000000,
                successful_payment_count=24,
                failed_payment_count=0
            ),
            Customer(
                id="c4eebc99-9c0b-4ef8-bb6d-6bb9bd380a04",
                merchant_id=merchant.id,
                external_customer_id="EXT_CUST_HABITUAL",
                name="Vikram Singh",
                email="vikram@example.com",
                customer_segment=CustomerSegment.HABITUAL_NON_PAYER,
                tenure_days=90,
                lifetime_value_paise=49900,
                successful_payment_count=1,
                failed_payment_count=4
            ),
        ]
        db.add_all(customers)
        db.commit()

        # 4. Create Revenue Events for 4 Revenue Scenarios
        events = [
            # Payment Failure
            RevenueEvent(
                id="e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                merchant_id=merchant.id,
                customer_id="c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                event_type=RevenueEventType.PAYMENT_FAILURE,
                external_reference="PAY_REF_1001",
                amount_paise=149900,
                reason_code="TEMPORARY_DECLINE",
                occurred_at=datetime.now(timezone.utc) - timedelta(hours=2)
            ),
            # Checkout Abandonment
            RevenueEvent(
                id="e2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02",
                merchant_id=merchant.id,
                customer_id="c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02",
                event_type=RevenueEventType.CHECKOUT_ABANDONMENT,
                external_reference="CART_9002",
                amount_paise=499000,
                reason_code="CART_TIMEOUT",
                occurred_at=datetime.now(timezone.utc) - timedelta(hours=5)
            ),
            # Subscription Failure
            RevenueEvent(
                id="e3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03",
                merchant_id=merchant.id,
                customer_id="c3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03",
                event_type=RevenueEventType.SUBSCRIPTION_FAILURE,
                external_reference="SUB_RENEWAL_88",
                amount_paise=2500000,
                reason_code="CARD_EXPIRED",
                occurred_at=datetime.now(timezone.utc) - timedelta(days=1)
            ),
            # Overdue B2B Receivable
            RevenueEvent(
                id="e4eebc99-9c0b-4ef8-bb6d-6bb9bd380a04",
                merchant_id=merchant.id,
                customer_id="c4eebc99-9c0b-4ef8-bb6d-6bb9bd380a04",
                event_type=RevenueEventType.OVERDUE_RECEIVABLE,
                external_reference="INV_2026_09",
                amount_paise=750000,
                reason_code="INVOICE_OVERDUE_30D",
                occurred_at=datetime.now(timezone.utc) - timedelta(days=30)
            )
        ]
        db.add_all(events)
        db.commit()

        # 5. Create Recovery Cases
        cases = [
            RecoveryCase(
                id="31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                merchant_id=merchant.id,
                customer_id="c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                revenue_event_id="e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                status=RecoveryCaseStatus.RECOVERED,
                scenario_type=RevenueEventType.PAYMENT_FAILURE,
                amount_at_risk_paise=149900,
                root_cause="temporary_payment_failure",
                diagnosis_confidence=0.92
            ),
            RecoveryCase(
                id="31eebc99-9c0b-4ef8-bb6d-6bb9bd380a02",
                merchant_id=merchant.id,
                customer_id="c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02",
                revenue_event_id="e2eebc99-9c0b-4ef8-bb6d-6bb9bd380a02",
                status=RecoveryCaseStatus.APPROVED,
                scenario_type=RevenueEventType.CHECKOUT_ABANDONMENT,
                amount_at_risk_paise=499000,
                root_cause="abandoned_intent",
                diagnosis_confidence=0.88
            ),
            RecoveryCase(
                id="31eebc99-9c0b-4ef8-bb6d-6bb9bd380a03",
                merchant_id=merchant.id,
                customer_id="c3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03",
                revenue_event_id="e3eebc99-9c0b-4ef8-bb6d-6bb9bd380a03",
                status=RecoveryCaseStatus.APPROVED,
                scenario_type=RevenueEventType.SUBSCRIPTION_FAILURE,
                amount_at_risk_paise=2500000,
                root_cause="card_expired",
                diagnosis_confidence=0.95
            ),
            RecoveryCase(
                id="31eebc99-9c0b-4ef8-bb6d-6bb9bd380a04",
                merchant_id=merchant.id,
                customer_id="c4eebc99-9c0b-4ef8-bb6d-6bb9bd380a04",
                revenue_event_id="e4eebc99-9c0b-4ef8-bb6d-6bb9bd380a04",
                status=RecoveryCaseStatus.BLOCKED,
                scenario_type=RevenueEventType.OVERDUE_RECEIVABLE,
                amount_at_risk_paise=750000,
                root_cause="habitual_delinquency",
                diagnosis_confidence=0.85
            )
        ]
        db.add_all(cases)
        db.commit()

        # 6. Create Decisions, Actions, and Outcomes for Case 1 (Successful Recovery)
        decision_1 = Decision(
            id="d1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
            recovery_case_id="31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
            diagnosis="temporary_payment_failure",
            compliance_result=ComplianceResult.APPROVED,
            recovery_right=RecoveryRightTreatment.RETRY,
            recovery_score=104930.0,
            selected_action=ActionType.RETRY,
            ai_rationale="First-time customer with temporary decline qualifies for instant retry.",
            ai_confidence=0.92,
            decision_mode=DecisionMode.AI
        )
        db.add(decision_1)
        db.commit()

        action_1 = RecoveryAction(
            id="a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
            decision_id="d1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
            action_type=ActionType.RETRY,
            channel=ChannelType.PAYMENT,
            attempt_number=1,
            status=ActionStatus.SUCCESS,
            executed_at=datetime.now(timezone.utc)
        )
        db.add(action_1)
        db.commit()

        outcome_1 = RecoveryOutcome(
            id="41eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
            action_id="a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
            recovered=True,
            recovered_amount_paise=149900,
            outcome_code="SIMULATED_RECOVERY_SUCCESS"
        )
        db.add(outcome_1)
        db.commit()

        # 7. Audit Events
        audit_events = [
            AuditEvent(
                recovery_case_id="31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                event_type=AuditEventType.CASE_DETECTED,
                actor_type=ActorType.SYSTEM,
                event_data_json={"scenario": "PAYMENT_FAILURE", "amount_paise": 149900}
            ),
            AuditEvent(
                recovery_case_id="31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                event_type=AuditEventType.COMPLIANCE_CHECKED,
                actor_type=ActorType.RULE,
                event_data_json={"result": "APPROVED"}
            ),
            AuditEvent(
                recovery_case_id="31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                event_type=AuditEventType.RECOVERY_RIGHTS_APPLIED,
                actor_type=ActorType.RULE,
                event_data_json={"segment": "FIRST_TIME", "treatment": "RETRY"}
            ),
            AuditEvent(
                recovery_case_id="31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                event_type=AuditEventType.DECISION_MADE,
                actor_type=ActorType.AI,
                event_data_json={"selected_action": "RETRY", "score": 104930.0}
            ),
            AuditEvent(
                recovery_case_id="31eebc99-9c0b-4ef8-bb6d-6bb9bd380a01",
                event_type=AuditEventType.ACTION_EXECUTED,
                actor_type=ActorType.SYSTEM,
                event_data_json={"recovered": True, "amount_paise": 149900}
            )
        ]
        db.add_all(audit_events)
        db.commit()

        print("Database seed completed successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
