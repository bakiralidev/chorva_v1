from pydantic import BaseModel

class FavoriteToggleResponse(BaseModel):
    message: str
    status: str
