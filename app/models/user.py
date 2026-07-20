import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)

    # hashed_password nullable — Google OAuth2 foydalanuvchilari uchun parol bo'lmaydi
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    accepted_offer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    preferred_lang: Mapped[str | None] = mapped_column(String(10), nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Telegram bot bilan bog'liq — OTP yuborish uchun chat_id
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Google OAuth2 ma'lumotlari
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Kirish usuli: "local" | "google"
    auth_provider: Mapped[str] = mapped_column(String(20), default="local", nullable=False)

    # Relationships
    advertisements: Mapped[list["Advertisement"]] = relationship("Advertisement", back_populates="user", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return self.email or self.phone_number or str(self.id)
