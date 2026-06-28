from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.category import Category
from app.models.region import Region
from app.schemas.category import CategoryResponse
from app.schemas.region import RegionResponse
from app.utils.lang import get_lang

router = APIRouter(prefix="/directories", tags=["Mobile Directories"])

@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang)
):
    """
    ### Tizimdagi barcha kategoriyalar ro'yxatini ko'p tilli formatda olish.
    
    Ushbu API kategoriyalar ro'yxatini qaytaradi. `name` va `slug` maydonlari so'rovdagi tilga mos ravishda tarjima qilinadi.
    
    **Tilni aniqlash ustuvorligi (Language Resolution Priority):**
    1. **Accept-Language sarlavhasi** (masalan: `Accept-Language: ru`)
    2. **lang query parametri** (masalan: `?lang=en`)
    3. Tizimga kirgan foydalanuvchining shaxsiy sozlamasi (`preferred_lang`)
    4. Standart til (`uz`)
    
    **Qo'llab-quvvatlanadigan tillar:** `uz`, `ru`, `en`, `tr`.
    """
    query = select(Category).order_by(Category.id)
    result = await db.execute(query)
    categories = result.scalars().all()
    return [c.to_response(lang) for c in categories]

@router.get("/regions", response_model=list[RegionResponse])
async def get_regions(
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang)
):
    """
    ### Tizimdagi barcha hududlar (viloyatlar) ro'yxatini ko'p tilli formatda olish.
    
    Ushbu API hududlar ro'yxatini qaytaradi. `name` maydoni so'rovdagi tilga mos ravishda tarjima qilinadi.
    
    **Tilni aniqlash ustuvorligi (Language Resolution Priority):**
    1. **Accept-Language sarlavhasi** (masalan: `Accept-Language: ru`)
    2. **lang query parametri** (masalan: `?lang=en`)
    3. Tizimga kirgan foydalanuvchining shaxsiy sozlamasi (`preferred_lang`)
    4. Standart til (`uz`)
    
    **Qo'llab-quvvatlanadigan tillar:** `uz`, `ru`, `en`, `tr`.
    """
    query = select(Region).order_by(Region.id)
    result = await db.execute(query)
    regions = result.scalars().all()
    return [r.to_response(lang) for r in regions]
