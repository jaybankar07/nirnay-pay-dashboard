from typing import Optional
from sqlalchemy.orm import Session
from app.models.merchant import Merchant


class MerchantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, merchant_id: str) -> Optional[Merchant]:
        return self.db.query(Merchant).filter(Merchant.id == merchant_id).first()

    def get_by_email(self, email: str) -> Optional[Merchant]:
        return self.db.query(Merchant).filter(Merchant.email == email).first()

    def create(self, merchant: Merchant) -> Merchant:
        self.db.add(merchant)
        self.db.commit()
        self.db.refresh(merchant)
        return merchant
