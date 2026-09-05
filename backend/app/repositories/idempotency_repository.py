from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.idempotency_key import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, merchant_id: str, endpoint: str, idempotency_key: str) -> Optional[IdempotencyKey]:
        return self.db.query(IdempotencyKey).filter(
            IdempotencyKey.merchant_id == merchant_id,
            IdempotencyKey.endpoint == endpoint,
            IdempotencyKey.idempotency_key == idempotency_key
        ).first()

    def create(
        self,
        merchant_id: str,
        endpoint: str,
        idempotency_key: str,
        response_code: int,
        response_json: dict
    ) -> IdempotencyKey:
        key_record = IdempotencyKey(
            merchant_id=merchant_id,
            endpoint=endpoint,
            idempotency_key=idempotency_key,
            response_code=response_code,
            response_json=response_json
        )
        self.db.add(key_record)
        try:
            self.db.commit()
            self.db.refresh(key_record)
            return key_record
        except IntegrityError:
            self.db.rollback()
            # Unique constraint caught concurrent duplicate insertion
            return self.get(merchant_id, endpoint, idempotency_key)
