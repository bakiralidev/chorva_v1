from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Livestock Trading Platform MVP"
    SECRET_KEY: str = "super-secret-key-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "sqlite+aiosqlite:///./chorva.db"

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
