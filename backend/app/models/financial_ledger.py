"""
Authoritative Financial Recovery Ledger Model for Nirnay Pay (RecoveryOS).
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.database.session import Base


class FinancialLedgerEntry(Base):
    __tablename__ = "financial_ledger_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True)
    recovery_case_id = Column(String(36), nullable=False, index=True)
    execution_action_id = Column(String(36), nullable=True)
    idempotency_key = Column(String(128), nullable=True, index=True)
    amount_at_risk_paise = Column(Integer, nullable=False)
    recovered_amount_paise = Column(Integer, nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="INR")
    execution_status = Column(String(32), nullable=False)
    reconciliation_status = Column(String(32), nullable=False, default="MATCHED")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "recovery_case_id": self.recovery_case_id,
            "execution_action_id": self.execution_action_id,
            "idempotency_key": self.idempotency_key,
            "amount_at_risk_paise": self.amount_at_risk_paise,
            "recovered_amount_paise": self.recovered_amount_paise,
            "currency": self.currency,
            "execution_status": self.execution_status,
            "reconciliation_status": self.reconciliation_status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
