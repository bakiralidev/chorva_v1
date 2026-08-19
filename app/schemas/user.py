import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict


# ─── Asosiy foydalanuvchi sxemalari ─────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = None
    telegram_username: str | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = None
    telegram_username: str | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Parol kamida 6 ta belgidan iborat bo'lishi shart")
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
    full_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    auth_provider: str = "local"
    preferred_lang: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "phone_number": "+998901234567",
                "full_name": "Abdulloh Karimov",
                "first_name": "Abdulloh",
                "last_name": "Karimov",
                "avatar_url": "https://api.chorva.uz/media/avatars/uuid.jpg",
                "auth_provider": "local",
                "preferred_lang": "uz",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2026-06-27T00:00:00Z"
            }
        }
    )


class UserRegisterResponse(BaseModel):
    """
    Ro'yxatdan o'tish javob sxemasi.
    otp_channel: "telegram" | "email" | "console"
    """
    user: UserResponse
    message: str = "Tasdiqlash kodi yuborildi"
    otp_channel: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "phone_number": "+998901234567",
                    "auth_provider": "local",
                    "is_active": False,
                    "is_superuser": False,
                    "created_at": "2026-06-27T00:00:00Z"
                },
                "message": "Tasdiqlash kodi Telegram orqali yuborildi",
                "otp_channel": "telegram"
            }
        }
    )


class GoogleAuthResponse(BaseModel):
    """Google OAuth2 kirish jarayoni boshlanganda qaytariladigan URL."""
    authorization_url: str = Field(..., description="Foydalanuvchini yo'naltirish kerak bo'lgan Google URL")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
            }
        }
    )


# ─── Email OTP-only (parolsiz) autentifikatsiya sxemalari ───────────────────

class OtpRequestSchema(BaseModel):
    """
    Email OTP so'rash sxemasi.
    Foydalanuvchi faqat email manzilini yuboradi.
    """
    email: EmailStr = Field(..., description="Email manzil")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class OtpRequestResponse(BaseModel):
    """OTP so'rash muvaffaqiyatli bo'lganda qaytariladigan javob."""
    message: str
    expires_in: int = Field(..., description="OTP necha soniyada amal qiladi")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Tasdiqlash kodi user@example.com ga yuborildi.",
                "expires_in": 300
            }
        }
    )


class OtpVerifySchema(BaseModel):
    """
    Email OTP tasdiqlash sxemasi.
    Email va 6 xonali kod yuboriladi.
    """
    email: EmailStr = Field(..., description="Email manzil")
    code: str = Field(..., min_length=6, max_length=6, description="6 xonali OTP kodi")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "code": "123456"
            }
        }
    )


# ─── Profil tahrirlash sxemalari ────────────────────────────────────────────

class UserNameUpdate(BaseModel):
    """Ism va familyani yangilash sxemasi."""
    first_name: str = Field(..., min_length=2, max_length=150, description="Ism (kamida 2 belgi)")
    last_name: str = Field(..., min_length=2, max_length=150, description="Familya (kamida 2 belgi)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Bobur",
                "last_name": "Karimov"
            }
        }
    )


class EmailChangeRequest(BaseModel):
    """Yangi email manzilini so'rash (OTP yuboriladi)."""
    new_email: EmailStr = Field(..., description="Yangi email manzil")

    model_config = ConfigDict(
        json_schema_extra={"example": {"new_email": "newemail@example.com"}}
    )


class EmailChangeConfirm(BaseModel):
    """OTP kod bilan email o'zgartirishni tasdiqlash."""
    new_email: EmailStr = Field(..., description="Yangi email manzil")
    code: str = Field(..., min_length=6, max_length=6, description="6 xonali tasdiqlash kodi")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_email": "newemail@example.com",
                "code": "123456"
            }
        }
    )


class PasswordChange(BaseModel):
    """Parolni o'zgartirish sxemasi."""
    old_password: str = Field(..., description="Joriy (eski) parol")
    new_password: str = Field(..., min_length=6, description="Yangi parol (kamida 6 belgi)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "old_password": "oldpassword123",
                "new_password": "newpassword456"
            }
        }
    )


class PhoneChangeRequest(BaseModel):
    """Telefon raqam qo'shish/o'zgartirish — Telegram OTP yuboriladi."""
    phone_number: str = Field(..., description="Yangi telefon raqam (+998XXXXXXXXX)")

    model_config = ConfigDict(
        json_schema_extra={"example": {"phone_number": "+998901234567"}}
    )


class PhoneChangeConfirm(BaseModel):
    """OTP kod bilan telefon raqamni tasdiqlash."""
    phone_number: str = Field(..., description="Yangi telefon raqam (+998XXXXXXXXX)")
    code: str = Field(..., min_length=6, max_length=6, description="6 xonali tasdiqlash kodi")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone_number": "+998901234567",
                "code": "123456"
            }
        }
    )


class MessageResponse(BaseModel):
    """Oddiy xabar javobi."""
    message: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Muvaffaqiyatli bajarildi."}}
    )


class TelegramLoginRequest(BaseModel):
    """Telegram Mini App initData bilan login qilish."""
    init_data: str = Field(
        ...,
        description="Telegram.WebApp.initData string (frontend JS dan olinadi)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "init_data": "query_id=AAH...&user=%7B%22id%22%3A123456789...&hash=abc123"
            }
        }
    )
