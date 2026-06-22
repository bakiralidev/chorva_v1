from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.auth.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Yangi foydalanuvchini ro'yxatdan o'tkazish.
    Faqat email yoki telefon raqamidan kamida bittasi to'ldirilishi lozim.
    """
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
        is_active=True,
        is_superuser=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Foydalanuvchi profiliga kirish va JWT token olish.
    'username' maydoniga email yoki telefon raqamini kiritish mumkin.
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
    return {"access_token": access_token, "token_type": "bearer"}
