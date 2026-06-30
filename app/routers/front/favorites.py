import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.advertisement import Advertisement
from app.models.favorite import Favorite
from app.schemas.advertisement import AdvertisementResponse
from app.schemas.favorite import FavoriteToggleResponse
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites (Sevimlilar)"])

@router.post("/toggle/{ad_id}", response_model=FavoriteToggleResponse)
async def toggle_favorite(
    ad_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    E'lonni sevimlilarga qo'shish yoki olib tashlash.
    Agar e'lon allaqachon sevimlilarda bo'lsa, u olib tashlanadi.
    Yo'q bo'lsa, qo'shiladi.
    """
    # E'lon mavjudligini tekshirish
    result_ad = await db.execute(select(Advertisement).where(Advertisement.id == ad_id))
    ad = result_ad.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")

    # Sevimlilarda bor-yo'qligini tekshirish
    result_fav = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.advertisement_id == ad_id
        )
    )
    favorite = result_fav.scalar_one_or_none()

    if favorite:
        # Agar bor bo'lsa, olib tashlash
        await db.delete(favorite)
        await db.commit()
        return {"message": "E'lon sevimlilardan olib tashlandi", "status": "removed"}
    else:
        # Yo'q bo'lsa, qo'shish
        new_favorite = Favorite(
            user_id=current_user.id,
            advertisement_id=ad_id
        )
        db.add(new_favorite)
        await db.commit()
        return {"message": "E'lon sevimlilarga qo'shildi", "status": "added"}


@router.get("", response_model=list[AdvertisementResponse])
async def get_favorites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Foydalanuvchining sevimli e'lonlari ro'yxatini olish.
    Faqat joriy foydalanuvchiga tegishli sevimlilarni qaytaradi.
    """
    # Use selectinload to eagerly load the advertisement
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Favorite).options(selectinload(Favorite.advertisement)).where(Favorite.user_id == current_user.id)
    )
    favorites = result.scalars().all()

    # E'lonlarni ajratib olish
    ads = [fav.advertisement for fav in favorites]
    return ads
