from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import generate_uuid, utc_now
from app.utils.enums import ActionType, ChannelType, ActionStatus


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(String, primary_key=True, default=generate_uuid)
    decision_id = Column(String, ForeignKey("decisions.id"), nullable=False, index=True)
    action_type = Column(Enum(ActionType), nullable=False)
    channel = Column(Enum(ChannelType), nullable=True)
    attempt_number = Column(Integer, nullable=False, default=1)
    status = Column(Enum(ActionStatus), nullable=False, default=ActionStatus.PENDING)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    decision = relationship("Decision", back_populates="actions")
    outcomes = relationship("RecoveryOutcome", back_populates="action", cascade="all, delete-orphan")
