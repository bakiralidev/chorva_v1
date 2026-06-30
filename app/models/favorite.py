import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    advertisement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("advertisements.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    advertisement: Mapped["Advertisement"] = relationship("Advertisement")

    def __str__(self) -> str:
        return f"Favorite(user={self.user_id}, ad={self.advertisement_id})"
