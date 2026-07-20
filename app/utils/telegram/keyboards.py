"""
keyboards.py — Telegram bot klaviaturalari.

Bu faylda foydalanuvchiga ko'rsatiladigan ReplyKeyboard tugmalari sozlanadi.
"""
from telegram import ReplyKeyboardMarkup, KeyboardButton


def get_phone_share_keyboard() -> ReplyKeyboardMarkup:
    """
    Foydalanuvchiga telefon raqamini ulashish uchun klaviatura qaytaradi.
    request_contact=True — Telegram'dan rasmiy raqamni oladi (soxtalashtirish mumkin emas).
    """
    button = KeyboardButton(
        text="📱 Telefon raqamimni ulashish",
        request_contact=True
    )
    return ReplyKeyboardMarkup(
        keyboard=[[button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
