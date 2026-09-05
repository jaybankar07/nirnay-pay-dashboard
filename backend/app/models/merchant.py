from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import generate_uuid, utc_now


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")
    revenue_events = relationship("RevenueEvent", back_populates="merchant", cascade="all, delete-orphan")
    recovery_cases = relationship("RecoveryCase", back_populates="merchant", cascade="all, delete-orphan")
    recovery_policies = relationship("RecoveryPolicy", back_populates="merchant", cascade="all, delete-orphan")
    batch_runs = relationship("BatchRun", back_populates="merchant", cascade="all, delete-orphan")
