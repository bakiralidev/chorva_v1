"""
bot.py — @chorva_uzbot Telegram bot handlerlar va Application.

Bu fayldagi BotApplication FastAPI startup da ishga tushiriladi.

OQim (Foydalanuvchi nuqtai nazaridan):
1. Foydalanuvchi @chorva_uzbot ga /start bosadi
2. Bot "Telefon raqamingizni ulashing" tugmasini chiqaradi
3. Foydalanuvchi tugmani bosadi → Telegram rasmiy raqamni yuboradi
4. Bot raqamni oladi → bazaga (telegram_links jadvaliga) yozadi
5. Foydalanuvchi Chorva.uz saytida shu raqam bilan ro'yxatdan o'tadi
6. Tizim bazadan chat_id ni topadi va OTP ni Telegram orqali yuboradi
"""
import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from app.config import settings
from app.utils.telegram.keyboards import get_phone_share_keyboard

logger = logging.getLogger("app.telegram.bot")

# Global bot application instance
_bot_app: Application | None = None


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start buyrug'i — foydalanuvchini kutib oladi va telefon ulashishni so'raydi.
    """
    user = update.effective_user
    await update.message.reply_html(
        f"Salom, {user.mention_html()}! 👋\n\n"
        f"<b>Chorva.uz</b> xizmatiga xush kelibsiz!\n\n"
        f"Ro'yxatdan o'tishda OTP kodni Telegram orqali olish uchun "
        f"quyidagi tugmani bosib, telefon raqamingizni ulashing:\n\n"
        f"⬇️ <b>Telefon raqamingizni ulashing</b>",
        reply_markup=get_phone_share_keyboard()
    )


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Foydalanuvchi contact (telefon raqam) yuborganida ishlaydi.
    Telefon raqami va chat_id ni bazaga saqlaydi.
    """
    contact = update.message.contact
    chat_id = str(update.effective_chat.id)

    # Rasmiy Telegram raqami (+ belgisi bilan normallashtirish)
    raw_phone = contact.phone_number
    phone_number = raw_phone if raw_phone.startswith("+") else f"+{raw_phone}"

    logger.info("Telefon ulashildi: phone=%s chat_id=%s", phone_number, chat_id)

    # Bazaga saqlash (asinxron DB sessiyasiz — alembic session yaratamiz)
    try:
        from app.database import AsyncSessionLocal
        from app.models.telegram_link import TelegramLink
        from sqlalchemy.future import select

        async with AsyncSessionLocal() as db:
            # Agar bu raqam avval saqlangan bo'lsa, yangilaymiz
            result = await db.execute(
                select(TelegramLink).where(TelegramLink.phone_number == phone_number)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.chat_id = chat_id
                logger.info("Mavjud TelegramLink yangilandi: phone=%s", phone_number)
            else:
                new_link = TelegramLink(phone_number=phone_number, chat_id=chat_id)
                db.add(new_link)
                logger.info("Yangi TelegramLink yaratildi: phone=%s", phone_number)

            await db.commit()

        await update.message.reply_text(
            "✅ Telefon raqamingiz muvaffaqiyatli saqlandi!\n\n"
            "Endi Chorva.uz saytida ro'yxatdan o'tganingizda "
            "tasdiqlash kodi shu Telegram akkauntingizga yuboriladi. 🎉",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error("TelegramLink saqlashda xatolik: %s", str(e))
        await update.message.reply_text(
            "⚠️ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove()
        )


def create_bot_application() -> Application:
    """
    Bot Application yaratadi va handlerlarni ro'yxatdan o'tkazadi.
    FastAPI startup da bir marta chaqiriladi.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN sozlanmagan — bot ishga tushmadi")
        return None

    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Handler ro'yxatdan o'tkazish
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(
        MessageHandler(filters.CONTACT, contact_handler)
    )

    logger.info("Telegram bot application yaratildi: @chorva_uzbot")
    return application


async def start_bot_polling() -> None:
    """
    Bot polling ni ishga tushiradi.
    Development muhitida ishlatiladi.
    Production da webhook ishlatish tavsiya etiladi.
    """
    global _bot_app
    if _bot_app is None:
        _bot_app = create_bot_application()

    if _bot_app is None:
        return

    try:
        await _bot_app.initialize()
        await _bot_app.start()
        await _bot_app.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram bot polling ishga tushdi")
    except Exception as e:
        logger.error("Telegram bot polling xatoligi: %s", str(e))


async def stop_bot_polling() -> None:
    """
    Bot polling ni to'xtatadi. FastAPI shutdown da chaqiriladi.
    """
    global _bot_app
    if _bot_app and _bot_app.updater and _bot_app.updater.running:
        await _bot_app.updater.stop()
        await _bot_app.stop()
        await _bot_app.shutdown()
        logger.info("Telegram bot to'xtatildi")
