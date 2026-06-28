from fastapi import APIRouter
from app.routers.admin.users import router as users_router
from app.routers.admin.ads import router as ads_router
from app.routers.admin.categories import router as categories_router
from app.routers.admin.regions import router as regions_router

router = APIRouter()
router.include_router(users_router)
router.include_router(ads_router)
router.include_router(categories_router)
router.include_router(regions_router)
