from pydantic import BaseModel, ConfigDict

class CategoryBase(BaseModel):
    name: str
    slug: str
    icon_url: str | None = None

class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
