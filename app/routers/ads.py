import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, and_

from app.database import get_db
from app.models.user import User
from app.models.category import Category
from app.models.region import Region
from app.models.advertisement import Advertisement, AdStatus
from app.models.image import Image
from app.schemas.advertisement import AdvertisementCreate, AdvertisementResponse, AdvertisementDetailResponse
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/ads", tags=["Advertisements"])

@router.get("/", response_model=list[AdvertisementResponse])
async def list_advertisements(
    category: str | None = Query(default=None, description="Kategoriya slugi (masalan: qoramol)"),
    region_id: int | None = Query(default=None, description="Viloyat IDsi"),
    min_price: float | None = Query(default=None, description="Minimal narx"),
    max_price: float | None = Query(default=None, description="Maksimal narx"),
    search: str | None = Query(default=None, description="Sarlavha yoki tavsif bo'yicha qidiruv kalit so'zi"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    E'lonlar ro'yxatini olish.
    Kategoriya, hudud, narx va qidiruv bo'yicha dinamik filtrlar qo'llaniladi.
    """
    # Faqat 'active' (faol) e'lonlarni yuklaymiz
    query = select(Advertisement).options(
        selectinload(Advertisement.images)
    ).where(Advertisement.status == AdStatus.active)

    # Filtr: Kategoriya slugi
    if category:
        query = query.join(Advertisement.category).where(Category.slug == category)

    # Filtr: Hudud ID
    if region_id:
        query = query.where(Advertisement.region_id == region_id)

    # Filtr: Minimal narx
    if min_price is not None:
        query = query.where(Advertisement.price >= min_price)

    # Filtr: Maksimal narx
    if max_price is not None:
        query = query.where(Advertisement.price <= max_price)

    # Filtr: Qidiruv (ilike)
    if search:
        query = query.where(
            or_(
                Advertisement.title.ilike(f"%{search}%"),
                Advertisement.description.ilike(f"%{search}%")
            )
        )

    # Eng yangi e'lonlar birinchi bo'lib chiqadi, saralash
    query = query.order_by(Advertisement.is_top.desc(), Advertisement.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{id}", response_model=AdvertisementDetailResponse)
async def get_advertisement_detail(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Bitta e'lonning batafsil ma'lumotini olish va ko'rishlar sonini (views_count) bittaga oshirish.
    """
    query = select(Advertisement).options(
        selectinload(Advertisement.user),
        selectinload(Advertisement.category),
        selectinload(Advertisement.region),
        selectinload(Advertisement.images)
    ).where(Advertisement.id == id)

    result = await db.execute(query)
    ad = result.scalar_one_or_none()

    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E'lon topilmadi."
        )

    # Ko'rishlar sonini oshirish
    ad.views_count += 1
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    
    return ad


@router.post("/", response_model=AdvertisementResponse, status_code=status.HTTP_201_CREATED)
async def create_advertisement(
    ad_in: AdvertisementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Yangi e'lon qo'shish. Faqat ro'yxatdan o'tgan foydalanuvchilar (JWT tokeni borlar) qila oladi.
    """
    # Kategoriya borligini tekshirish
    category_query = select(Category).where(Category.id == ad_in.category_id)
    category_res = await db.execute(category_query)
    if not category_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kiritilgan kategoriya mavjud emas."
        )

    # Hudud borligini tekshirish
    region_query = select(Region).where(Region.id == ad_in.region_id)
    region_res = await db.execute(region_query)
    if not region_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kiritilgan hudud/viloyat mavjud emas."
        )

    # Reklamani yaratish
    new_ad = Advertisement(
        user_id=current_user.id,
        category_id=ad_in.category_id,
        region_id=ad_in.region_id,
        title=ad_in.title,
        description=ad_in.description,
        price=ad_in.price,
        is_negotiable=ad_in.is_negotiable,
        age=ad_in.age,
        weight=ad_in.weight,
        color=ad_in.color,
        quantity=ad_in.quantity,
        contact_phone=ad_in.contact_phone,
        status=AdStatus.active,
        views_count=0,
        is_top=False
    )
    db.add(new_ad)
    await db.flush()  # ID sini olish uchun flush

    # Rasmlarni bog'lash
    if ad_in.images:
        has_main = any(img.is_main for img in ad_in.images)
        for idx, img_in in enumerate(ad_in.images):
            # Agar birorta ham rasm main deb belgilanmagan bo'lsa, birinchisini main qilamiz
            is_main = img_in.is_main
            if not has_main and idx == 0:
                is_main = True
            
            new_image = Image(
                advertisement_id=new_ad.id,
                image_url=img_in.image_url,
                is_main=is_main
            )
            db.add(new_image)

    await db.commit()

    # Yangi e'lonni rasmlari bilan qayta o'qish
    result_query = select(Advertisement).options(
        selectinload(Advertisement.images)
    ).where(Advertisement.id == new_ad.id)
    result = await db.execute(result_query)
    return result.scalar_one()
