from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    advertisements: Mapped[list["Advertisement"]] = relationship("Advertisement", back_populates="category")

    def __str__(self) -> str:
        return self.name
