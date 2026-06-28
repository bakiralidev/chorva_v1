from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user import User
from app.models.region import Region, RegionTranslation
from app.schemas.region import RegionCreate, RegionResponse
from app.auth.dependencies import get_current_active_superuser

router = APIRouter(prefix="/regions", tags=["Admin Regions"])

@router.post("/", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
async def create_region(
    region_in: RegionCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] Yangi hudud/viloyat yaratish.
    """
    # Hudud nomi unikal ekanligini tekshirish
    query = select(Region).join(Region.translations).where(RegionTranslation.name == region_in.name)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ushbu nomdagi hudud/viloyat allaqachon mavjud."
        )

    db_reg = Region(name=region_in.name)
    db.add(db_reg)
    await db.commit()
    await db.refresh(db_reg)
    return db_reg

@router.put("/{id}", response_model=RegionResponse)
async def update_region(
    id: int,
    region_in: RegionCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] Hudud/viloyat nomini o'zgartirish.
    """
    query = select(Region).where(Region.id == id)
    result = await db.execute(query)
    db_reg = result.scalar_one_or_none()
    if not db_reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hudud/viloyat topilmadi."
        )

    # Nomi boshqasi bilan mos kelmasligini tekshirish
    if region_in.name != db_reg.name:
        query_name = select(Region).join(Region.translations).where(RegionTranslation.name == region_in.name)
        result_name = await db.execute(query_name)
        if result_name.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ushbu nomdagi hudud/viloyat allaqachon mavjud."
            )

    db_reg.name = region_in.name
    db.add(db_reg)
    await db.commit()
    await db.refresh(db_reg)
    return db_reg

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_region(
    id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] Hudud/viloyatni o'chirish.
    """
    query = select(Region).where(Region.id == id)
    result = await db.execute(query)
    db_reg = result.scalar_one_or_none()
    if not db_reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hudud/viloyat topilmadi."
        )

    await db.delete(db_reg)
    await db.commit()
    return None
