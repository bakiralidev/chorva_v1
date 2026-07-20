"""
auth.py — Autentifikatsiya endpointlari (ro'yxatdan o'tish, kirish, tokenlar).

## OTP yuborish kanallari:

### Telegram orqali OTP:
- Foydalanuvchi avval @chorva_uzbot ga `/start` bosib, telefon raqamini ulashgan bo'lishi kerak
- Ro'yxatdan o'tishda `phone_number` kiritilsa → bazada TelegramLink topilsa → OTP Telegram'ga boradi

### Email orqali OTP:
- Ro'yxatdan o'tishda `email` kiritilsa → Gmailga OTP boradi
- `.env` da SMTP sozlamalari to'ldirilgan bo'lishi kerak

### Console fallback (development):
- SMTP yoki Telegram sozlanmagan bo'lsa → OTP faqat server logiga chiqariladi
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.database import get_db
from app.models.user import User
from app.models.verification import VerificationCode
from app.models.telegram_link import TelegramLink
from app.schemas.user import UserCreate, UserResponse, UserRegisterResponse, VerifyCode, UserUpdate
from app.schemas.token import Token, TokenRefreshRequest
from app.auth.security import hash_password, verify_password, create_access_token, generate_refresh_token
from app.auth.dependencies import get_current_user
from app.models.refresh_token import RefreshToken
from app.config import settings
from app.utils.telegram.otp import send_otp_via_telegram
from app.utils.email_service import send_otp_email
import random
import string
import uuid
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def create_user_refresh_token(db: AsyncSession, user_id: uuid.UUID) -> str:
    token_str = generate_refresh_token()
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(
        user_id=user_id,
        token=token_str,
        expires_at=expires_at
    )
    db.add(db_token)
    await db.commit()
    return token_str


async def _send_otp(
    phone_number: str | None,
    email: str | None,
    otp_code: str,
    db: AsyncSession,
) -> str:
    """
    OTP ni mavjud kanalga yuboradi va kanal nomini qaytaradi.
    Kanal ustuvorligi: Telegram → Email → Console (fallback)
    """
    # 1. Telegram orqali yuborish (telefon raqam bo'lsa)
    if phone_number:
        result = await db.execute(
            select(TelegramLink).where(TelegramLink.phone_number == phone_number)
        )
        tg_link = result.scalar_one_or_none()

        if tg_link:
            sent = await send_otp_via_telegram(tg_link.chat_id, otp_code, phone_number)
            if sent:
                return "telegram"

    # 2. Email orqali yuborish
    if email:
        sent = await send_otp_email(email, otp_code)
        if sent:
            return "email"

    # 3. Fallback — faqat log ga chiqarish (development)
    logger.warning(
        "OTP CONSOLE FALLBACK [%s]: %s",
        phone_number or email,
        otp_code
    )
    print(f"\n{'='*50}")
    print(f"[OTP CONSOLE] {phone_number or email} uchun tasdiqlash kodi: {otp_code}")
    print(f"{'='*50}\n")
    return "console"


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi foydalanuvchini ro'yxatdan o'tkazish",
    description="""
### Yangi foydalanuvchini ro'yxatdan o'tkazish

Ushbu endpoint yangi foydalanuvchi akkauntini yaratish uchun ishlatiladi.

**Majburiy shartlar:**
- `email` yoki `phone_number` dan kamida bittasi kiritilishi shart
- `password` kamida **6 ta belgidan** iborat bo'lishi kerak
- `accepted_offer` maydonini `true` qilib yuborish shart

**OTP yuborish kanallari:**
- 📱 **Telegram**: Agar foydalanuvchi avval @chorva_uzbot ga `/start` bosib,
  telefon raqamini ulashgan bo'lsa → OTP Telegram orqali boradi
- 📧 **Email**: Agar email kiritilgan va SMTP sozlangan bo'lsa → Gmailga OTP boradi
- Javobdagi `otp_channel` maydoni qaysi kanal orqali ketganini ko'rsatadi

**Muayyan Xatoliklar:**
- **400**: Ofertaga rozi bo'lmagan
- **400**: Email ham, telefon ham yuborilmagan
- **400**: Email allaqachon ro'yxatdan o'tgan
- **400**: Telefon raqam allaqachon ro'yxatdan o'tgan
""",
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    if not user_in.accepted_offer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ro'yxatdan o'tish uchun Ommaviy ofertaga rozi bo'lishingiz shart."
        )

    # Email unikal ekanligini tekshirish
    if user_in.email:
        query = select(User).where(User.email == user_in.email)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ushbu email tizimda ro'yxatdan o'tgan."
            )

    # Telefon raqam unikal ekanligini tekshirish
    if user_in.phone_number:
        query = select(User).where(User.phone_number == user_in.phone_number)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ushbu telefon raqami tizimda ro'yxatdan o'tgan."
            )

    # Parolni hash qilish va foydalanuvchini yaratish
    hashed_pwd = hash_password(user_in.password)
    new_user = User(
        email=user_in.email,
        phone_number=user_in.phone_number,
        hashed_password=hashed_pwd,
        is_active=False,
        is_verified=False,
        accepted_offer=True,
        is_superuser=False,
        auth_provider="local",
    )
    db.add(new_user)
    await db.flush()  # id ni olish uchun

    # 6 xonali OTP yaratish
    code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    verification = VerificationCode(
        user_id=new_user.id,
        code=code,
        expires_at=expires_at
    )
    db.add(verification)
    await db.commit()
    await db.refresh(new_user)

    # OTP ni yuborish (Telegram → Email → Console)
    channel = await _send_otp(
        phone_number=user_in.phone_number,
        email=user_in.email,
        otp_code=code,
        db=db,
    )

    # Kanal bo'yicha xabar
    channel_messages = {
        "telegram": "Tasdiqlash kodi Telegram orqali yuborildi. @chorva_uzbot da tekshiring.",
        "email": f"Tasdiqlash kodi {user_in.email} elektron pochta manzilingizga yuborildi.",
        "console": "Tasdiqlash kodi server logiga yozildi (development rejimi).",
    }

    return {
        "user": new_user,
        "message": channel_messages.get(channel, "Tasdiqlash kodi yuborildi."),
        "otp_channel": channel,
    }


@router.post(
    "/verify",
    response_model=Token,
    summary="OTP kodni tasdiqlash va JWT token olish",
    description="""
### OTP kodni tasdiqlash va tizimga kirish

Ro'yxatdan o'tgandan so'ng yuborilgan 6 xonali kodni tasdiqlash uchun ishlatiladi.
Muvaffaqiyatli tekshiruvdan so'ng `access_token` va `refresh_token` qaytariladi.

**So'rov maydonlari:**
- `username` — ro'yxatdan o'tishda ishlatilgan email yoki telefon raqami
- `code` — 6 xonali OTP kodi (Telegram yoki Email orqali kelgan)

**Muayyan Xatoliklar:**
- **404**: Foydalanuvchi topilmadi
- **400**: Tasdiqlash kodi topilmadi (qaytadan /register ga murojaat qiling)
- **400**: Kod muddati tugagan (5 daqiqa)
- **400**: Kod noto'g'ri
""",
)
async def verify_code(
    verify_in: VerifyCode,
    db: AsyncSession = Depends(get_db)
):
    query = select(User).where(
        or_(
            User.email == verify_in.username,
            User.phone_number == verify_in.username
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi."
        )

    # Eng so'nggi yuborilgan kodni olish
    v_query = select(VerificationCode).where(
        VerificationCode.user_id == user.id
    ).order_by(VerificationCode.created_at.desc())
    v_result = await db.execute(v_query)
    verification = v_result.scalars().first()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tasdiqlash kodi topilmadi. Qaytadan urinib ko'ring."
        )

    if verification.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tasdiqlash kodi muddati tugagan."
        )

    if verification.code != verify_in.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tasdiqlash kodi noto'g'ri."
        )

    # Foydalanuvchini faollashtirish
    user.is_verified = True
    user.is_active = True

    # Kodni o'chirish (bir marta ishlatiladigan)
    await db.delete(verification)
    await db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = await create_user_refresh_token(db, user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post(
    "/login",
    response_model=Token,
    summary="Email/telefon va parol bilan kirish",
    description="""
### Foydalanuvchi profiliga kirish va JWT Access Token olish

Tizimda avtorizatsiyadan o'tish uchun ishlatiladi. `OAuth2` standartiga mos keladi.

**So'rov maydonlari:**
- `username` — foydalanuvchining **email** manzili yoki **telefon raqami**
- `password` — foydalanuvchining paroli

> ⚠️ **Eslatma:** Google OAuth2 orqali ro'yxatdan o'tgan foydalanuvchilar
> bu endpoint orqali kira olmaydi (ularda parol yo'q).
> Google foydalanuvchilari uchun `/auth/google` endpointidan foydalaning.

**Olingan token:**
- Keyingi yopiq (protected) endpointlar uchun `Authorization: Bearer <token>` sarlavhasida yuboring

**Muayyan Xatoliklar:**
- **400**: Login yoki parol noto'g'ri
- **400**: Foydalanuvchi akkaunti faol emas (OTP tasdiqlanmagan)
- **400**: Bu foydalanuvchi Google orqali ro'yxatdan o'tgan (parol yo'q)
""",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Foydalanuvchini email yoki telefon orqali qidirish
    query = select(User).where(
        or_(
            User.email == form_data.username,
            User.phone_number == form_data.username
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kiritilgan login yoki parol noto'g'ri."
        )

    # Google OAuth2 foydalanuvchisi parol bilan kira olmaydi
    if user.auth_provider == "google" or user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu akkaunt Google orqali ro'yxatdan o'tgan. Iltimos 'Google bilan kirish' tugmasidan foydalaning."
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kiritilgan login yoki parol noto'g'ri."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Foydalanuvchi akkaunti faol emas. OTP kodini tasdiqlab kirish kerak."
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = await create_user_refresh_token(db, user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Joriy foydalanuvchi ma'lumotlarini olish",
    description="""
### Tizimga kirgan foydalanuvchining shaxsiy ma'lumotlarini olish

Faqatgina ro'yxatdan o'tgan va `Bearer` tokenga ega bo'lgan foydalanuvchilar foydalana oladi.

**So'rov sarlavhalari:**
- `Authorization: Bearer <access_token>` (Majburiy)

**Qaytariladigan ma'lumotlar:**
- `id`, `email`, `phone_number` — asosiy ma'lumotlar
- `full_name`, `avatar_url` — Google'dan kelgan ism va rasm (agar Google orqali kirgan bo'lsa)
- `auth_provider` — `"local"` yoki `"google"`
- `is_active`, `is_superuser`, `created_at`

**Muayyan Xatoliklar:**
- **401**: Token yuborilmagan, eskirgan yoki noto'g'ri
""",
)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Foydalanuvchi ma'lumotlarini yangilash",
    description="""
### Foydalanuvchining shaxsiy ma'lumotlarini tahrirlash

**Tahrirlash mumkin bo'lgan maydonlar:**
- `email` — yangi email (unikal bo'lishi shart)
- `phone_number` — yangi telefon raqami (unikal bo'lishi shart)
- `telegram_username` — Telegram username (@username formatida)

**So'rov sarlavhalari:**
- `Authorization: Bearer <access_token>` (Majburiy)

**Muayyan Xatoliklar:**
- **400**: Kiritilgan email allaqachon boshqa foydalanuvchida mavjud
- **400**: Kiritilgan telefon raqami allaqachon boshqa foydalanuvchida mavjud
- **401**: Token yuborilmagan yoki noto'g'ri
""",
)
async def update_my_profile(
    profile_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if profile_update.email is not None and profile_update.email != current_user.email:
        query = select(User).where(User.email == profile_update.email)
        res = await db.execute(query)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ushbu email allaqachon ro'yxatdan o'tgan."
            )
        current_user.email = profile_update.email

    if profile_update.phone_number is not None and profile_update.phone_number != current_user.phone_number:
        query = select(User).where(User.phone_number == profile_update.phone_number)
        res = await db.execute(query)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ushbu telefon raqami allaqachon ro'yxatdan o'tgan."
            )
        current_user.phone_number = profile_update.phone_number

    if profile_update.telegram_username is not None:
        current_user.telegram_username = profile_update.telegram_username

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post(
    "/refresh",
    response_model=Token,
    summary="Access Token ni yangilash (Refresh Token Rotation)",
    description="""
### Refresh Token yordamida tokenlarni yangilash

`access_token` muddati tugagach, yangi token olish uchun ishlatiladi.
Har safar refresh qilganda **eski refresh_token bekor qilinadi** va yangi biri beriladi
(Token Rotation xavfsizlik mexanizmi).

**So'rov tanasi:**
- `refresh_token` — avval `/login` yoki `/verify` dan olingan refresh token

**Muayyan Xatoliklar:**
- **401**: Refresh token noto'g'ri yoki bekor qilingan
- **401**: Refresh token muddati tugagan
- **401**: Foydalanuvchi hisobi faol emas
""",
)
async def refresh_token(
    refresh_in: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    query = select(RefreshToken).where(
        RefreshToken.token == refresh_in.refresh_token,
        RefreshToken.is_revoked == False
    )
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token noto'g'ri yoki bekor qilingan."
        )

    if datetime.utcnow() > db_token.expires_at:
        await db.delete(db_token)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token muddati tugagan. Iltimos qaytadan login qiling."
        )

    user_query = select(User).where(User.id == db_token.user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi hisobi faol emas yoki topilmadi."
        )

    await db.delete(db_token)
    await db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = await create_user_refresh_token(db, user.id)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post(
    "/logout",
    summary="Tizimdan chiqish",
    description="""
### Tizimdan chiqish va Refresh Tokenni bekor qilish

Refresh tokenni bazadan o'chirib, uni yaroqsiz holatga keltiradi.

**So'rov tanasi:**
- `refresh_token` — bekor qilinishi kerak bo'lgan refresh token

> ℹ️ Access token muddati tugagunicha texnik jihatdan faol bo'ladi,
> ammo yangi access token olish imkoni yo'qoladi.
""",
)
async def logout(
    refresh_in: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    query = select(RefreshToken).where(
        RefreshToken.token == refresh_in.refresh_token
    )
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    if db_token:
        await db.delete(db_token)
        await db.commit()

    return {"message": "Tizimdan muvaffaqiyatli chiqildi."}
