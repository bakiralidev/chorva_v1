from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.offer import Offer
from app.schemas.offer import OfferResponse
from app.utils.lang import get_lang

router = APIRouter(prefix="/offers", tags=["Offers"])

@router.get("/active", response_model=OfferResponse)
async def get_active_offer(
    db: AsyncSession = Depends(get_db),
    lang: str = Depends(get_lang)
):
    """
    ### Faol Ommaviy ofertani olish.
    
    Tizimdagi hozirgi vaqtda amal qilib turgan ommaviy ofertani (Terms of Service) qaytaradi.
    
    **Ishlash qoidalari va ishlatilishi (Frontend/Mobile dasturchilar uchun):**
    
    * **`has_file` parametriga qarab ish tuting:**
      * **`has_file == true` bo'lsa (Faylli oferta):**
        * Tizimda PDF/Doc fayl biriktirilgan bo'ladi.
        * `file_url` maydonida fayl manzili (masalan: `/uploads/filename.pdf`) qaytadi. 
        * `title` va `content` maydonlari bo'sh (`""` yoki `null`) bo'ladi.
        * **Ishlatilishi**: Frontend/Mobile ilovada foydalanuvchiga matn o'rniga faylni ko'rish yoki yuklab olish tugmasini ko'rsatish lozim (Havola: `BaseURL + file_url`).
      * **`has_file == false` bo'lsa (Matnli oferta):**
        * `file_url` qiymati `null` bo'ladi.
        * `title` va `content` maydonlarida ofertaning tarjima qilingan sarlavha va matn qiymatlari qaytadi.
        * **Ishlatilishi**: Foydalanuvchiga ofertani sahifada to'g'ridan-to'g'ri matn (HTML/Text) ko'rinishida ko'rsatish lozim.
        
    * **Til tanlash**:
      * Agar so'ralgan tilda tarjima mavjud bo'lsa, o'sha tilda qaytaradi.
      * Tarjima mavjud bo'lmasa, standart til (uz) dagi matn qaytariladi.
    """
    query = select(Offer).options(
        selectinload(Offer.translations)
    ).where(Offer.is_active == True)

    result = await db.execute(query)
    offer = result.scalar_one_or_none()

    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faol oferta topilmadi."
        )

    return offer.to_response(lang)
