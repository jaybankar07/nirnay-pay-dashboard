from pydantic import BaseModel, EmailStr


class MerchantResponse(BaseModel):
    id: str
    name: str
    email: str
