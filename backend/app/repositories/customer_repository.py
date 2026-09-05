from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, merchant_id: str, customer_id: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(
            Customer.merchant_id == merchant_id,
            Customer.id == customer_id
        ).first()

    def get_by_external_id(self, merchant_id: str, external_customer_id: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(
            Customer.merchant_id == merchant_id,
            Customer.external_customer_id == external_customer_id
        ).first()

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def list_by_merchant(self, merchant_id: str, limit: int = 50, offset: int = 0) -> List[Customer]:
        return self.db.query(Customer).filter(
            Customer.merchant_id == merchant_id
        ).offset(offset).limit(limit).all()
