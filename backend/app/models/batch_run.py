from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import generate_uuid, utc_now
from app.utils.enums import BatchStrategy


class BatchRun(Base):
    __tablename__ = "batch_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    strategy = Column(Enum(BatchStrategy), nullable=False)
    total_cases = Column(Integer, nullable=False, default=0)
    total_at_risk_paise = Column(Integer, nullable=False, default=0)
    recovered_paise = Column(Integer, nullable=False, default=0)
    recovery_rate = Column(Float, nullable=False, default=0.0)
    compliance_blocks = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="batch_runs")
