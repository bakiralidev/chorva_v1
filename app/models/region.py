from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))

    # Relationships
    advertisements: Mapped[list["Advertisement"]] = relationship("Advertisement", back_populates="region")

    def __str__(self) -> str:
        return self.name
