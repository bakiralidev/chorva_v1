from fastapi import FastAPI
from app.routers.front.auth import router as front_auth_router
from app.routers.front.directories import router as front_directories_router
from app.routers.front.ads import router as front_ads_router
from app.routers.front.offers import router as front_offers_router
from app.routers.front.favorites import router as front_favorites_router
from app.routers.front.sliders import router as front_sliders_router
from app.routers.mobile.auth import router as mobile_auth_router
from app.routers.mobile.directories import router as mobile_directories_router
from app.routers.mobile.ads import router as mobile_ads_router
from app.routers.mobile.offers import router as mobile_offers_router
from app.routers.mobile.favorites import router as mobile_favorites_router
from app.routers.mobile.sliders import router as mobile_sliders_router
from app.routers.admin import router as admin_router

# Vebsayt uchun ochiq API sub-ilovasi
front_app = FastAPI(
    title="Chorva.uz Front API",
    description="Vebsayt uchun ochiq API",
    version="1.0.0",
    docs_url="/front-docs",
    redoc_url="/redoc",
    openapi_url="/front-openapi.json"
)

# Mobil ilovalar uchun ochiq API sub-ilovasi
mobile_app = FastAPI(
    title="Chorva.uz Mobile API",
    description="Mobil ilovalar uchun ochiq API",
    version="1.0.0",
    docs_url="/mobile-docs",
    redoc_url="/redoc",
    openapi_url="/mobile-openapi.json"
)

# Administratorlar uchun maxsus boshqaruv REST API sub-ilovasi
admin_app = FastAPI(
    title="Chorva.uz Admin REST API",
    description="Administratorlar uchun maxsus boshqaruv API",
    version="1.0.0",
    docs_url="/admin-docs",
    redoc_url="/redoc",
    openapi_url="/admin-openapi.json"
)

# Routerlarni tegishli sub-ilovalarga ulash
front_app.include_router(front_auth_router)
front_app.include_router(front_directories_router)
front_app.include_router(front_ads_router)
front_app.include_router(front_offers_router)
front_app.include_router(front_favorites_router)
front_app.include_router(front_sliders_router)

mobile_app.include_router(mobile_auth_router)
mobile_app.include_router(mobile_directories_router)
mobile_app.include_router(mobile_ads_router)
mobile_app.include_router(mobile_offers_router)
mobile_app.include_router(mobile_favorites_router)
mobile_app.include_router(mobile_sliders_router)

admin_app.include_router(admin_router)

__all__ = ["front_app", "mobile_app", "admin_app"]


