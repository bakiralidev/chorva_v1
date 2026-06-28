from pydantic import BaseModel, ConfigDict

class RegionBase(BaseModel):
    name: str

class RegionCreate(RegionBase):
    pass

class RegionResponse(RegionBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Toshkent viloyati"
            }
        }
    )
