import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict

class UserBase(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

    @model_validator(mode="after")
    def validate_email_or_phone(self) -> 'UserCreate':
        if not self.email and not self.phone_number:
            raise ValueError("Ro'yxatdan o'tish uchun email yoki telefon raqamidan kamida bittasini to'ldirish shart.")
        return self

class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
