from pydantic import BaseModel, ConfigDict

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjNlNDU2Ny1lODliLTEyZDMtYTQ1Ni00MjY2MTQxNzQwMDAifQ...",
                "refresh_token": "X-3t9x9m9j1t2h3m...",
                "token_type": "bearer"
            }
        }
    )

class TokenData(BaseModel):
    user_id: str | None = None

class TokenRefreshRequest(BaseModel):
    refresh_token: str
