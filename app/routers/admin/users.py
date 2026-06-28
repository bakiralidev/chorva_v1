import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.auth.dependencies import get_current_active_superuser

router = APIRouter(prefix="/users", tags=["Admin Users"])

@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] Tizimdagi barcha foydalanuvchilar ro'yxatini olish.
    """
    query = select(User).order_by(User.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{id}", response_model=UserResponse)
async def get_user_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] Bitta foydalanuvchining batafsil ma'lumotlarini olish.
    """
    query = select(User).where(User.id == id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi."
        )
    return user

@router.put("/{id}/status", response_model=UserResponse)
async def update_user_status(
    id: uuid.UUID,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] Foydalanuvchi hisobini faollashtirish yoki bloklash (is_active holatini o'zgartirish).
    """
    query = select(User).where(User.id == id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi."
        )
    
    # O'zini o'zi bloklashni oldini olish
    if user.id == admin.id and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrator o'z hisobini bloklay olmaydi."
        )

    user.is_active = is_active
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
