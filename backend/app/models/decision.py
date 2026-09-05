from sqlalchemy import Column, String, Float, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import generate_uuid, utc_now
from app.utils.enums import ComplianceResult, RecoveryRightTreatment, ActionType, DecisionMode


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=generate_uuid)
    recovery_case_id = Column(String, ForeignKey("recovery_cases.id"), nullable=False, index=True)
    diagnosis = Column(String, nullable=True)
    compliance_result = Column(Enum(ComplianceResult), nullable=False)
    recovery_right = Column(Enum(RecoveryRightTreatment), nullable=False)
    recovery_score = Column(Float, nullable=True)
    selected_action = Column(Enum(ActionType), nullable=False)
    ai_rationale = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    decision_mode = Column(Enum(DecisionMode), nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="decisions")
    actions = relationship("RecoveryAction", back_populates="decision", cascade="all, delete-orphan")
