"""
auth_google.py — Google OAuth2 orqali tizimga kirish endpointlari.

## Google Cloud Console'dan credentials olish tartibi:

1. **Google Cloud Console** ga o'ting: https://console.cloud.google.com
2. Yangi loyiha yarating yoki mavjudini tanlang
3. **APIs & Services → Library** → "Google+ API" yoki "Google Identity" qidiring → Enable
4. **APIs & Services → Credentials** → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Application type: **Web application**
6. Authorized redirect URIs ga qo'shing:
   - Development: `http://localhost:8000/api/v1/front/auth/google/callback`
   - Production: `https://yourdomain.com/api/v1/front/auth/google/callback`
7. **Client ID** va **Client Secret** ni `.env` fayliga yozing:
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

## Oqim (Flow):

1. Frontend `GET /auth/google` ga so'rov yuboradi → `authorization_url` oladi
2. Foydalanuvchi shu URL ga o'tadi → Google login sahifasi ochiladi
3. Google foydalanuvchi ruxsatini oladi → `GOOGLE_REDIRECT_URI` ga redirect qiladi
4. `GET /auth/google/callback?code=...` → server Google'dan token aladi → user info oladi
5. Foydalanuvchi bazaga saqlanadi (yangi bo'lsa yaratiladi, mavjud bo'lsa tokenlar yangilanadi)
6. JWT access_token va refresh_token qaytariladi
"""
import logging
import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.user import GoogleAuthResponse
from app.schemas.token import Token
from app.auth.security import create_access_token, generate_refresh_token
from app.config import settings

logger = logging.getLogger("app.auth.google")

router = APIRouter(prefix="/auth", tags=["Authentication — Google OAuth2"])

# Google OAuth2 endpointlari
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# So'ralgan ruxsatlar (scopes)
SCOPES = "openid email profile"


async def _create_refresh_token_in_db(db: AsyncSession, user_id: uuid.UUID) -> str:
    """Yangi refresh token yaratib bazaga saqlaydi."""
    token_str = generate_refresh_token()
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(user_id=user_id, token=token_str, expires_at=expires_at)
    db.add(db_token)
    await db.commit()
    return token_str


@router.get(
    "/google",
    response_model=GoogleAuthResponse,
    summary="Google OAuth2 bilan kirish — URL olish",
    description="""
### Google OAuth2 bilan kirish — 1-qadam

Foydalanuvchini Google login sahifasiga yo'naltirish uchun URL qaytaradi.

**Qanday ishlatiladi:**
1. Bu endpointga GET so'rov yuboring
2. Javobdagi `authorization_url` ni oling
3. Foydalanuvchini shu URLga yo'naltiring (redirect qiling)
4. Foydalanuvchi Google akkauntiga kirib, ruxsat bergach, callback endpointga qaytariladi

**Natija:** Foydalanuvchi `GOOGLE_REDIRECT_URI` ga `?code=...&state=...` parametrlari bilan qaytadi.
""",
)
async def google_login():
    """
    Google OAuth2 authorization URL ni qaytaradi.
    Frontend foydalanuvchini shu URL ga yo'naltirishi kerak.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth2 sozlanmagan. Administrator bilan bog'laning."
        )

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "select_account",
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    auth_url = f"{GOOGLE_AUTH_URL}?{query_string}"

    return {"authorization_url": auth_url}


@router.get(
    "/google/callback",
    response_model=Token,
    summary="Google OAuth2 callback — token olish",
    description="""
### Google OAuth2 bilan kirish — 2-qadam (Callback)

Google login muvaffaqiyatli bo'lgach, Google shu endpointga foydalanuvchini qaytaradi.

**Bu endpoint avtomatik ishlaydi** — uni to'g'ridan-to'g'ri chaqirmang.
Google `?code=...` parametri bilan redirect qilganda server:

1. Google'dan `code` ni `access_token` ga almashtiradi
2. Google'dan foydalanuvchi ma'lumotlarini oladi (`email`, `name`, `picture`, `google_id`)
3. Agar foydalanuvchi bazada yo'q bo'lsa — **yangi akkaunt yaratadi**
4. Agar mavjud bo'lsa — ma'lumotlarini yangilaydi
5. JWT `access_token` va `refresh_token` qaytaradi

**Foydalanuvchi ma'lumotlari bazaga yozilishi:**
- `email` — Google emaili
- `full_name` — To'liq ismi
- `avatar_url` — Profil rasmi URL
- `google_id` — Google'ning unique ID (`sub`)
- `auth_provider` — `"google"` qiymati
- `is_active = True`, `is_verified = True` (Google allaqachon tasdiqlagan)
- `accepted_offer = True` (birinchi kirishda avtomatik)
""",
)
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    Google OAuth2 callback handler.
    Google authorization code ni JWT tokenga almashtiradi.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth2 sozlanmagan."
        )

    # 1. Google'dan access_token olish
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if token_response.status_code != 200:
        logger.error("Google token xatoligi: %s", token_response.text)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google'dan token olishda xatolik yuz berdi."
        )

    token_data = token_response.json()
    google_access_token = token_data.get("access_token")

    if not google_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google access token olinmadi."
        )

    # 2. Google'dan foydalanuvchi ma'lumotlarini olish
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

    if userinfo_response.status_code != 200:
        logger.error("Google userinfo xatoligi: %s", userinfo_response.text)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google'dan foydalanuvchi ma'lumotlarini olishda xatolik."
        )

    google_user = userinfo_response.json()
    google_id = google_user.get("sub")
    email = google_user.get("email")
    full_name = google_user.get("name")
    avatar_url = google_user.get("picture")
    email_verified = google_user.get("email_verified", False)

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google'dan zaruriy ma'lumotlar olinmadi."
        )

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google emailingiz tasdiqlanmagan."
        )

    # 3. Foydalanuvchini bazadan qidirish (google_id yoki email bo'yicha)
    user: User | None = None

    # Avval google_id bo'yicha qidiramiz
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        # Email bo'yicha qidiramiz (avval local ro'yxatdan o'tgan bo'lishi mumkin)
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user:
        # Mavjud foydalanuvchi — Google ma'lumotlarini yangilaymiz
        user.google_id = google_id
        user.full_name = full_name or user.full_name
        user.avatar_url = avatar_url or user.avatar_url
        if not user.is_active:
            user.is_active = True
        if not user.is_verified:
            user.is_verified = True
        # Agar avval local ro'yxatdan o'tgan bo'lsa, auth_provider ni yangilashdan saqlaymiz
        if user.auth_provider == "local" and not user.hashed_password:
            user.auth_provider = "google"
        logger.info("Google OAuth2: mavjud foydalanuvchi yangilandi: email=%s", email)
    else:
        # Yangi foydalanuvchi yaratish
        user = User(
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
            google_id=google_id,
            hashed_password=None,  # Google foydalanuvchisida parol yo'q
            is_active=True,
            is_verified=True,
            accepted_offer=True,   # Google bilan kirganda oferta avtomatik qabul qilinadi
            is_superuser=False,
            auth_provider="google",
        )
        db.add(user)
        logger.info("Google OAuth2: yangi foydalanuvchi yaratildi: email=%s", email)

    await db.commit()
    await db.refresh(user)

    # 4. JWT tokenlar yaratish
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = await _create_refresh_token_in_db(db, user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
