from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import generate_uuid, utc_now
from app.utils.enums import AuditEventType, ActorType


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    recovery_case_id = Column(String, ForeignKey("recovery_cases.id"), nullable=False, index=True)
    event_type = Column(Enum(AuditEventType), nullable=False, index=True)
    actor_type = Column(Enum(ActorType), nullable=False)
    event_data_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True, default=utc_now)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="audit_events")
