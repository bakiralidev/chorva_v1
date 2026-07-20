"""
otp.py — Telegram orqali OTP kodi yuborish.

Bu faylda send_otp_via_telegram() funksiyasi joylashgan.
Auth router bu funksiyani import qilib ishlatadi.
"""
import logging
from telegram import Bot
from telegram.error import TelegramError
from app.config import settings

logger = logging.getLogger("app.telegram.otp")


async def send_otp_via_telegram(chat_id: str, otp_code: str, phone_number: str) -> bool:
    """
    Telegram orqali OTP kodi yuboradi.

    Args:
        chat_id: Foydalanuvchining Telegram chat ID si (TelegramLink jadvalidan olinadi)
        otp_code: 6 xonali OTP kodi
        phone_number: Foydalanuvchi telefon raqami (xabar matnida ko'rsatish uchun)

    Returns:
        True — yuborildi, False — xatolik yuz berdi
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN sozlanmagan — OTP yuborilmadi")
        return False

    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        message = (
            f"🔐 <b>Chorva.uz — Tasdiqlash kodi</b>\n\n"
            f"Telefon: <code>{phone_number}</code>\n"
            f"Kod: <b><code>{otp_code}</code></b>\n\n"
            f"⏱ Ushbu kod <b>5 daqiqa</b> ichida amal qiladi.\n"
            f"🚫 Kodni hech kimga bermang!"
        )
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="HTML"
        )
        logger.info("OTP Telegram orqali yuborildi: chat_id=%s", chat_id)
        return True
    except TelegramError as e:
        logger.error("Telegram OTP yuborishda xatolik: chat_id=%s error=%s", chat_id, str(e))
        return False
