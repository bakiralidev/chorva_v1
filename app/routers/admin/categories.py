from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user import User
from app.models.category import Category, CategoryTranslation
from app.schemas.category import CategoryCreate, CategoryResponse
from app.auth.dependencies import get_current_active_superuser

router = APIRouter(prefix="/categories", tags=["Admin Categories"])

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    cat_in: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] Yangi kategoriya yaratish.
    """
    # Slug unikal ekanligini tekshirish
    query = select(Category).join(Category.translations).where(CategoryTranslation.slug == cat_in.slug)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ushbu slug manzilli kategoriya allaqachon mavjud."
        )

    db_cat = Category(
        name=cat_in.name,
        slug=cat_in.slug,
        icon_url=cat_in.icon_url
    )
    db.add(db_cat)
    await db.commit()
    await db.refresh(db_cat)
    return db_cat

@router.put("/{id}", response_model=CategoryResponse)
async def update_category(
    id: int,
    cat_in: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] Kategoriyani tahrirlash.
    """
    query = select(Category).where(Category.id == id)
    result = await db.execute(query)
    db_cat = result.scalar_one_or_none()
    if not db_cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategoriya topilmadi."
        )

    # Slug boshqasi bilan mos kelmasligini tekshirish
    if cat_in.slug != db_cat.slug:
        query_slug = select(Category).join(Category.translations).where(CategoryTranslation.slug == cat_in.slug)
        result_slug = await db.execute(query_slug)
        if result_slug.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ushbu slug manzilli kategoriya allaqachon mavjud."
            )

    db_cat.name = cat_in.name
    db_cat.slug = cat_in.slug
    db_cat.icon_url = cat_in.icon_url
    db.add(db_cat)
    await db.commit()
    await db.refresh(db_cat)
    return db_cat

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_superuser)
):
    """
    [Admin] Kategoriyani o'chirish.
    """
    query = select(Category).where(Category.id == id)
    result = await db.execute(query)
    db_cat = result.scalar_one_or_none()
    if not db_cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategoriya topilmadi."
        )

    await db.delete(db_cat)
    await db.commit()
    return None
