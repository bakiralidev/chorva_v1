import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, File, UploadFile
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
        "gender": ad.gender,
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
    title: str = Form(..., min_length=3, max_length=255, description="E'lon sarlavhasi (Masalan: 'Sotiladigan sog'lom sigir')"),
    description: str = Form(..., min_length=10, description="E'lon tavsifi (Chorva haqida batafsil ma'lumot)"),
    price: float | None = Form(None, description="Narxi so'mda (Kelishiladigan bo'lsa yubormaslik mumkin)"),
    is_negotiable: bool = Form(False, description="Narxi kelishiladigan bo'lsa 'true', aks holda 'false'"),
    age: str | None = Form(None, description="Yoshi (Masalan: '2 yosh', '1 yosh-u 3 oylik')"),
    weight: str | None = Form(None, description="Vazni (Masalan: '350 kg')"),
    color: str | None = Form(None, description="Rangi (Masalan: 'Qora', 'Qizil-ola')"),
    gender: str | None = Form(None, description="Hayvon jinsi (Masalan: 'Erkak', 'Urgochi')"),
    quantity: int = Form(1, ge=1, description="Sotiladigan chorva soni"),
    contact_phone: str = Form(..., min_length=7, max_length=50, description="Aloqa telefon raqami"),
    category_id: int = Form(..., description="Tizimdan olingan kategoriya ID raqami"),
    region_id: int = Form(..., description="Tizimdan olingan hudud/viloyat ID raqami"),
    images: list[UploadFile] = File(None, description="E'lon rasmlari fayllari (Maksimal 5 tagacha rasm jo'natish mumkin)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ### Yangi e'lon joylashtirish (Fayl yuklash bilan birga).
    
    Ushbu endpoint veb-sayt foydalanuvchilari uchun rasm fayllari bilan birgalikda yangi e'lon joylashtirish uchun mo'ljallangan. 
    So'rov formatini **`multipart/form-data`** ko'rinishida yuborish lozim.
    
    ---
    ### 📌 Muhim Qoidalar va Ishlash Mantiqi:
    1. **Rasm fayllari yuklash:**
       * `images` maydonida 1 tadan 5 tagacha haqiqiy rasm faylini yuborishingiz mumkin.
       * Birinchi yuborilgan rasm avtomatik ravishda e'lonning **asosiy (bosh) rasmi** (`is_main = True`) qilib belgilanadi.
       * Yuklangan barcha rasmlar serverning `uploads/ad_pics` papkasiga saqlanadi va unikal nomga ega bo'ladi.
    2. **Avtorizatsiya:**
       * Ushbu API faqat ro'yxatdan o'tgan va tizimga kirgan foydalanuvchilar uchun ochiq.
       * `Authorization: Bearer <access_token>` sarlavhasini yuborish shart.
    3. **Validatsiyalar:**
       * `category_id` va `region_id` tizimda mavjud bo'shigi shart (avval tegishli ma'lumotnomalardan yuklab oling).
       * Sarlavha kamida 3 ta belgi, tavsif esa kamida 10 ta belgidan iborat bo'lishi lozim.
       
    ---
    ### 💻 Frontendchilar uchun Qo'llanish Qo'llanmasi (Spoon-Feed Examples):
    
    #### 1️⃣ JavaScript (`axios` yordamida `FormData` jo'natish):
    ```javascript
    // 1. FormData ob'ektini yaratamiz
    const formData = new FormData();
    
    // 2. Oddiy matnli maydonlarni qo'shamiz
    formData.append('title', 'Sotiladigan baquvvat zotdor buqa');
    formData.append('description', '2 yoshli, juda baquvvat va sog\'lom buqa sotiladi. Emlashlari qilingan.');
    formData.append('price', 12500000);
    formData.append('is_negotiable', true);
    formData.append('age', '2 yosh');
    formData.append('weight', '450 kg');
    formData.append('color', 'Qora-ola');
    formData.append('quantity', 1);
    formData.append('contact_phone', '+998901234567');
    formData.append('category_id', 1); // Kategoriya ID
    formData.append('region_id', 1);   // Viloyat ID
    
    // 3. Foydalanuvchi tanlagan rasmlarni qo'shamiz (masalan, HTML inputdan olingan fileList)
    const files = document.querySelector('input[type="file"]').files;
    for (let i = 0; i < files.length; i++) {
        formData.append('images', files[i]); // Har bir faylni ketma-ket bir xil 'images' kaliti ostida qo'shamiz
    }
    
    // 4. API ga so'rov yuboramiz
    axios.post('http://127.0.0.1:8000/api/v1/front/ads/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data', // Axios buni avtomatik o'rnatadi, lekin qo'lda yozish ham mumkin
            'Authorization': `Bearer ${yourAccessToken}`
        }
    })
    .then(response => {
        console.log('E\'lon muvaffaqiyatli yaratildi:', response.data);
    })
    .catch(error => {
        console.error('Xatolik:', error.response.data);
    });
    ```
    
    #### 2️⃣ JavaScript (`Fetch API` yordamida):
    ```javascript
    const formData = new FormData();
    // (maydonlarni append qilish yuqoridagidek)
    
    fetch('http://127.0.0.1:8000/api/v1/front/ads/', {
        method: 'POST',
        headers: {
            // DIQQAT: Fetch API da Content-Type ni yozmang! Brauzer uning chegarasini (boundary) o'zi aniqlab yozadi.
            'Authorization': `Bearer ${yourAccessToken}`
        },
        body: formData
    })
    .then(res => res.json())
    .then(data => console.log(data));
    ```

    #### 3️⃣ `curl` orqali sinov so'rovi:
    ```bash
    curl -X POST "http://127.0.0.1:8000/api/v1/front/ads/" \
      -H "Authorization: Bearer ACCESS_TOKEN_SHU_YERDA" \
      -H "Content-Type: multipart/form-data" \
      -F "title=Simmental sigir" \
      -F "description=Sog'lom zotdor sigir sotiladi" \
      -F "price=12000000" \
      -F "is_negotiable=true" \
      -F "age=3 yosh" \
      -F "weight=400 kg" \
      -F "color=Qizil-ola" \
      -F "quantity=1" \
      -F "contact_phone=+998901112233" \
      -F "category_id=1" \
      -F "region_id=1" \
      -F "images=@/path/to/image1.jpg" \
      -F "images=@/path/to/image2.jpg"
    ```
    
    ---
    ### ⚠️ Xatolik Holatlari (Error Responses):
    * **401 Unauthorized:** JWT Token yuborilmagan, eskirgan yoki xato.
    * **400 Bad Request (Kategoriya topilmaganda):** `{"detail": "Kiritilgan kategoriya mavjud emas."}`
    * **400 Bad Request (Viloyat topilmaganda):** `{"detail": "Kiritilgan hudud/viloyat mavjud emas."}`
    * **422 Unprocessable Entity:** Majburiy maydonlar to'ldirilmagan yoki validatsiya xatosi (masalan, title < 3 ta belgi).
    """
    # Kategoriya borligini tekshirish
    category_query = select(Category).where(Category.id == category_id)
    category_res = await db.execute(category_query)
    if not category_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kiritilgan kategoriya mavjud emas."
        )

    # Hudud borligini tekshirish
    region_query = select(Region).where(Region.id == region_id)
    region_res = await db.execute(region_query)
    if not region_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kiritilgan hudud/viloyat mavjud emas."
        )

    # Reklamani yaratish
    new_ad = Advertisement(
        user_id=current_user.id,
        category_id=category_id,
        region_id=region_id,
        title=title,
        description=description,
        price=price,
        is_negotiable=is_negotiable,
        age=age,
        weight=weight,
        color=color,
        gender=gender,
        quantity=quantity,
        contact_phone=contact_phone,
        status=AdStatus.active,
        views_count=0,
        is_top=False
    )
    db.add(new_ad)
    await db.flush()  # ID sini olish uchun flush

    # Rasmlarni yuklash va bazaga bog'lash
    if images:
        import os
        upload_dir = os.path.join("uploads", "ad_pics")
        os.makedirs(upload_dir, exist_ok=True)
        
        valid_images = [img for img in images if img.filename]
        for idx, img in enumerate(valid_images):
            # Unikal nom beramiz va diskka saqlaymiz
            file_ext = os.path.splitext(img.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Faylni diskka yozish
            content = await img.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Birinchi yuborilgan rasmni avtomatik ravishda asosiy (is_main = True) qilamiz
            is_main = (idx == 0)
            
            new_image = Image(
                advertisement_id=new_ad.id,
                image_url=f"/uploads/ad_pics/{unique_filename}",
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
    title: str | None = Form(None, min_length=3, max_length=255),
    description: str | None = Form(None, min_length=10),
    price: float | None = Form(None),
    is_negotiable: bool | None = Form(None),
    age: str | None = Form(None),
    weight: str | None = Form(None),
    color: str | None = Form(None),
    gender: str | None = Form(None),
    quantity: int | None = Form(None, ge=1),
    contact_phone: str | None = Form(None, min_length=7, max_length=50),
    category_id: int | None = Form(None),
    region_id: int | None = Form(None),
    images: list[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ### Foydalanuvchining o'z e'lonini tahrirlashi (Fayl yuklash bilan).
    
    Tizimga kirgan foydalanuvchi faqat o'ziga tegishli bo'lgan va o'chirilmagan e'lonni tahrirlashi mumkin.
    So'rov formatini **`multipart/form-data`** ko'rinishida yuborish lozim.
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
        
    if category_id is not None:
        cat_query = select(Category).where(Category.id == category_id)
        cat_res = await db.execute(cat_query)
        if not cat_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kiritilgan kategoriya mavjud emas."
            )
        ad.category_id = category_id
        
    if region_id is not None:
        reg_query = select(Region).where(Region.id == region_id)
        reg_res = await db.execute(reg_query)
        if not reg_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kiritilgan hudud/viloyat mavjud emas."
            )
        ad.region_id = region_id

    if title is not None:
        ad.title = title
    if description is not None:
        ad.description = description
    if price is not None:
        ad.price = price
    if is_negotiable is not None:
        ad.is_negotiable = is_negotiable
    if age is not None:
        ad.age = age
    if weight is not None:
        ad.weight = weight
    if color is not None:
        ad.color = color
    if gender is not None:
        ad.gender = gender
    if quantity is not None:
        ad.quantity = quantity
    if contact_phone is not None:
        ad.contact_phone = contact_phone
        
    valid_images = [img for img in images if img and img.filename] if images else []
    if valid_images:
        import os
        import shutil
        # Delete old images from disk
        for img in ad.images:
            if img.image_url and img.image_url.startswith("/uploads/"):
                filename = img.image_url.replace("/uploads/", "")
                file_path = os.path.join("uploads", filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
        
        # Clear the old images from relationship collection (automatically deletes from DB due to delete-orphan cascade)
        ad.images.clear()
        
        # Save and append new images
        upload_dir = os.path.join("uploads", "ad_pics")
        os.makedirs(upload_dir, exist_ok=True)
        
        for idx, img in enumerate(valid_images):
            file_ext = os.path.splitext(img.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            content = await img.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            is_main = (idx == 0)
            
            new_image = Image(
                image_url=f"/uploads/ad_pics/{unique_filename}",
                is_main=is_main
            )
            ad.images.append(new_image)

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
