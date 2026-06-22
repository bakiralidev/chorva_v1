import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.advertisement import AdStatus
from app.schemas.user import UserResponse
from app.schemas.category import CategoryResponse
from app.schemas.region import RegionResponse

class AdImageCreate(BaseModel):
    image_url: str
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
    quantity: int = Field(default=1, ge=1)
    contact_phone: str = Field(..., min_length=7, max_length=50)

class AdvertisementCreate(AdvertisementBase):
    category_id: int
    region_id: int
    images: list[AdImageCreate] | None = Field(default=None, description="E'lon rasmlari ro'yxati")

class AdvertisementResponse(AdvertisementBase):
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: int
    region_id: int
    views_count: int
    is_top: bool
    status: AdStatus
    created_at: datetime
    images: list[AdImageResponse] = []

    model_config = ConfigDict(from_attributes=True)

class AdvertisementDetailResponse(AdvertisementBase):
    id: uuid.UUID
    user: UserResponse
    category: CategoryResponse
    region: RegionResponse
    views_count: int
    is_top: bool
    status: AdStatus
    created_at: datetime
    images: list[AdImageResponse] = []

    model_config = ConfigDict(from_attributes=True)
