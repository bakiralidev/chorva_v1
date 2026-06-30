from app.routers.mobile.auth import router as auth_router
from app.routers.mobile.directories import router as directories_router
from app.routers.mobile.ads import router as ads_router
from app.routers.mobile.favorites import router as favorites_router
from app.routers.mobile.offers import router as offers_router

__all__ = ["auth_router", "directories_router", "ads_router", "favorites_router", "offers_router"]
