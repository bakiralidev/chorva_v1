import uuid
from datetime import datetime
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
from app.schemas.advertisement import AdvertisementCreate, AdvertisementResponse, AdvertisementDetailResponse, AdvertisementUpdate
from app.auth.dependencies import get_current_user
from app.utils.lang import get_lang

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
    ### Barcha faol e'lonlar ro'yxatini olish (Filtrlar bilan).
    
    Tizimdagi faol, sotilmagan va o'chirilmagan barcha e'lonlar ro'yxatini olish uchun ishlatiladi.
    Ushbu endpoint **barcha uchun ochiq** bo'lib, avtorizatsiyadan o'tish talab etilmaydi.
    
    **Dinamik filtrlar:**
    * **category**: Kategoriya slugi (masalan, `qoramol`).
    * **region_id**: Hudud/viloyat ID raqami.
    * **min_price / max_price**: Narxlar oralig'i bo'yicha cheklash.
    * **search**: E'lon sarlavhasi (title) yoki tavsifi (description) bo'yicha kalit so'z orqali qidirish.
    
    **Paginatsiya va tartiblash:**
    * So'rovlar `limit` va `offset` orqali paginatsiya qilinadi.
    * Javobda avval `is_top == True` bo'lgan e'lonlar, so'ngra yangi qo'shilgan e'lonlar birinchi bo'lib chiqadi.
    """
    # Faqat faol va o'chirilmagan e'lonlarni yuklaymiz
    query = select(Advertisement).options(
        selectinload(Advertisement.images)
    ).where(Advertisement.status == AdStatus.active, Advertisement.is_deleted == False)

    # Filtr: Kategoriya slugi
    if category:
        from app.models.category import CategoryTranslation
        query = query.join(Advertisement.category).join(Category.translations).where(CategoryTranslation.slug == category)

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


@router.get("/my", response_model=list[AdvertisementResponse])
async def list_my_advertisements(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ### Tizimga kirgan foydalanuvchining shaxsiy e'lonlari ro'yxatini olish.
    
    Faqatgina ro'yxatdan o'tgan foydalanuvchi o'ziga tegishli bo'lgan barcha holatdagi (faol, nofaol, sotilgan) va o'chirilmagan e'lonlarini ko'ra oladi.
    
    **So'rov sarlavhalari (Request Headers):**
    * `Authorization: Bearer <access_token>` (Majburiy)
    
    **Muayyan Xatoliklar (Error States):**
    * **401 Unauthorized**: JWT token yuborilmagan yoki eskirgan bo'lsa.
    """
    query = select(Advertisement).options(
        selectinload(Advertisement.images)
    ).where(
        Advertisement.user_id == current_user.id,
        Advertisement.is_deleted == False
    ).order_by(
        Advertisement.created_at.desc()
    ).offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{id}", response_model=AdvertisementDetailResponse)
async def get_advertisement_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang)
):
    """
    ### Muayyan e'lonning batafsil ma'lumotlarini olish.
    
    ID raqami bo'yicha bitta e'lonning to'liq ma'lumotlarini qaytaradi.
    * Ushbu endpoint **barcha uchun ochiq** bo'lib, avtorizatsiyadan o'tish talab etilmaydi.
    * Har gal ushbu endpointga so'rov yuborilganda, e'lonning ko'rishlar soni (`views_count`) bazada avtomatik ravishda **1 taga oshiriladi**.
    * E'londagi kategoriya va hudud nomlari so'rovda ko'rsatilgan tilga mos ravishda tarjima qilib qaytariladi.
    
    **Tilni aniqlash ustuvorligi (Language Resolution Priority):**
    * `Accept-Language` header yoki `?lang=...` query parametri orqali boshqariladi.
    
    **Muayyan Xatoliklar (Error States):**
    * **404 Not Found**: Agar berilgan ID bo'yicha e'lon topilmasa yoki u o'chirilgan bo'lsa.
    """
    query = select(Advertisement).options(
        selectinload(Advertisement.user),
        selectinload(Advertisement.category),
        selectinload(Advertisement.region),
        selectinload(Advertisement.images)
    ).where(Advertisement.id == id, Advertisement.is_deleted == False)

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
    
    return {
        "id": ad.id,
        "title": ad.title,
        "description": ad.description,
        "price": ad.price,
        "is_negotiable": ad.is_negotiable,
        "age": ad.age,
        "weight": ad.weight,
        "color": ad.color,
        "quantity": ad.quantity,
        "contact_phone": ad.contact_phone,
        "views_count": ad.views_count,
        "is_top": ad.is_top,
        "status": ad.status,
        "created_at": ad.created_at,
        "updated_at": ad.updated_at,
        "user": ad.user,
        "category": ad.category.to_response(lang),
        "region": ad.region.to_response(lang),
        "images": ad.images
    }


@router.post("/", response_model=AdvertisementResponse, status_code=status.HTTP_201_CREATED)
async def create_advertisement(
    ad_in: AdvertisementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ### Yangi e'lon qo'shish.
    
    Tizimga kirgan foydalanuvchilar tomonidan yangi e'lonlar qo'shish uchun ishlatiladi.
    
    * E'lon yaratilganda uning holati avtomatik ravishda `active` deb belgilanadi va top-elonligi `is_top = False` bo'ladi.
    * E'longa bir nechta rasmlar bog'lanishi mumkin. Agar rasmlar ichidan hech biri `is_main = True` (asosiy rasm) qilinmagan bo'lsa, birinchi yuborilgan rasm avtomatik asosiy rasm qilib olinadi.
    
    **So'rov sarlavhalari (Request Headers):**
    * `Authorization: Bearer <access_token>` (Majburiy)
    
    **Muayyan Xatoliklar (Error States):**
    * **401 Unauthorized**: JWT token yuborilmagan yoki noto'g'ri bo'lsa.
    * **400 Bad Request**: 
      * Agar yuborilgan `category_id` yoki `region_id` tizimda mavjud bo'lmasa.
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
        valid_images = [img for img in ad_in.images if img.image_url]
        has_main = any(img.is_main for img in valid_images)
        for idx, img_in in enumerate(valid_images):
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


@router.put("/{id}", response_model=AdvertisementResponse)
async def update_advertisement(
    id: uuid.UUID,
    ad_update: AdvertisementUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ### Foydalanuvchining o'z e'lonini tahrirlashi.
    
    Tizimga kirgan foydalanuvchi faqat o'ziga tegishli bo'lgan va o'chirilmagan e'lonni tahrirlashi mumkin.
    
    * Barcha kiruvchi maydonlar ixtiyoriy (optional). Faqat o'zgartiriladigan maydonlarni yuborish yetarli.
    * Agar `images` ro'yxati yuborilsa, e'lonning eski rasmlari butunlay o'chirilib, yangilari bilan almashtiriladi.
    * E'lon tahrirlanganda `updated_at` maydoni avtomatik tarzda tahrirlangan vaqt bilan yangilanadi.
    
    **So'rov sarlavhalari (Request Headers):**
    * `Authorization: Bearer <access_token>` (Majburiy)
    
    **Muayyan Xatoliklar (Error States):**
    * **401 Unauthorized**: JWT token yuborilmagan yoki eskirgan bo'lsa.
    * **403 Forbidden**: Agar foydalanuvchi boshqa shaxsga tegishli e'lonni tahrirlamoqchi bo'lsa.
    * **404 Not Found**: Agar e'lon topilmasa yoki o'chirilgan bo'lsa.
    * **400 Bad Request**: Agar yangilanayotgan `category_id` yoki `region_id` tizimda mavjud bo'lmasa.
    """
    query = select(Advertisement).options(
        selectinload(Advertisement.images)
    ).where(Advertisement.id == id, Advertisement.is_deleted == False)
    
    result = await db.execute(query)
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E'lon topilmadi."
        )
        
    if ad.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sizda ushbu e'lonni tahrirlash huquqi yo'q."
        )
        
    if ad_update.category_id is not None:
        cat_query = select(Category).where(Category.id == ad_update.category_id)
        cat_res = await db.execute(cat_query)
        if not cat_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kiritilgan kategoriya mavjud emas."
            )
        ad.category_id = ad_update.category_id
        
    if ad_update.region_id is not None:
        reg_query = select(Region).where(Region.id == ad_update.region_id)
        reg_res = await db.execute(reg_query)
        if not reg_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kiritilgan hudud/viloyat mavjud emas."
            )
        ad.region_id = ad_update.region_id

    update_data = ad_update.model_dump(exclude_unset=True, exclude={"category_id", "region_id", "images"})
    for key, value in update_data.items():
        setattr(ad, key, value)
        
    if ad_update.images is not None:
        from sqlalchemy import delete
        await db.execute(delete(Image).where(Image.advertisement_id == ad.id))
        
        valid_images = [img for img in ad_update.images if img.image_url]
        has_main = any(img.is_main for img in valid_images)
        for idx, img_in in enumerate(valid_images):
            is_main = img_in.is_main
            if not has_main and idx == 0:
                is_main = True
            new_image = Image(
                advertisement_id=ad.id,
                image_url=img_in.image_url,
                is_main=is_main
            )
            db.add(new_image)

    ad.updated_at = datetime.utcnow()
    await db.commit()
    
    result_query = select(Advertisement).options(
        selectinload(Advertisement.images)
    ).where(Advertisement.id == ad.id)
    result = await db.execute(result_query)
    return result.scalar_one()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_advertisement(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ### Foydalanuvchining o'z e'lonini o'chirishi (Soft Delete).
    
    E'lonni tizimdan butunlay o'chirib yubormaydi.
    * E'lonning `is_deleted` maydoni `True` qilinadi.
    * `deleted_at` maydoniga o'chirilgan sana yoziladi.
    * Foydalanuvchi faqat o'ziga tegishli bo'lgan e'lonni o'chira oladi.
    
    **So'rov sarlavhalari (Request Headers):**
    * `Authorization: Bearer <access_token>` (Majburiy)
    
    **Muayyan Xatoliklar (Error States):**
    * **401 Unauthorized**: JWT token yuborilmagan yoki eskirgan bo'lsa.
    * **403 Forbidden**: Agar foydalanuvchi boshqa shaxsga tegishli e'lonni o'chirmoqchi bo'lsa.
    * **404 Not Found**: Agar e'lon topilmasa yoki allaqachon o'chirilgan bo'lsa.
    """
    query = select(Advertisement).where(Advertisement.id == id, Advertisement.is_deleted == False)
    result = await db.execute(query)
    ad = result.scalar_one_or_none()
    
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E'lon topilmadi."
        )
        
    if ad.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sizda ushbu e'lonni o'chirish huquqi yo'q."
        )
        
    from datetime import datetime
    ad.is_deleted = True
    ad.deleted_at = datetime.utcnow()
    
    db.add(ad)
    await db.commit()
    return None
