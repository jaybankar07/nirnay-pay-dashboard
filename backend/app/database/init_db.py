import app.models
from app.database.session import Base, engine, SessionLocal
from app.models.merchant import Merchant
from app.models.recovery_policy import RecoveryPolicy

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        merchants_to_seed = [
            ("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", "Apex SaaS Technologies", "finance@apexsast.com"),
            ("b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22", "Nirnay Merchant Corp", "merchant@nirnaypay.com")
        ]

        for m_id, m_name, m_email in merchants_to_seed:
            existing = db.query(Merchant).filter(Merchant.id == m_id).first()
            if not existing:
                merchant = Merchant(id=m_id, name=m_name, email=m_email)
                db.add(merchant)
                db.commit()

            # Seed Recovery Policy
            policy = db.query(RecoveryPolicy).filter(RecoveryPolicy.merchant_id == m_id).first()
            if not policy:
                default_policy = RecoveryPolicy(
                    merchant_id=m_id,
                    policy_name="Standard Customer LTV Protection Policy",
                    rules_json={
                        "FIRST_TIME": "RETRY",
                        "LOYAL": "GRACE_PERIOD",
                        "PREMIUM": "SOFT_REMINDER",
                        "HIGH_VALUE": "GRACE_PERIOD",
                        "HABITUAL_NON_PAYER": "ESCALATE"
                    },
                    active=True
                )
                db.add(default_policy)
                db.commit()
    finally:
        db.close()
