from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import generate_uuid, utc_now


class RecoveryOutcome(Base):
    __tablename__ = "recovery_outcomes"

    id = Column(String, primary_key=True, default=generate_uuid)
    action_id = Column(String, ForeignKey("recovery_actions.id"), nullable=False, index=True)
    recovered = Column(Boolean, nullable=False, default=False)
    recovered_amount_paise = Column(Integer, nullable=False, default=0)
    outcome_code = Column(String, nullable=False)
    failure_reason = Column(String, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    action = relationship("RecoveryAction", back_populates="outcomes")
