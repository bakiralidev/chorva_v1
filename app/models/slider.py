from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Slider(Base):
    __tablename__ = "sliders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    image_url: Mapped[str] = mapped_column(String(500))
    link: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __str__(self) -> str:
        return self.image_url
