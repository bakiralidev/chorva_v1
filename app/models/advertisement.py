import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Text, Numeric, Boolean, Integer, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class AdStatus(str, enum.Enum):
    active = "active"
    sold = "sold"
    inactive = "inactive"

class Advertisement(Base):
    __tablename__ = "advertisements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id", ondelete="RESTRICT"))
    
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    is_negotiable: Mapped[bool] = mapped_column(Boolean, default=False)
    
    age: Mapped[str | None] = mapped_column(String(100), nullable=True)
    weight: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    
    contact_phone: Mapped[str] = mapped_column(String(50))
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    is_top: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[AdStatus] = mapped_column(Enum(AdStatus), default=AdStatus.active)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="advertisements")
    category: Mapped["Category"] = relationship("Category", back_populates="advertisements")
    region: Mapped["Region"] = relationship("Region", back_populates="advertisements")
    images: Mapped[list["Image"]] = relationship("Image", back_populates="advertisement", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return self.title
