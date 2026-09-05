from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, UniqueConstraint
from app.database.session import Base
from app.models.base import generate_uuid, utc_now


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    idempotency_key = Column(String, nullable=False)
    response_code = Column(Integer, nullable=False)
    response_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("merchant_id", "endpoint", "idempotency_key", name="uq_idempotency"),
    )
