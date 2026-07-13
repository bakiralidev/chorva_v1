from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.database import get_db
from app.models.user import User
from app.models.verification import VerificationCode
from app.schemas.user import UserCreate, UserResponse, UserRegisterResponse, VerifyCode, UserUpdate
from app.schemas.token import Token, TokenRefreshRequest
from app.auth.security import hash_password, verify_password, create_access_token, generate_refresh_token
from app.auth.dependencies import get_current_user
from app.models.refresh_token import RefreshToken
from app.config import settings
import random
import string
import uuid
from datetime import datetime, timedelta

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

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    ### Yangi foydalanuvchini ro'yxatdan o'tkazish.
    
    Ushbu endpoint yangi foydalanuvchi akkauntini yaratish uchun ishlatiladi.
    
    * **Email** yoki **Telefon raqamidan** kamida bittasini kiritish majburiy.
    * Parol kamida **6 ta belgidan** iborat bo'lishi kerak.

    **Muayyan Xatoliklar (Error States):**
    * **400 Bad Request**: 
      * Agar foydalanuvchi Ofertaga rozi bo'lmasa.
      * Agar email ham, telefon raqami ham yuborilmagan bo'lsa.
      * Agar kiritilgan email yoki telefon raqami allaqachon ro'yxatdan o'tgan bo'lsa.
    """
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
        is_superuser=False
    )
    db.add(new_user)
    await db.flush() # id ni olish uchun

    # Tasdiqlash kodini yaratish (6 xonali)
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
    
    print(f"\n[{new_user.email or new_user.phone_number} uchun tasdiqlash kodi]: {code}\n")
    
    return {
        "user": new_user,
        "verification_code": code,
        "message": "Tasdiqlash kodi yuborildi. Iltimos kodni kiriting."
    }

@router.post("/verify", response_model=Token)
async def verify_code(
    verify_in: VerifyCode,
    db: AsyncSession = Depends(get_db)
):
    """
    ### Tasdiqlash kodi orqali ro'yxatdan o'tishni yakunlash va Token olish.
    """
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

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    ### Foydalanuvchi profiliga kirish va JWT Access Token olish.
    
    Tizimda avtorizatsiyadan o'tish uchun ishlatiladi. `OAuth2` standartiga mos keladi.
    
    * **username** maydoniga foydalanuvchining **email** manzili yoki **telefon raqami** kiritilishi mumkin.
    * Olingan token keyingi yopiq (protected) endpointlar uchun **Authorization: Bearer <token>** sarlavhasida yuboriladi.

    **Muayyan Xatoliklar (Error States):**
    * **400 Bad Request**: 
      * Login yoki parol noto'g'ri bo'lsa.
      * Foydalanuvchi akkaunti faol bo'lmasa.
    """
    # Foydalanuvchini email yoki telefon orqali qidirish
    query = select(User).where(
        or_(
            User.email == form_data.username,
            User.phone_number == form_data.username
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kiritilgan login yoki parol noto'g'ri."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Foydalanuvchi akkaunti faol emas."
        )

    # JWT access token yaratish
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = await create_user_refresh_token(db, user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    ### Tizimga kirgan foydalanuvchining shaxsiy ma'lumotlarini olish.
    
    Faqatgina ro'yxatdan o'tgan va `Bearer` tokenga ega bo'lgan foydalanuvchilar foydalana oladi.

    **So'rov sarlavhalari (Request Headers):**
    * `Authorization: Bearer <access_token>` (Majburiy)

    **Muayyan Xatoliklar (Error States):**
    * **401 Unauthorized**: Token yuborilmagan, eskirgan yoki noto'g'ri bo'lsa.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    profile_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ### Foydalanuvchining shaxsiy ma'lumotlarini (email, telefon, telegram_username) tahrirlash.
    """
    if profile_update.email is not None and profile_update.email != current_user.email:
        # Check if email is already taken
        query = select(User).where(User.email == profile_update.email)
        res = await db.execute(query)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ushbu email allaqachon ro'yxatdan o'tgan."
            )
        current_user.email = profile_update.email

    if profile_update.phone_number is not None and profile_update.phone_number != current_user.phone_number:
        # Check if phone number is already taken
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


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_in: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    ### Refresh Token yordamida Access Token va Refresh Tokenni yangilash (Rotation).
    """
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


@router.post("/logout")
async def logout(
    refresh_in: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    ### Tizimdan chiqish va Refresh Tokenni bekor qilish (o'chirish).
    """
    query = select(RefreshToken).where(
        RefreshToken.token == refresh_in.refresh_token
    )
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    if db_token:
        await db.delete(db_token)
        await db.commit()

    return {"message": "Tizimdan muvaffaqiyatli chiqildi."}
