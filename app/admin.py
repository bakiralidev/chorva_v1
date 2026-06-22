from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy.future import select
from sqlalchemy import or_, and_
import uuid

from app.config import settings
from app.database import async_session_local
from app.models.user import User
from app.models.category import Category
from app.models.region import Region
from app.models.advertisement import Advertisement
from app.models.image import Image
from app.auth.security import verify_password

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
    name = "Foydalanuvchi"
    name_plural = "Foydalanuvchilar"
    column_list = ["id", "email", "phone_number", "is_active", "is_superuser", "created_at"]
    column_searchable_list = ["email", "phone_number"]
    column_sortable_list = ["created_at"]
    form_columns = ["email", "phone_number", "is_active", "is_superuser"]

class CategoryAdmin(ModelView, model=Category):
    name = "Kategoriya"
    name_plural = "Kategoriyalar"
    column_list = ["id", "name", "slug"]
    column_searchable_list = ["name", "slug"]
    form_columns = ["name", "slug", "icon_url"]

class RegionAdmin(ModelView, model=Region):
    name = "Hudud"
    name_plural = "Hududlar"
    column_list = ["id", "name"]
    column_searchable_list = ["name"]
    form_columns = ["name"]

from sqladmin.filters import BooleanFilter, StaticValuesFilter, ForeignKeyFilter

class AdvertisementAdmin(ModelView, model=Advertisement):
    name = "E'lon"
    name_plural = "E'lonlar"
    column_list = ["id", "title", "price", "status", "views_count", "created_at"]
    column_searchable_list = ["title", "description"]
    column_filters = [
        StaticValuesFilter(column=Advertisement.status, values=[("active", "Faol"), ("sold", "Sotilgan"), ("inactive", "Faol emas")], title="Holati"),
        BooleanFilter(column=Advertisement.is_top, title="Top e'lon"),
        ForeignKeyFilter(foreign_key=Advertisement.category_id, foreign_display_field=Category.name, title="Kategoriya"),
        ForeignKeyFilter(foreign_key=Advertisement.region_id, foreign_display_field=Region.name, title="Hudud")
    ]
    form_columns = [
        "user_id", "category_id", "region_id",
        "title", "description", "price",
        "is_negotiable", "age", "weight",
        "color", "quantity", "contact_phone",
        "status", "is_top"
    ]

class ImageAdmin(ModelView, model=Image):
    name = "Rasm"
    name_plural = "Rasmlar"
    column_list = ["id", "advertisement_id", "image_url", "is_main"]
    form_columns = ["advertisement_id", "image_url", "is_main"]

