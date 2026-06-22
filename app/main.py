from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin

from app.config import settings
from app.database import engine
from app.routers import auth_router, directories_router, ads_router
from app.admin import (
    admin_auth_backend, 
    UserAdmin, 
    CategoryAdmin, 
    RegionAdmin, 
    AdvertisementAdmin, 
    ImageAdmin
)

# SQLAdmin and WTForms 3.2+ compatibility monkey patch
from sqladmin.widgets import BooleanInputWidget
BooleanInputWidget.validation_attrs = ["required", "disabled"]

# FastAPI application initialization
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Chorva mollari savdosi uchun onlayn platforma backend MVP API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS sozlamalari (alohida frontend jamoasi ulanishi uchun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ishlab chiqarishda buni faqat frontend manziliga cheklash kerak
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routerlarni ulash
app.include_router(auth_router, prefix="/api/v1")
app.include_router(directories_router, prefix="/api/v1")
app.include_router(ads_router, prefix="/api/v1")

# SQLAdmin panelini ulash
admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=admin_auth_backend,
    title="Chorva.uz Admin",
    base_url="/admin"
)

# Admin ko'rinishlarini ro'yxatdan o'tkazish
admin.add_view(UserAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(RegionAdmin)
admin.add_view(AdvertisementAdmin)
admin.add_view(ImageAdmin)

@app.get("/")
async def root():
    return {
        "message": "Chorva.uz backend MVP API ishlamoqda!",
        "api_docs": "/docs",
        "admin_dashboard": "/admin"
    }
