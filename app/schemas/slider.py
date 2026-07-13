from pydantic import BaseModel, ConfigDict

class SliderResponse(BaseModel):
    id: int
    image_url: str
    link: str | None = None

    model_config = ConfigDict(from_attributes=True)
