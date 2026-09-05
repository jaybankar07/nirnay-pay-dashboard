from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import generate_uuid, utc_now
from app.utils.enums import RevenueEventType


class RevenueEvent(Base):
    __tablename__ = "revenue_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    event_type = Column(Enum(RevenueEventType), nullable=False, index=True)
    external_reference = Column(String, nullable=True)
    amount_paise = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, default="INR")
    reason_code = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True, default=utc_now)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="revenue_events")
    customer = relationship("Customer", back_populates="revenue_events")
    recovery_cases = relationship("RecoveryCase", back_populates="revenue_event", cascade="all, delete-orphan")
