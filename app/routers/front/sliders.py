from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.slider import Slider
from app.schemas.slider import SliderResponse

router = APIRouter(prefix="/sliders", tags=["Sliders"])

@router.get("/", response_model=list[SliderResponse])
async def list_sliders(db: AsyncSession = Depends(get_db)):
    """
    ### Barcha faol sliderlar ro'yxatini olish.
    
    Bosh sahifadagi karusel/slider uchun rasmlar va tegishli havolalar ro'yxatini qaytaradi.
    Ushbu API hamma uchun ochiq (avtorizatsiyasiz).
    """
    query = select(Slider).order_by(Slider.id)
    result = await db.execute(query)
    return result.scalars().all()
