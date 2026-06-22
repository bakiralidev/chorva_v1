import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    advertisement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("advertisements.id", ondelete="CASCADE"))
    image_url: Mapped[str] = mapped_column(String(500))
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    advertisement: Mapped["Advertisement"] = relationship("Advertisement", back_populates="images")

    def __str__(self) -> str:
        return self.image_url
