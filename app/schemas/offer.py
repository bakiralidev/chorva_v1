from pydantic import BaseModel, ConfigDict
from datetime import datetime

class OfferResponse(BaseModel):
    id: int
    title: str | None = ""
    content: str | None = ""
    has_file: bool = False
    file_url: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Foydalanish shartlari (Ommaviy oferta)",
                "content": "Ushbu tizimdan foydalanish qoidalari...",
                "has_file": False,
                "file_url": None,
                "is_active": True,
                "created_at": "2026-06-27T00:00:00Z"
            }
        }
    )
