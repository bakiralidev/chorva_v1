import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict

class UserBase(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    accepted_offer: bool = Field(..., description="Foydalanish shartlariga (Oferta) rozilik")

    @model_validator(mode="after")
    def validate_email_or_phone(self) -> 'UserCreate':
        if not self.email and not self.phone_number:
            raise ValueError("Ro'yxatdan o'tish uchun email yoki telefon raqamidan kamida bittasini to'ldirish shart.")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "phone_number": "+998901234567",
                "password": "strongpassword123",
                "accepted_offer": True
            }
        }
    )

class VerifyCode(BaseModel):
    username: str = Field(..., description="Email yoki telefon raqami")
    code: str = Field(..., min_length=6, max_length=6, description="6 xonali tasdiqlash kodi")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "+998901234567",
                "code": "123456"
            }
        }
    )

class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "phone_number": "+998901234567",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2026-06-27T00:00:00Z"
            }
        }
    )

class UserRegisterResponse(BaseModel):
    user: UserResponse
    verification_code: str
    message: str = "Tasdiqlash kodi yuborildi"

