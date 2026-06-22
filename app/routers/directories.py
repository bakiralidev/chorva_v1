from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.category import Category
from app.models.region import Region
from app.schemas.category import CategoryResponse
from app.schemas.region import RegionResponse

router = APIRouter(prefix="/directories", tags=["Directories"])

@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """
    Tizimdagi barcha kategoriyalar ro'yxatini olish (Qoramol, Qo'y, Echki, Ot va hkz).
    """
    query = select(Category).order_by(Category.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/regions", response_model=list[RegionResponse])
async def get_regions(db: AsyncSession = Depends(get_db)):
    """
    Tizimdagi barcha hududlar (viloyatlar) ro'yxatini olish (Toshkent, Samarqand va hkz).
    """
    query = select(Region).order_by(Region.id)
    result = await db.execute(query)
    return result.scalars().all()
