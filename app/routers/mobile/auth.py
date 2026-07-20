"""
auth.py — Mobile API autentifikatsiya endpointlari.

Bu router front/auth.py bilan bir xil mantiqqa ega,
faqat prefix va tag farqli.

## OTP yuborish kanallari:
- 📱 **Telegram**: @chorva_uzbot ga /start bosib telefon ulashilgan bo'lsa
- 📧 **Email**: Email kiritilgan va SMTP sozlangan bo'lsa
- 🖥️ **Console**: Development fallback
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

logger = logging.getLogger("app.auth.mobile")

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
    """OTP ni mavjud kanalga yuboradi. Ustuvorlik: Telegram → Email → Console"""
    if phone_number:
        result = await db.execute(
            select(TelegramLink).where(TelegramLink.phone_number == phone_number)
        )
        tg_link = result.scalar_one_or_none()
        if tg_link:
            sent = await send_otp_via_telegram(tg_link.chat_id, otp_code, phone_number)
            if sent:
                return "telegram"

    if email:
        sent = await send_otp_email(email, otp_code)
        if sent:
            return "email"

    logger.warning("OTP CONSOLE FALLBACK [%s]: %s", phone_number or email, otp_code)
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

**Majburiy shartlar:**
- `email` yoki `phone_number` dan kamida bittasi kiritilishi shart
- `password` kamida **6 ta belgidan** iborat bo'lishi kerak
- `accepted_offer` maydonini `true` qilib yuborish shart

**OTP yuborish kanallari:**
- 📱 **Telegram**: @chorva_uzbot ga `/start` bosib telefon ulashilgan bo'lsa → OTP Telegram'ga boradi
- 📧 **Email**: Email kiritilgan bo'lsa → Gmailga OTP boradi
- Javobdagi `otp_channel` qaysi kanal ishlatilganini ko'rsatadi

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

    if user_in.email:
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ushbu email tizimda ro'yxatdan o'tgan.")

    if user_in.phone_number:
        result = await db.execute(select(User).where(User.phone_number == user_in.phone_number))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ushbu telefon raqami tizimda ro'yxatdan o'tgan.")

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
    await db.flush()

    code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    verification = VerificationCode(user_id=new_user.id, code=code, expires_at=expires_at)
    db.add(verification)
    await db.commit()
    await db.refresh(new_user)

    channel = await _send_otp(
        phone_number=user_in.phone_number,
        email=user_in.email,
        otp_code=code,
        db=db,
    )

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

**So'rov maydonlari:**
- `username` — ro'yxatdan o'tishda ishlatilgan email yoki telefon raqami
- `code` — 6 xonali OTP kodi

**Muayyan Xatoliklar:**
- **404**: Foydalanuvchi topilmadi
- **400**: Tasdiqlash kodi topilmadi
- **400**: Kod muddati tugagan (5 daqiqa)
- **400**: Kod noto'g'ri
""",
)
async def verify_code(verify_in: VerifyCode, db: AsyncSession = Depends(get_db)):
    query = select(User).where(
        or_(User.email == verify_in.username, User.phone_number == verify_in.username)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi.")

    v_result = await db.execute(
        select(VerificationCode)
        .where(VerificationCode.user_id == user.id)
        .order_by(VerificationCode.created_at.desc())
    )
    verification = v_result.scalars().first()

    if not verification:
        raise HTTPException(status_code=400, detail="Tasdiqlash kodi topilmadi. Qaytadan urinib ko'ring.")
    if verification.is_expired:
        raise HTTPException(status_code=400, detail="Tasdiqlash kodi muddati tugagan.")
    if verification.code != verify_in.code:
        raise HTTPException(status_code=400, detail="Tasdiqlash kodi noto'g'ri.")

    user.is_verified = True
    user.is_active = True
    await db.delete(verification)
    await db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = await create_user_refresh_token(db, user.id)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post(
    "/login",
    response_model=Token,
    summary="Email/telefon va parol bilan kirish",
    description="""
### Foydalanuvchi profiliga kirish

**So'rov maydonlari:**
- `username` — email yoki telefon raqami
- `password` — foydalanuvchi paroli

> ⚠️ Google OAuth2 orqali ro'yxatdan o'tgan foydalanuvchilar bu endpoint orqali kira olmaydi.

**Muayyan Xatoliklar:**
- **400**: Login yoki parol noto'g'ri
- **400**: Akkaunt faol emas
- **400**: Google akkaunt — parol yo'q
""",
)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    query = select(User).where(
        or_(User.email == form_data.username, User.phone_number == form_data.username)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Kiritilgan login yoki parol noto'g'ri.")

    if user.auth_provider == "google" or user.hashed_password is None:
        raise HTTPException(
            status_code=400,
            detail="Bu akkaunt Google orqali ro'yxatdan o'tgan. 'Google bilan kirish' tugmasidan foydalaning."
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Kiritilgan login yoki parol noto'g'ri.")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Foydalanuvchi akkaunti faol emas.")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = await create_user_refresh_token(db, user.id)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Joriy foydalanuvchi ma'lumotlarini olish",
    description="""
### Tizimga kirgan foydalanuvchining ma'lumotlarini olish

**So'rov sarlavhalari:**
- `Authorization: Bearer <access_token>` (Majburiy)

**Muayyan Xatoliklar:**
- **401**: Token yuborilmagan yoki noto'g'ri
""",
)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Foydalanuvchi ma'lumotlarini yangilash",
    description="""
### Foydalanuvchining ma'lumotlarini tahrirlash

**Tahrirlash mumkin bo'lgan maydonlar:**
- `email`, `phone_number`, `telegram_username`

**Muayyan Xatoliklar:**
- **400**: Email yoki telefon boshqa foydalanuvchida mavjud
- **401**: Token noto'g'ri
""",
)
async def update_my_profile(
    profile_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if profile_update.email is not None and profile_update.email != current_user.email:
        res = await db.execute(select(User).where(User.email == profile_update.email))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ushbu email allaqachon ro'yxatdan o'tgan.")
        current_user.email = profile_update.email

    if profile_update.phone_number is not None and profile_update.phone_number != current_user.phone_number:
        res = await db.execute(select(User).where(User.phone_number == profile_update.phone_number))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ushbu telefon raqami allaqachon ro'yxatdan o'tgan.")
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
    summary="Access Token ni yangilash",
    description="""
### Refresh Token orqali tokenlarni yangilash (Token Rotation)

**So'rov tanasi:**
- `refresh_token` — avval olingan refresh token

**Muayyan Xatoliklar:**
- **401**: Token noto'g'ri, bekor qilingan yoki muddati tugagan
""",
)
async def refresh_token(refresh_in: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    query = select(RefreshToken).where(
        RefreshToken.token == refresh_in.refresh_token,
        RefreshToken.is_revoked == False
    )
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token noto'g'ri yoki bekor qilingan.")

    if datetime.utcnow() > db_token.expires_at:
        await db.delete(db_token)
        await db.commit()
        raise HTTPException(status_code=401, detail="Refresh token muddati tugagan.")

    user_result = await db.execute(select(User).where(User.id == db_token.user_id))
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Foydalanuvchi hisobi faol emas.")

    await db.delete(db_token)
    await db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = await create_user_refresh_token(db, user.id)
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@router.post(
    "/logout",
    summary="Tizimdan chiqish",
    description="""
### Tizimdan chiqish va Refresh Tokenni bekor qilish

**So'rov tanasi:**
- `refresh_token` — bekor qilinishi kerak bo'lgan token
""",
)
async def logout(refresh_in: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_in.refresh_token))
    db_token = result.scalar_one_or_none()
    if db_token:
        await db.delete(db_token)
        await db.commit()
    return {"message": "Tizimdan muvaffaqiyatli chiqildi."}
