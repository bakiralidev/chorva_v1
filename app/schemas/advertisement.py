import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.advertisement import AdStatus
from app.schemas.user import UserResponse
from app.schemas.category import CategoryResponse
from app.schemas.region import RegionResponse

class AdImageCreate(BaseModel):
    image_url: str | None = None
    is_main: bool = False

class AdImageResponse(BaseModel):
    id: int
    image_url: str
    is_main: bool

    model_config = ConfigDict(from_attributes=True)

class AdvertisementBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    price: float | None = None
    is_negotiable: bool = False
    age: str | None = None
    weight: str | None = None
    color: str | None = None
    gender: str | None = None
    quantity: int = Field(default=1, ge=1)
    contact_phone: str = Field(..., min_length=7, max_length=50)

class AdvertisementCreate(AdvertisementBase):
    category_id: int
    region_id: int
    images: list[AdImageCreate] | None = Field(default=None, description="E'lon rasmlari ro'yxati")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Sotiladigan baquvvat buqa",
                "description": "2 yoshli, juda baquvvat va sog'lom zotdor buqa sotiladi. Barcha emlashlari qilingan.",
                "price": 12500000.0,
                "is_negotiable": True,
                "age": "2 yosh",
                "weight": "450 kg",
                "color": "Qora-ola",
                "quantity": 1,
                "contact_phone": "+998901234567",
                "category_id": 1,
                "region_id": 1,
                "images": [
                    {
                        "image_url": "/uploads/ad_pics/bull1.jpg",
                        "is_main": True
                    },
                    {
                        "image_url": "/uploads/ad_pics/bull2.jpg",
                        "is_main": False
                    }
                ]
            }
        }
    )

class AdvertisementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=10)
    price: float | None = None
    is_negotiable: bool | None = None
    age: str | None = None
    weight: str | None = None
    color: str | None = None
    gender: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    contact_phone: str | None = Field(default=None, min_length=7, max_length=50)
    category_id: int | None = None
    region_id: int | None = None
    images: list[AdImageCreate] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Sotiladigan baquvvat zotdor buqa (kelishiladi)",
                "price": 12000000.0,
                "is_negotiable": True
            }
        }
    )

class AdvertisementResponse(AdvertisementBase):
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: int
    region_id: int
    views_count: int
    is_top: bool
    status: AdStatus
    created_at: datetime
    updated_at: datetime | None = None
    images: list[AdImageResponse] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "987f6543-e21b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "category_id": 1,
                "region_id": 1,
                "title": "Sotiladigan baquvvat buqa",
                "description": "2 yoshli, juda baquvvat va sog'lom zotdor buqa sotiladi. Barcha emlashlari qilingan.",
                "price": 12500000.0,
                "is_negotiable": True,
                "age": "2 yosh",
                "weight": "450 kg",
                "color": "Qora-ola",
                "quantity": 1,
                "contact_phone": "+998901234567",
                "views_count": 42,
                "is_top": False,
                "status": "active",
                "created_at": "2026-06-27T00:00:00Z",
                "updated_at": "2026-06-27T00:05:00Z",
                "images": [
                    {
                        "id": 1,
                        "image_url": "/uploads/ad_pics/bull1.jpg",
                        "is_main": True
                    }
                ]
            }
        }
    )

class AdvertisementDetailResponse(AdvertisementBase):
    id: uuid.UUID
    user: UserResponse
    category: CategoryResponse
    region: RegionResponse
    views_count: int
    is_top: bool
    status: AdStatus
    created_at: datetime
    updated_at: datetime | None = None
    images: list[AdImageResponse] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "987f6543-e21b-12d3-a456-426614174000",
                "title": "Sotiladigan baquvvat buqa",
                "description": "2 yoshli, juda baquvvat va sog'lom zotdor buqa sotiladi. Barcha emlashlari qilingan.",
                "price": 12500000.0,
                "is_negotiable": True,
                "age": "2 yosh",
                "weight": "450 kg",
                "color": "Qora-ola",
                "quantity": 1,
                "contact_phone": "+998901234567",
                "views_count": 42,
                "is_top": False,
                "status": "active",
                "created_at": "2026-06-27T00:00:00Z",
                "updated_at": "2026-06-27T00:05:00Z",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "phone_number": "+998901234567",
                    "is_active": True,
                    "is_superuser": False,
                    "created_at": "2026-06-27T00:00:00Z"
                },
                "category": {
                    "id": 1,
                    "name": "Qoramol",
                    "slug": "qoramol",
                    "icon_url": "/uploads/categories/cattle.png"
                },
                "region": {
                    "id": 1,
                    "name": "Toshkent viloyati"
                },
                "images": [
                    {
                        "id": 1,
                        "image_url": "/uploads/ad_pics/bull1.jpg",
                        "is_main": True
                    }
                ]
            }
        }
    )
