from typing import Optional
from sqlalchemy.orm import Session
from app.models.merchant import Merchant
from app.repositories.merchant_repository import MerchantRepository
from app.core.exceptions import NotFoundError


class MerchantService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MerchantRepository(db)

    def get_merchant(self, merchant_id: str) -> Merchant:
        merchant = self.repo.get_by_id(merchant_id)
        if not merchant:
            raise NotFoundError(f"Merchant '{merchant_id}' not found.")
        return merchant
