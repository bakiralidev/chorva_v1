import uuid
from contextvars import ContextVar
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt

from app.database import get_db
from app.config import settings
from app.auth.security import ALGORITHM
from app.models.user import User

# Request-scoped admin language ContextVar (defaults to 'uz')
admin_lang: ContextVar[str] = ContextVar("admin_lang", default="uz")

async def get_lang(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    Every API request should determine the language using this priority:
    1. Accept-Language header
    2. lang query parameter
    3. User preferred language
    4. Default language (uz)
    """
    # 1. Accept-Language header
    accept_lang = request.headers.get("Accept-Language")

    # 2. lang query parameter
    lang_param = request.query_params.get("lang")

    # 3. User preferred language
    user_pref_lang = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id_str = payload.get("sub")
            if user_id_str:
                user_id = uuid.UUID(user_id_str)
                query = select(User).where(User.id == user_id)
                result = await db.execute(query)
                user = result.scalar_one_or_none()
                if user:
                    user_pref_lang = getattr(user, "preferred_lang", None)
        except Exception:
            pass

    # Resolve languages in order of priority
    supported_langs = ["uz", "ru", "en", "tr"]
    for lang in [accept_lang, lang_param, user_pref_lang]:
        if lang:
            # Parse lang code (e.g. 'ru-RU' -> 'ru', 'uz' -> 'uz')
            code = lang.split(",")[0].split("-")[0].strip().lower()
            if code in supported_langs:
                return code

    return "uz"
