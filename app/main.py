import os
import logging
import time
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.database import engine
from fastapi.responses import RedirectResponse
from app.routers import front_app, mobile_app, admin_app
from app.utils.lang import admin_lang
from app.utils.admin_i18n import get_admin_t
from app.logging_config import setup_logging

setup_logging()

logger = logging.getLogger("app")
request_logger = logging.getLogger("app.requests")

class AdminLangMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        lang = request.cookies.get("admin_lang", "uz")
        if lang not in ["uz", "ru", "en", "tr"]:
            lang = "uz"
        
        token = admin_lang.set(lang)
        try:
            response = await call_next(request)
            return response
        finally:
            admin_lang.reset(token)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, log_responses: bool = True):
        super().__init__(app)
        self.log_responses = log_responses

    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", None)
        if not request_id:
            request_id = request.headers.get("x-request-id", uuid.uuid4().hex)
            request.state.request_id = request_id

        started_at = time.perf_counter()
        client_host = request.client.host if request.client else "-"

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.exception(
                "Unhandled request error request_id=%s method=%s path=%s client=%s duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                client_host,
                duration_ms,
            )
            raise

        if not self.log_responses:
            return response

        duration_ms = (time.perf_counter() - started_at) * 1000
        log_method = request_logger.warning if response.status_code >= 400 else request_logger.info
        log_method(
            "request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f client=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            client_host,
        )
        response.headers["X-Request-ID"] = request_id
        return response


from app.admin import (
    admin_auth_backend, 
    UserAdmin, 
    CategoryAdmin, 
    RegionAdmin, 
    AdvertisementAdmin, 
    ImageAdmin,
    OfferAdmin,
    VerificationCodeAdmin
)

# SQLAdmin and WTForms 3.2+ compatibility monkey patch
try:
    from sqladmin.widgets import BooleanInputWidget
    BooleanInputWidget.validation_attrs = ["required", "disabled"]
except ImportError:
    # SQLAdmin v0.20+ or newer does not require or have this widget
    pass

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

app.add_middleware(AdminLangMiddleware)
app.add_middleware(RequestLoggingMiddleware)
front_app.add_middleware(RequestLoggingMiddleware, log_responses=False)
mobile_app.add_middleware(RequestLoggingMiddleware, log_responses=False)
admin_app.add_middleware(RequestLoggingMiddleware, log_responses=False)


@app.on_event("startup")
async def log_startup() -> None:
    logger.info("Application startup: %s", settings.PROJECT_NAME)


@app.on_event("shutdown")
async def log_shutdown() -> None:
    logger.info("Application shutdown: %s", settings.PROJECT_NAME)

# Rasmlarni yuklash va ularga havola qilish uchun static papkani ulaymiz
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Sub-ilovalarni (sub-apps) ulash
app.mount("/api/v1/admin", admin_app)
app.mount("/api/v1/front", front_app)
app.mount("/api/v1/mobile", mobile_app)

# Hujjatlarga qayta yo'naltirish (redirect)
@app.get("/front-docs", include_in_schema=False)
async def redirect_front_docs():
    return RedirectResponse(url="/api/v1/front/front-docs")

@app.get("/front-redoc", include_in_schema=False)
async def redirect_front_redoc():
    return RedirectResponse(url="/api/v1/front/redoc")

@app.get("/mobile-docs", include_in_schema=False)
async def redirect_mobile_docs():
    return RedirectResponse(url="/api/v1/mobile/mobile-docs")

@app.get("/mobile-redoc", include_in_schema=False)
async def redirect_mobile_redoc():
    return RedirectResponse(url="/api/v1/mobile/redoc")

@app.get("/admin-docs", include_in_schema=False)
async def redirect_admin_docs():
    return RedirectResponse(url="/api/v1/admin/admin-docs")

@app.get("/admin-redoc", include_in_schema=False)
async def redirect_admin_redoc():
    return RedirectResponse(url="/api/v1/admin/redoc")

# SQLAdmin panelini ulash
admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=admin_auth_backend,
    title="Chorva.uz Admin",
    base_url="/admin",
    templates_dir="app/templates"
)

# Jinja2 global context processor — barcha admin template-larga 't' va 'admin_lang_code' ni uzatadi
_original_templates = admin.templates

_original_context_fn = getattr(_original_templates, "TemplateResponse", None)

class _AdminTemplates:
    """SQLAdmin templates wrapper — har bir so'rovga til lug'atini inject qiladi."""
    def __init__(self, wrapped):
        self._w = wrapped

    def TemplateResponse(self, request, name, context=None, *args, **kwargs):
        if context is None:
            context = {}
        
        lang = "uz"
        if request is not None and hasattr(request, "cookies"):
            lang = request.cookies.get("admin_lang", "uz")
            if lang not in ["uz", "ru", "en", "tr"]:
                lang = "uz"
        
        context["t"] = get_admin_t(lang)
        context["admin_lang_code"] = lang
        context["request"] = request
        
        return self._w.TemplateResponse(request, name, context, *args, **kwargs)

    def __getattr__(self, item):
        return getattr(self._w, item)

admin.templates = _AdminTemplates(admin.templates)

# Admin ko'rinishlarini ro'yxatdan o'tkazish
admin.add_view(UserAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(RegionAdmin)
admin.add_view(AdvertisementAdmin)
admin.add_view(ImageAdmin)
admin.add_view(OfferAdmin)
admin.add_view(VerificationCodeAdmin)

@app.get("/")
async def root():
    return {
        "message": "Chorva.uz backend MVP API ishlamoqda!",
        "front_swagger_docs": "/front-docs",
        "front_redoc_docs": "/front-redoc",
        "mobile_swagger_docs": "/mobile-docs",
        "mobile_redoc_docs": "/mobile-redoc",
        "admin_swagger_docs": "/admin-docs",
        "admin_redoc_docs": "/admin-redoc",
        "admin_dashboard": "/admin"
    }
