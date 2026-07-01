from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy.future import select
from sqlalchemy import or_, and_
import uuid
import os
import shutil
from wtforms import FileField
from markupsafe import Markup

from app.config import settings
from app.database import async_session_local
from app.models.user import User
from app.models.category import Category, CategoryTranslation
from app.models.region import Region, RegionTranslation
from app.models.advertisement import Advertisement
from app.models.image import Image
from app.models.offer import Offer
from app.models.verification import VerificationCode
from app.auth.security import verify_password
from app.utils.lang import admin_lang
from app.utils.admin_i18n import get_admin_t

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        """
        Admin panelga kirish logikasi. Faqat is_superuser bo'lgan foydalanuvchilarga ruxsat beriladi.
        """
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return False

        async with async_session_local() as session:
            # Email yoki telefon orqali superuserni qidiramiz
            query = select(User).where(
                and_(
                    or_(User.email == username, User.phone_number == username),
                    User.is_superuser == True
                )
            )
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user and verify_password(password, user.hashed_password):
                # Sessiyaga foydalanuvchi ID sini token sifatida yozamiz
                request.session.update({"token": str(user.id)})
                return True
                
        return False

    async def logout(self, request: Request) -> bool:
        """
        Tizimdan (sessiyadan) chiqish.
        """
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """
        Har bir admin so'rovini autentifikatsiya qilish.
        """
        token = request.session.get("token")
        if not token:
            return False
        
        try:
            user_id = uuid.UUID(token)
        except ValueError:
            return False

        async with async_session_local() as session:
            query = select(User).where(
                and_(
                    User.id == user_id, 
                    User.is_superuser == True,
                    User.is_active == True
                )
            )
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            if user:
                return True
                
        return False

# Admin autentifikatsiya obyekti
admin_auth_backend = AdminAuth(secret_key=settings.SECRET_KEY)

# SQLAdmin uchun modellar ko'rinishi (Model Views)
class UserAdmin(ModelView, model=User):
    column_list = ["id", "email", "phone_number", "is_active", "accepted_offer", "is_superuser", "created_at"]
    column_searchable_list = ["email", "phone_number"]
    column_sortable_list = ["created_at"]
    form_columns = ["email", "phone_number", "is_active", "accepted_offer", "is_superuser"]

    @property
    def name(self) -> str:
        return get_admin_t(admin_lang.get()).get("user", "User")

    @property
    def name_plural(self) -> str:
        return get_admin_t(admin_lang.get()).get("users", "Users")

    @property
    def _column_labels(self) -> dict:
        t = get_admin_t(admin_lang.get())
        return {
            "id": t["col_id"],
            "email": t["col_email"],
            "phone_number": t["col_phone"],
            "is_active": t["col_is_active"],
            "accepted_offer": t["col_accepted_offer"],
            "is_superuser": t["col_is_superuser"],
            "created_at": t["col_created_at"],
        }
    
    @_column_labels.setter
    def _column_labels(self, value):
        pass

    @property
    def column_filters(self):
        t = get_admin_t(admin_lang.get())
        return [
            BooleanFilter(column=User.accepted_offer, title=t["filter_accepted_offer"]),
            BooleanFilter(column=User.is_active, title=t["col_is_active"]),
            BooleanFilter(column=User.is_superuser, title=t["col_is_superuser"]),
        ]

from wtforms import Form, StringField, TextAreaField, BooleanField

class OfferForm(Form):
    has_file = BooleanField("Fayl biriktirish (Tanlansa, sarlavha va matnlar majburiy emas)")
    file_url = FileField("Fayl (PDF, DOC, va hkz.)")
    title_uz = StringField("Sarlavha (UZ)")
    content_uz = TextAreaField("Matn (UZ)")
    title_ru = StringField("Sarlavha (RU)")
    content_ru = TextAreaField("Matn (RU)")
    title_en = StringField("Sarlavha (EN)")
    content_en = TextAreaField("Matn (EN)")
    title_tr = StringField("Sarlavha (TR)")
    content_tr = TextAreaField("Matn (TR)")
    is_active = BooleanField("Faol")


class CategoryForm(Form):
    icon_url = FileField("Icon File")
    name_uz = StringField("Kategoriya Nomi (UZ)")
    slug_uz = StringField("Slug (UZ)")
    name_ru = StringField("Kategoriya Nomi (RU)")
    slug_ru = StringField("Slug (RU)")
    name_en = StringField("Kategoriya Nomi (EN)")
    slug_en = StringField("Slug (EN)")
    name_tr = StringField("Kategoriya Nomi (TR)")
    slug_tr = StringField("Slug (TR)")

class RegionForm(Form):
    name_uz = StringField("Hudud Nomi (UZ)")
    name_ru = StringField("Hudud Nomi (RU)")
    name_en = StringField("Hudud Nomi (EN)")
    name_tr = StringField("Hudud Nomi (TR)")

class CategoryAdmin(ModelView, model=Category):
    column_list = ["id", "name", "slug", "icon_url"]
    form = CategoryForm

    @property
    def name(self) -> str:
        return get_admin_t(admin_lang.get()).get("category", "Category")

    @property
    def name_plural(self) -> str:
        return get_admin_t(admin_lang.get()).get("categories", "Categories")

    @property
    def _column_labels(self) -> dict:
        t = get_admin_t(admin_lang.get())
        return {
            "id": t["col_id"],
            "name": t["col_name"],
            "slug": t["col_slug"],
            "icon_url": t["col_icon"],
        }

    @_column_labels.setter
    def _column_labels(self, value):
        pass

    column_formatters = {
        "name": lambda m, a: m.get_translation_field(admin_lang.get(), "name") or m.name_uz or m.name_ru or f"Category #{m.id}",
        "slug": lambda m, a: m.get_translation_field(admin_lang.get(), "slug") or m.slug_uz or "",
        "icon_url": lambda m, a: Markup(f'<img src="{m.icon_url}" width="30" height="30" style="border-radius: 50%; object-fit: cover;" />') if m.icon_url else ""
    }

    async def on_model_change(self, data: dict, model: Category, is_created: bool, request: Request) -> None:
        # Extract translations and pop from data to avoid SQLAdmin attribute errors
        langs = ["uz", "ru", "en", "tr"]
        for lang in langs:
            name_key = f"name_{lang}"
            slug_key = f"slug_{lang}"
            if name_key in data:
                model.set_translation_field(lang, "name", data.pop(name_key))
            if slug_key in data:
                model.set_translation_field(lang, "slug", data.pop(slug_key))

        # Handle file upload for icon_url
        file_data = data.get("icon_url")
        if file_data and hasattr(file_data, "filename") and file_data.filename:
            ext = os.path.splitext(file_data.filename)[1]
            unique_filename = f"{uuid.uuid4()}{ext}"
            
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file_data.file, buffer)
            
            model.icon_url = f"/uploads/{unique_filename}"
            data["icon_url"] = f"/uploads/{unique_filename}"
        else:
            if not is_created:
                if "icon_url" in data:
                    del data["icon_url"]
            else:
                model.icon_url = ""
                data["icon_url"] = ""

    async def on_model_delete(self, model: Category, request: Request) -> None:
        if model.icon_url and model.icon_url.startswith("/uploads/"):
            filename = model.icon_url.replace("/uploads/", "")
            file_path = os.path.join("uploads", filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

class RegionAdmin(ModelView, model=Region):
    column_list = ["id", "name"]
    form = RegionForm

    @property
    def name(self) -> str:
        return get_admin_t(admin_lang.get()).get("region", "Region")

    @property
    def name_plural(self) -> str:
        return get_admin_t(admin_lang.get()).get("regions", "Regions")

    @property
    def _column_labels(self) -> dict:
        t = get_admin_t(admin_lang.get())
        return {
            "id": t["col_id"],
            "name": t["col_name"],
        }

    @_column_labels.setter
    def _column_labels(self, value):
        pass

    column_formatters = {
        "name": lambda m, a: m.get_translation_field(admin_lang.get(), "name") or m.name_uz or m.name_ru or f"Region #{m.id}",
    }

    async def on_model_change(self, data: dict, model: Region, is_created: bool, request: Request) -> None:
        langs = ["uz", "ru", "en", "tr"]
        for lang in langs:
            name_key = f"name_{lang}"
            if name_key in data:
                model.set_translation_field(lang, "name", data.pop(name_key))

from typing import Any, Optional, List, Tuple, Callable
from sqlalchemy.sql.expression import Select
from sqladmin.filters import BooleanFilter, StaticValuesFilter, ForeignKeyFilter

class TranslatedForeignKeyFilter(ForeignKeyFilter):
    def __init__(
        self,
        foreign_key: Any,
        translation_model: Any,
        fk_field_name: str,
        display_field_name: str,
        title: Optional[str] = None,
        parameter_name: Optional[str] = None,
    ):
        super().__init__(
            foreign_key=foreign_key,
            foreign_display_field=getattr(translation_model, display_field_name),
            foreign_model=translation_model,
            title=title,
            parameter_name=parameter_name,
        )
        self.fk_field_name = fk_field_name
        self.display_field_name = display_field_name

    async def lookups(
        self,
        request: Request,
        model: Any,
        run_query: Callable[[Select], Any],
    ) -> List[Tuple[str, str]]:
        fk_column = getattr(self.foreign_model, self.fk_field_name)
        display_column = getattr(self.foreign_model, self.display_field_name)
        
        # Read admin language cookie (default is 'uz')
        lang = request.cookies.get("admin_lang", "uz")
        if lang not in ["uz", "ru", "en", "tr"]:
            lang = "uz"
            
        query = select(fk_column, display_column).where(self.foreign_model.language == lang).distinct()
        results = await run_query(query)
        
        return [("", "All")] + [
            (str(key), str(value))
            for key, value in results
        ]

class AdvertisementAdmin(ModelView, model=Advertisement):
    column_list = ["id", "title", "price", "status", "views_count", "created_at"]
    column_searchable_list = ["title", "description"]

    @property
    def name(self) -> str:
        return get_admin_t(admin_lang.get()).get("advertisement", "Advertisement")

    @property
    def name_plural(self) -> str:
        return get_admin_t(admin_lang.get()).get("advertisements", "Advertisements")

    @property
    def _column_labels(self) -> dict:
        t = get_admin_t(admin_lang.get())
        return {
            "id": t["col_id"],
            "title": t["col_title"],
            "price": t["col_price"],
            "status": t["col_status"],
            "views_count": t["col_views"],
            "created_at": t["col_created_at"],
            "is_top": t["col_is_top"],
        }

    @_column_labels.setter
    def _column_labels(self, value):
        pass

    @property
    def column_filters(self):
        t = get_admin_t(admin_lang.get())
        return [
            StaticValuesFilter(
                column=Advertisement.status,
                values=[
                    ("active", t["filter_active"]),
                    ("sold", t["filter_sold"]),
                    ("inactive", t["filter_inactive"])
                ],
                title=t["filter_status"]
            ),
            BooleanFilter(column=Advertisement.is_top, title=t["filter_is_top"]),
            TranslatedForeignKeyFilter(
                foreign_key=Advertisement.category_id,
                translation_model=CategoryTranslation,
                fk_field_name="category_id",
                display_field_name="name",
                title=t["filter_category"]
            ),
            TranslatedForeignKeyFilter(
                foreign_key=Advertisement.region_id,
                translation_model=RegionTranslation,
                fk_field_name="region_id",
                display_field_name="name",
                title=t["filter_region"]
            )
        ]

    form_columns = [
        "user", "category", "region",
        "title", "description", "price",
        "is_negotiable", "age", "weight",
        "color", "quantity", "contact_phone",
        "status", "is_top"
    ]

    async def on_model_change(self, data: dict, model: Advertisement, is_created: bool, request: Request) -> None:
        missing_fields = [
            field_name
            for field_name in ("user", "category", "region")
            if not data.get(field_name) and not getattr(model, field_name, None)
        ]
        if missing_fields:
            raise ValueError("E'lon uchun foydalanuvchi, kategoriya va hudud majburiy.")

class ImageAdmin(ModelView, model=Image):
    column_list = ["id", "advertisement_id", "image_url", "is_main"]
    form_columns = ["advertisement", "image_url", "is_main"]

    @property
    def name(self) -> str:
        return get_admin_t(admin_lang.get()).get("image", "Image")

    @property
    def name_plural(self) -> str:
        return get_admin_t(admin_lang.get()).get("images", "Images")

    @property
    def _column_labels(self) -> dict:
        t = get_admin_t(admin_lang.get())
        return {
            "id": t["col_id"],
            "advertisement_id": t["col_ad_id"],
            "image_url": t["col_image_url"],
            "is_main": t["col_is_main"],
        }

    @_column_labels.setter
    def _column_labels(self, value):
        pass
    
    form_overrides = {
        "image_url": FileField,
    }

    form_args = {
        "image_url": {
            "label": "Rasm fayli (Yangi rasmni tanlang)"
        }
    }

    column_formatters = {
        "image_url": lambda m, a: Markup(f'<img src="{m.image_url}" width="80" style="border-radius: 5px; max-height: 80px; object-fit: cover;" />') if m.image_url else ""
    }

    async def on_model_change(self, data: dict, model: Image, is_created: bool, request: Request) -> None:
        file_data = data.get("image_url")
        if file_data and hasattr(file_data, "filename") and file_data.filename:
            ext = os.path.splitext(file_data.filename)[1]
            unique_filename = f"{uuid.uuid4()}{ext}"
            
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file_data.file, buffer)
            
            data["image_url"] = f"/uploads/{unique_filename}"
        else:
            if not is_created:
                if "image_url" in data:
                    del data["image_url"]
            else:
                data["image_url"] = ""

    async def on_model_delete(self, model: Image, request: Request) -> None:
        if model.image_url and model.image_url.startswith("/uploads/"):
            filename = model.image_url.replace("/uploads/", "")
            file_path = os.path.join("uploads", filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

class OfferAdmin(ModelView, model=Offer):
    column_list = ["id", "title_uz", "has_file", "file_url", "is_active", "created_at"]
    form = OfferForm
    can_delete = False

    form_overrides = {
        "file_url": FileField,
    }

    column_formatters = {
        "file_url": lambda m, a: Markup(f'<a href="{m.file_url}" target="_blank" class="btn btn-sm btn-outline-info">Faylni ko\'rish</a>') if m.file_url else ""
    }
    
    @property
    def name(self) -> str:
        t = get_admin_t(admin_lang.get())
        return "Oferta"

    @property
    def name_plural(self) -> str:
        t = get_admin_t(admin_lang.get())
        return "Oferta (Foydalanish shartlari)"
        
    @property
    def _column_labels(self) -> dict:
        t = get_admin_t(admin_lang.get())
        return {
            "id": "ID",
            "title_uz": "Sarlavha (UZ)",
            "title_ru": "Sarlavha (RU)",
            "title_en": "Sarlavha (EN)",
            "title_tr": "Sarlavha (TR)",
            "content_uz": "Matn (UZ)",
            "content_ru": "Matn (RU)",
            "content_en": "Matn (EN)",
            "content_tr": "Matn (TR)",
            "has_file": "Faylli oferta",
            "file_url": "Fayl",
            "is_active": "Faol",
            "created_at": "Yaratilgan vaqt"
        }

    @_column_labels.setter
    def _column_labels(self, value):
        pass

    from sqladmin import action
    @action(
        name="faol_bilan_almashtirish",
        label="Faol bilan almashtirish",
        confirmation_message="Ushbu ofertani faol qilib, qolganlarini nofaol qilmoqchimisiz?"
    )
    async def make_active(self, request: Request):
        pks = request.query_params.get("pks", "").split(",")
        if pks:
            pk = int(pks[0])
            async with async_session_local() as session:
                from sqlalchemy import update
                await session.execute(update(Offer).values(is_active=False))
                await session.execute(update(Offer).where(Offer.id == pk).values(is_active=True))
                await session.commit()
        from starlette.responses import RedirectResponse
        referer = request.headers.get("Referer")
        if referer:
            return RedirectResponse(referer)
        return RedirectResponse(request.url_for("admin:list", identity=self.identity))

    async def on_model_change(self, data: dict, model: Offer, is_created: bool, request: Request) -> None:
        has_file = data.get("has_file", False)
        file_data = data.get("file_url")
        has_new_file = file_data and hasattr(file_data, "filename") and file_data.filename
        has_existing_file = not is_created and model.file_url

        if has_file:
            if not has_new_file and not has_existing_file:
                raise ValueError("Fayl biriktirish tanlandi, lekin fayl yuklanmadi!")
            
            if has_new_file:
                if model.file_url and model.file_url.startswith("/uploads/"):
                    old_path = os.path.join("uploads", model.file_url.replace("/uploads/", ""))
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception:
                            pass

                ext = os.path.splitext(file_data.filename)[1]
                unique_filename = f"{uuid.uuid4()}{ext}"
                upload_dir = "uploads"
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, unique_filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file_data.file, buffer)
                data["file_url"] = f"/uploads/{unique_filename}"
            else:
                if "file_url" in data:
                    del data["file_url"]

            langs = ["uz", "ru", "en", "tr"]
            for lang in langs:
                title_key = f"title_{lang}"
                content_key = f"content_{lang}"
                data.pop(title_key, None)
                data.pop(content_key, None)
                model.set_translation_field(lang, "title", "")
                model.set_translation_field(lang, "content", "")
        else:
            title_uz = data.get("title_uz", "").strip()
            content_uz = data.get("content_uz", "").strip()
            if not title_uz or not content_uz:
                raise ValueError("Agar fayl biriktirilmasa, sarlavha (UZ) va matn (UZ) kiritilishi shart!")

            if model.file_url and model.file_url.startswith("/uploads/"):
                old_path = os.path.join("uploads", model.file_url.replace("/uploads/", ""))
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass
            
            data["file_url"] = None

            langs = ["uz", "ru", "en", "tr"]
            for lang in langs:
                title_key = f"title_{lang}"
                content_key = f"content_{lang}"
                if title_key in data:
                    model.set_translation_field(lang, "title", data.pop(title_key) or "")
                if content_key in data:
                    model.set_translation_field(lang, "content", data.pop(content_key) or "")

    async def on_model_delete(self, model: Offer, request: Request) -> None:
        if model.file_url and model.file_url.startswith("/uploads/"):
            filename = model.file_url.replace("/uploads/", "")
            file_path = os.path.join("uploads", filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

class VerificationCodeAdmin(ModelView, model=VerificationCode):
    column_list = ["id", "user_id", "code", "expires_at", "created_at"]
    can_create = False
    can_edit = False
    
    @property
    def name(self) -> str:
        return "Tasdiqlash kodi"

    @property
    def name_plural(self) -> str:
        return "Tasdiqlash kodlari"

