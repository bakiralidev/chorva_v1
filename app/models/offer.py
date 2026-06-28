from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func, UniqueConstraint, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    has_file: Mapped[bool] = mapped_column(Boolean, default=False)
    file_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    translations: Mapped[list["OfferTranslation"]] = relationship(
        "OfferTranslation",
        back_populates="offer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

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
        new_t = OfferTranslation(language=lang)
        setattr(new_t, field, value)
        self.translations.append(new_t)

    def translate(self, lang: str, fields: list[str], default_lang: str = "uz") -> dict:
        trans = None
        for t in self.translations:
            if t.language == lang:
                trans = t
                break
        
        if not trans and lang != default_lang:
            for t in self.translations:
                if t.language == default_lang:
                    trans = t
                    break
                    
        if not trans and self.translations:
            trans = self.translations[0]

        res = {}
        for f in fields:
            res[f] = getattr(trans, f, "") if trans else ""
        return res

    def to_response(self, lang: str) -> dict:
        translated = self.translate(lang, ["title", "content"])
        return {
            "id": self.id,
            "title": translated["title"] or "",
            "content": translated["content"] or "",
            "has_file": self.has_file,
            "file_url": self.file_url,
            "is_active": self.is_active,
            "created_at": self.created_at
        }

    @property
    def title_uz(self) -> str: return self.get_translation_field("uz", "title")
    @title_uz.setter
    def title_uz(self, val: str) -> None: self.set_translation_field("uz", "title", val)

    @property
    def content_uz(self) -> str: return self.get_translation_field("uz", "content")
    @content_uz.setter
    def content_uz(self, val: str) -> None: self.set_translation_field("uz", "content", val)

    @property
    def title_ru(self) -> str: return self.get_translation_field("ru", "title")
    @title_ru.setter
    def title_ru(self, val: str) -> None: self.set_translation_field("ru", "title", val)

    @property
    def content_ru(self) -> str: return self.get_translation_field("ru", "content")
    @content_ru.setter
    def content_ru(self, val: str) -> None: self.set_translation_field("ru", "content", val)

    @property
    def title_en(self) -> str: return self.get_translation_field("en", "title")
    @title_en.setter
    def title_en(self, val: str) -> None: self.set_translation_field("en", "title", val)

    @property
    def content_en(self) -> str: return self.get_translation_field("en", "content")
    @content_en.setter
    def content_en(self, val: str) -> None: self.set_translation_field("en", "content", val)
    
    @property
    def title_tr(self) -> str: return self.get_translation_field("tr", "title")
    @title_tr.setter
    def title_tr(self, val: str) -> None: self.set_translation_field("tr", "title", val)

    @property
    def content_tr(self) -> str: return self.get_translation_field("tr", "content")
    @content_tr.setter
    def content_tr(self, val: str) -> None: self.set_translation_field("tr", "content", val)

    def __str__(self) -> str:
        return self.title_uz or self.title_ru or f"Offer #{self.id}"


class OfferTranslation(Base):
    __tablename__ = "offer_translations"
    __table_args__ = (
        UniqueConstraint("offer_id", "language", name="uq_offer_lang"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    offer: Mapped[Offer] = relationship(Offer, back_populates="translations")
