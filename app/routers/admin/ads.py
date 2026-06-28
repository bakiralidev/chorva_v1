import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.advertisement import Advertisement, AdStatus
from app.models.image import Image
from app.schemas.advertisement import AdvertisementResponse
from app.auth.dependencies import get_current_active_superuser

router = APIRouter(prefix="/ads", tags=["Admin Advertisements"])

@router.get("/", response_model=list[AdvertisementResponse])
async def list_all_ads_for_moderation(
    status_filter: AdStatus | None = Query(default=None, description="E'lonlar holati bo'yicha filtrlash"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] Tizimdagi barcha e'lonlarni ko'rish (faol, sotilgan va faol bo'lmagan barchasi).
    """
    query = select(Advertisement).options(
        selectinload(Advertisement.images)
    ).order_by(Advertisement.created_at.desc())

    if status_filter:
        query = query.where(Advertisement.status == status_filter)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/{id}/status", response_model=AdvertisementResponse)
async def update_ad_status(
    id: uuid.UUID,
    status_val: AdStatus,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] E'lon holatini o'zgartirish (active, sold, inactive).
    """
    query = select(Advertisement).options(selectinload(Advertisement.images)).where(Advertisement.id == id)
    result = await db.execute(query)
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E'lon topilmadi."
        )

    ad.status = status_val
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad

@router.put("/{id}/top", response_model=AdvertisementResponse)
async def toggle_ad_top(
    id: uuid.UUID,
    is_top: bool,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] E'lonni TOP (saralangan e'lonlar) qatoriga qo'shish yoki undan chiqarish.
    """
    query = select(Advertisement).options(selectinload(Advertisement.images)).where(Advertisement.id == id)
    result = await db.execute(query)
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E'lon topilmadi."
        )

    ad.is_top = is_top
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad_by_admin(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] E'lonni butunlay o'chirib tashlash (fayl tizimidagi rasmlari bilan birga).
    """
    query = select(Advertisement).options(selectinload(Advertisement.images)).where(Advertisement.id == id)
    result = await db.execute(query)
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E'lon topilmadi."
        )

    # Rasmlarni diskdan tozalash
    for img in ad.images:
        if img.image_url and img.image_url.startswith("/uploads/"):
            filename = img.image_url.replace("/uploads/", "")
            file_path = os.path.join("uploads", filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    await db.delete(ad)
    await db.commit()
    return None
