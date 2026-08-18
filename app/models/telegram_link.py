"""
TelegramLink — foydalanuvchi Telegram botga /start bosib,
telefon raqamini ulashganda, phone_number <-> chat_id bog'liqligini saqlash uchun.

Oqim:
1. Foydalanuvchi @chorva_uzbot ga /start bosadi
2. Bot til tanlash keyboard ko'rsatadi
3. Foydalanuvchi tilni tanlaydi → to'liq ismini yozadi
4. Bot "Telefon raqamingizni ulashing" tugmasini ko'rsatadi
5. Foydalanuvchi ulashadi → bot phone_number va chat_id ni shu jadvalga yozadi
6. Foydalanuvchi users jadvalida yaratiladi (auth_provider="telegram")
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TelegramLink(Base):
    __tablename__ = "telegram_links"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Foydalanuvchi ulashgan telefon raqami (Telegram rasmiy raqami)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Telegram chat ID — OTP yuborish uchun
    chat_id: Mapped[str] = mapped_column(String(50), nullable=False)
    # Bot onboarding da yozilgan to'liq ism
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Foydalanuvchi tanlagan til: "uz" | "ru"
    lang: Mapped[str | None] = mapped_column(String(10), nullable=True, default="uz")
    # Qo'shilgan vaqt
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    def __str__(self) -> str:
        return f"{self.phone_number} → {self.chat_id}"

