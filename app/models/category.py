from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    translations: Mapped[list["CategoryTranslation"]] = relationship(
        "CategoryTranslation",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    advertisements: Mapped[list["Advertisement"]] = relationship("Advertisement", back_populates="category")

    def get_translation_field(self, lang: str, field: str) -> str:
        for t in self.translations:
            if t.language == lang:
                return getattr(t, field, "") or ""
        return ""

    def set_translation_field(self, lang: str, field: str, value: str) -> None:
        for t in self.translations:
            if t.language == lang:
                setattr(t, field, value)
                return
        # If not found, create new translation
        new_t = CategoryTranslation(language=lang)
        setattr(new_t, field, value)
        self.translations.append(new_t)

    def translate(self, lang: str, fields: list[str], default_lang: str = "uz") -> dict:
        trans = None
        for t in self.translations:
            if t.language == lang:
                trans = t
                break
        
        # Fallback 1: Default language (uz)
        if not trans and lang != default_lang:
            for t in self.translations:
                if t.language == default_lang:
                    trans = t
                    break
                    
        # Fallback 2: First available translation
        if not trans and self.translations:
            trans = self.translations[0]

        res = {}
        for f in fields:
            res[f] = getattr(trans, f, "") if trans else ""
        return res

    def to_response(self, lang: str) -> dict:
        translated = self.translate(lang, ["name", "slug"])
        return {
            "id": self.id,
            "name": translated["name"] or "",
            "slug": translated["slug"] or "",
            "icon_url": self.icon_url,
        }

    # Python properties for backward compatibility and fallback
    @property
    def name(self) -> str: return self.name_uz
    @name.setter
    def name(self, val: str) -> None: self.name_uz = val

    @property
    def slug(self) -> str: return self.slug_uz
    @slug.setter
    def slug(self, val: str) -> None: self.slug_uz = val

    # Python properties for SQLAdmin WTForms integrations
    @property
    def name_uz(self) -> str: return self.get_translation_field("uz", "name")
    @name_uz.setter
    def name_uz(self, val: str) -> None: self.set_translation_field("uz", "name", val)

    @property
    def slug_uz(self) -> str: return self.get_translation_field("uz", "slug")
    @slug_uz.setter
    def slug_uz(self, val: str) -> None: self.set_translation_field("uz", "slug", val)

    @property
    def name_ru(self) -> str: return self.get_translation_field("ru", "name")
    @name_ru.setter
    def name_ru(self, val: str) -> None: self.set_translation_field("ru", "name", val)

    @property
    def slug_ru(self) -> str: return self.get_translation_field("ru", "slug")
    @slug_ru.setter
    def slug_ru(self, val: str) -> None: self.set_translation_field("ru", "slug", val)

    @property
    def name_en(self) -> str: return self.get_translation_field("en", "name")
    @name_en.setter
    def name_en(self, val: str) -> None: self.set_translation_field("en", "name", val)

    @property
    def slug_en(self) -> str: return self.get_translation_field("en", "slug")
    @slug_en.setter
    def slug_en(self, val: str) -> None: self.set_translation_field("en", "slug", val)

    @property
    def name_tr(self) -> str: return self.get_translation_field("tr", "name")
    @name_tr.setter
    def name_tr(self, val: str) -> None: self.set_translation_field("tr", "name", val)

    @property
    def slug_tr(self) -> str: return self.get_translation_field("tr", "slug")
    @slug_tr.setter
    def slug_tr(self, val: str) -> None: self.set_translation_field("tr", "slug", val)

    def __str__(self) -> str:
        # Fallback for display representation
        return self.name_uz or self.name_ru or f"Category #{self.id}"


class CategoryTranslation(Base):
    __tablename__ = "category_translations"
    __table_args__ = (
        UniqueConstraint("category_id", "language", name="uq_category_lang"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    category: Mapped[Category] = relationship(Category, back_populates="translations")
