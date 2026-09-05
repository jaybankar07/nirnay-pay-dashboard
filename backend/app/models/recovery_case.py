from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import generate_uuid, utc_now
from app.utils.enums import RecoveryCaseStatus, RevenueEventType


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    revenue_event_id = Column(String, ForeignKey("revenue_events.id"), nullable=False, index=True)
    status = Column(Enum(RecoveryCaseStatus), nullable=False, default=RecoveryCaseStatus.DETECTED, index=True)
    scenario_type = Column(Enum(RevenueEventType), nullable=False, index=True)
    amount_at_risk_paise = Column(Integer, nullable=False)
    root_cause = Column(String, nullable=True)
    diagnosis_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="recovery_cases")
    customer = relationship("Customer", back_populates="recovery_cases")
    revenue_event = relationship("RevenueEvent", back_populates="recovery_cases")
    decisions = relationship("Decision", back_populates="recovery_case", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="recovery_case", cascade="all, delete-orphan")
