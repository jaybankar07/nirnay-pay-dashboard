from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.batch_run import BatchRun


class BatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, batch_run: BatchRun) -> BatchRun:
        self.db.add(batch_run)
        self.db.commit()
        self.db.refresh(batch_run)
        return batch_run

    def get_by_id(self, merchant_id: str, batch_run_id: str) -> Optional[BatchRun]:
        return self.db.query(BatchRun).filter(
            BatchRun.merchant_id == merchant_id,
            BatchRun.id == batch_run_id
        ).first()

    def list_by_merchant(self, merchant_id: str, limit: int = 20) -> List[BatchRun]:
        return self.db.query(BatchRun).filter(
            BatchRun.merchant_id == merchant_id
        ).order_by(BatchRun.created_at.desc()).limit(limit).all()
