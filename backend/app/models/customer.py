from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import generate_uuid, utc_now
from app.utils.enums import CustomerSegment


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    external_customer_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    customer_segment = Column(Enum(CustomerSegment), nullable=False, default=CustomerSegment.FIRST_TIME)
    tenure_days = Column(Integer, nullable=False, default=0)
    lifetime_value_paise = Column(Integer, nullable=False, default=0)
    successful_payment_count = Column(Integer, nullable=False, default=0)
    failed_payment_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("merchant_id", "external_customer_id", name="uq_merchant_customer"),
    )

    # Relationships
    merchant = relationship("Merchant", back_populates="customers")
    subscriptions = relationship("Subscription", back_populates="customer", cascade="all, delete-orphan")
    revenue_events = relationship("RevenueEvent", back_populates="customer")
    recovery_cases = relationship("RecoveryCase", back_populates="customer")
