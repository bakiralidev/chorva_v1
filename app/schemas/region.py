from pydantic import BaseModel, ConfigDict

class RegionBase(BaseModel):
    name: str

class RegionResponse(RegionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
