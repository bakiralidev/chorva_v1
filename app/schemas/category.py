from pydantic import BaseModel, ConfigDict

class CategoryBase(BaseModel):
    name: str
    slug: str
    icon_url: str | None = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Qoramol",
                "slug": "qoramol",
                "icon_url": "/uploads/categories/cattle.png"
            }
        }
    )
