from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.merchant_service import MerchantService
from app.schemas.merchant import MerchantResponse
from app.schemas.common import StandardResponse

router = APIRouter(tags=["Merchants"])


@router.get("/merchants/{merchant_id}", response_model=StandardResponse[MerchantResponse])
def get_merchant(merchant_id: str, db: Session = Depends(get_db)):
    service = MerchantService(db)
    merchant = service.get_merchant(merchant_id)
    return StandardResponse(
        data=MerchantResponse(
            id=str(merchant.id),
            name=merchant.name,
            email=merchant.email
        )
    )
