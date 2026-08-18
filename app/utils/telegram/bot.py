"""
bot.py — @chorva_uzbot Telegram bot handlerlar va Application.

Bu fayldagi BotApplication FastAPI startup da ishga tushiriladi.

Yangi onboarding oqimi:
1. Foydalanuvchi /start bosadi
2. Bot til tanlash inline keyboard chiqaradi (🇺🇿 O'zbek | 🇷🇺 Русский)
3. Foydalanuvchi tilni tanlaydi → til saqlanadi
4. Bot to'liq ismni so'raydi (kamida 5 belgi)
5. Foydalanuvchi ismini yozadi → ism saqlanadi
6. Bot telefon raqam ulashish tugmasini chiqaradi
7. Foydalanuvchi telefon ulashadi → DB ga yoziladi → User yaratiladi
8. ✅ Muvaffaqiyatli xabar + Chorva Market ochish tugmasi
"""
import logging
from telegram import (
    Update, ReplyKeyboardRemove, InlineKeyboardButton,
    InlineKeyboardMarkup, WebAppInfo
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from app.config import settings

logger = logging.getLogger("app.telegram.bot")

# Global bot application instance
_bot_app: Application | None = None

# ConversationHandler holatlari
LANG, NAME, PHONE = range(3)

# Mini App URL
MINI_APP_URL = "https://chorva-market.vercel.app/"

# Til bo'yicha xabarlar
MESSAGES = {
    "uz": {
        "welcome": (
            "🐄 <b>Chorva Market</b> ga xush kelibsiz!\n\n"
            "Davom etish uchun tilni tanlang:"
        ),
        "ask_name": (
            "✍️ <b>To'liq ismingizni kiriting</b>\n\n"
            "Masalan: <i>Bobur Karimov</i>\n"
            "(Kamida 5 ta belgi bo'lishi kerak)"
        ),
        "name_too_short": (
            "⚠️ Ism juda qisqa. Kamida <b>5 ta belgi</b> kiriting.\n"
            "Masalan: <i>Bobur Karimov</i>"
        ),
        "ask_phone": (
            "📱 <b>Telefon raqamingizni ulashing</b>\n\n"
            "Pastdagi tugmani bosing — Telegram raqamingiz avtomatik yuboriladi."
        ),
        "phone_button": "📱 Telefon raqamimni ulashish",
        "success": (
            "✅ <b>Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>\n\n"
            "Chorva Market'ga kirish uchun pastdagi tugmani bosing 👇"
        ),
        "open_app": "🛒 Chorva Market'ni ochish",
        "error": "⚠️ Xatolik yuz berdi. Iltimos /start bosib qaytadan urinib ko'ring.",
        "already_registered": (
            "✅ Siz allaqachon ro'yxatdan o'tgansiz!\n\n"
            "Chorva Market'ga kirish uchun:"
        ),
    },
    "ru": {
        "welcome": (
            "🐄 Добро пожаловать в <b>Chorva Market</b>!\n\n"
            "Выберите язык для продолжения:"
        ),
        "ask_name": (
            "✍️ <b>Введите ваше полное имя</b>\n\n"
            "Например: <i>Бобур Каримов</i>\n"
            "(Минимум 5 символов)"
        ),
        "name_too_short": (
            "⚠️ Имя слишком короткое. Введите минимум <b>5 символов</b>.\n"
            "Например: <i>Бобур Каримов</i>"
        ),
        "ask_phone": (
            "📱 <b>Поделитесь номером телефона</b>\n\n"
            "Нажмите кнопку ниже — номер Telegram отправится автоматически."
        ),
        "phone_button": "📱 Поделиться номером телефона",
        "success": (
            "✅ <b>Регистрация прошла успешно!</b>\n\n"
            "Нажмите кнопку ниже, чтобы открыть Chorva Market 👇"
        ),
        "open_app": "🛒 Открыть Chorva Market",
        "error": "⚠️ Произошла ошибка. Попробуйте снова, нажав /start.",
        "already_registered": (
            "✅ Вы уже зарегистрированы!\n\n"
            "Чтобы открыть Chorva Market:"
        ),
    }
}


def get_lang_keyboard() -> InlineKeyboardMarkup:
    """Til tanlash inline keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 O'zbek tili", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский язык", callback_data="lang_ru"),
        ]
    ])


def get_open_app_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Mini App ochish inline tugmasi."""
    text = MESSAGES[lang]["open_app"]
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text, web_app=WebAppInfo(url=MINI_APP_URL))
    ]])


def get_phone_keyboard(lang: str):
    """Telefon ulashish ReplyKeyboard."""
    from telegram import ReplyKeyboardMarkup, KeyboardButton
    button = KeyboardButton(
        text=MESSAGES[lang]["phone_button"],
        request_contact=True
    )
    return ReplyKeyboardMarkup(
        keyboard=[[button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /start buyrug'i — foydalanuvchi allaqachon ro'yxatdan o'tganligini
    tekshirib, agar o'tmagan bo'lsa til tanlash oqimini boshlaydi.
    """
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    try:
        from app.database import AsyncSessionLocal
        from app.models.telegram_link import TelegramLink
        from sqlalchemy.future import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(TelegramLink).where(TelegramLink.chat_id == chat_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Allaqachon ro'yxatdan o'tgan
                lang = existing.lang or "uz"
                msg = MESSAGES[lang]["already_registered"]
                await update.message.reply_html(
                    msg,
                    reply_markup=get_open_app_keyboard(lang)
                )
                return ConversationHandler.END
    except Exception as e:
        logger.error("start_handler DB xatosi: %s", e)

    # Yangi foydalanuvchi — til tanlashdan boshlaymiz
    await update.message.reply_html(
        MESSAGES["uz"]["welcome"],
        reply_markup=get_lang_keyboard()
    )
    return LANG


async def lang_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Foydalanuvchi til tanladi (callback query).
    Tilni context ga saqlab, ismni so'raydi.
    """
    query = update.callback_query
    await query.answer()

    lang = "uz" if query.data == "lang_uz" else "ru"
    context.user_data["lang"] = lang

    await query.edit_message_text(
        MESSAGES[lang]["ask_name"],
        parse_mode="HTML"
    )
    return NAME


async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Foydalanuvchi ismini yozdi.
    Kamida 5 belgi tekshiruvi. To'g'ri bo'lsa telefon so'raydi.
    """
    lang = context.user_data.get("lang", "uz")
    full_name = update.message.text.strip()

    if len(full_name) < 5:
        await update.message.reply_html(MESSAGES[lang]["name_too_short"])
        return NAME  # Qaytadan so'raymiz

    context.user_data["full_name"] = full_name

    await update.message.reply_html(
        MESSAGES[lang]["ask_phone"],
        reply_markup=get_phone_keyboard(lang)
    )
    return PHONE


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Foydalanuvchi contact (telefon raqam) yuborganida ishlaydi.
    TelegramLink va User jadvallariga yozadi.
    """
    contact = update.message.contact
    chat_id = str(update.effective_chat.id)
    tg_user = update.effective_user

    lang = context.user_data.get("lang", "uz")
    full_name = context.user_data.get("full_name", tg_user.full_name or "")

    # Raqamni normallashtirish
    raw_phone = contact.phone_number
    phone_number = raw_phone if raw_phone.startswith("+") else f"+{raw_phone}"

    logger.info("Telefon ulashildi: phone=%s chat_id=%s lang=%s", phone_number, chat_id, lang)

    try:
        from app.database import AsyncSessionLocal
        from app.models.telegram_link import TelegramLink
        from app.models.user import User
        from sqlalchemy.future import select

        async with AsyncSessionLocal() as db:
            # TelegramLink ni yangilaymiz yoki yaratamiz
            result = await db.execute(
                select(TelegramLink).where(TelegramLink.phone_number == phone_number)
            )
            existing_link = result.scalar_one_or_none()

            if existing_link:
                existing_link.chat_id = chat_id
                existing_link.full_name = full_name
                existing_link.lang = lang
            else:
                new_link = TelegramLink(
                    phone_number=phone_number,
                    chat_id=chat_id,
                    full_name=full_name,
                    lang=lang,
                )
                db.add(new_link)

            # Foydalanuvchi allaqachon borligini tekshiramiz
            user_result = await db.execute(
                select(User).where(User.phone_number == phone_number)
            )
            existing_user = user_result.scalar_one_or_none()

            if not existing_user:
                # Telegram orqali ro'yxatdan o'tish — parolsiz user
                name_parts = full_name.split(maxsplit=1)
                first_name = name_parts[0] if name_parts else full_name
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                new_user = User(
                    phone_number=phone_number,
                    full_name=full_name,
                    first_name=first_name,
                    last_name=last_name,
                    telegram_chat_id=chat_id,
                    telegram_username=tg_user.username,
                    preferred_lang=lang,
                    auth_provider="telegram",
                    is_active=True,
                    is_verified=True,
                    accepted_offer=True,
                )
                db.add(new_user)
                logger.info("Yangi Telegram foydalanuvchi yaratildi: phone=%s", phone_number)
            else:
                # Mavjud foydalanuvchini yangilaymiz
                existing_user.telegram_chat_id = chat_id
                if not existing_user.preferred_lang:
                    existing_user.preferred_lang = lang
                logger.info("Mavjud foydalanuvchi yangilandi: phone=%s", phone_number)

            await db.commit()

        # Klaviaturani yopib, muvaffaqiyat xabarini yuboramiz
        await update.message.reply_text(
            "✅",
            reply_markup=ReplyKeyboardRemove()
        )
        await update.message.reply_html(
            MESSAGES[lang]["success"],
            reply_markup=get_open_app_keyboard(lang)
        )

    except Exception as e:
        logger.error("contact_handler xatolik: %s", str(e))
        await update.message.reply_text(
            MESSAGES[lang]["error"],
            reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Foydalanuvchi /cancel bosdi — suhbatni bekor qilish."""
    lang = context.user_data.get("lang", "uz")
    cancel_msg = {
        "uz": "❌ Bekor qilindi. Qaytadan boshlash uchun /start yozing.",
        "ru": "❌ Отменено. Напишите /start, чтобы начать заново."
    }
    await update.message.reply_text(
        cancel_msg.get(lang, cancel_msg["uz"]),
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def create_bot_application() -> Application:
    """
    Bot Application yaratadi va ConversationHandler ni ro'yxatdan o'tkazadi.
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

    # Onboarding ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            LANG: [CallbackQueryHandler(lang_callback_handler, pattern="^lang_(uz|ru)$")],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            PHONE: [MessageHandler(filters.CONTACT, contact_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

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
