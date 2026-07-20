"""
migrate.py — SQLite development bazasini yangi schema bilan qayta yaratish.

DIQQAT: Bu script barcha ma'lumotlarni o'chiradi!
Faqat development muhitida ishlatilsin.
Production uchun Alembic migration ishlatiladi.
"""
import sys, asyncio
sys.path.insert(0, '.')

async def migrate():
    from app.database import engine, Base, AsyncSessionLocal
    from app.models import (
        User, Category, Region, Advertisement, Image,
        RefreshToken, Favorite, Offer, OfferTranslation,
        VerificationCode, Slider, TelegramLink
    )
    from sqlalchemy import text

    print("Migratsiya boshlanmoqda...")
    
    async with engine.begin() as conn:
        # Barcha jadvallarni o'chirib qayta yaratamiz
        await conn.run_sync(Base.metadata.drop_all)
        print("  Eski jadvallar o'chirildi")
        await conn.run_sync(Base.metadata.create_all)
        print("  Yangi jadvallar yaratildi")
    
    # Jadvallarni ko'rsatish
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        tables = [row[0] for row in result.fetchall()]
        print(f"\nJadvallar ({len(tables)} ta):")
        for t in tables:
            print(f"  OK {t}")
    
    await engine.dispose()
    print("\nMigratsiya muvaffaqiyatli tugadi!")
    print("Yangi ustunlar: telegram_chat_id, google_id, full_name, avatar_url, auth_provider")

asyncio.run(migrate())
