"""
migrate_prod.py — PostgreSQL production serveri uchun xavfsiz migratsiya.

Bu script:
1. users jadvaliga YANGI ustunlar qo'shadi (mavjud ma'lumotlar saqlanadi)
2. telegram_links jadvalini yaratadi (agar yo'q bo'lsa)

XAVFSIZ: Mavjud ma'lumotlar O'CHIRILMAYDI!
"""
import sys, asyncio
sys.path.insert(0, '.')

async def migrate_production():
    from app.database import engine
    from sqlalchemy import text

    print("Production migratsiyasi boshlanmoqda...")

    migrations = [
        # ============================================================
        # 1. telegram_links jadvalini yaratish (yangi jadval)
        # ============================================================
        {
            "desc": "telegram_links jadvali yaratish",
            "sql": """
                CREATE TABLE IF NOT EXISTS telegram_links (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    phone_number VARCHAR(50) NOT NULL,
                    chat_id VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """
        },
        {
            "desc": "telegram_links.phone_number index",
            "sql": "CREATE INDEX IF NOT EXISTS ix_telegram_links_phone_number ON telegram_links(phone_number)"
        },

        # ============================================================
        # 2. users jadvaliga yangi ustunlar qo'shish
        # ============================================================
        {
            "desc": "users.hashed_password — NULL ga ruxsat berish",
            "sql": "ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL"
        },
        {
            "desc": "users.telegram_chat_id ustuni qo'shish",
            "sql": "ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id VARCHAR(50)"
        },
        {
            "desc": "users.google_id ustuni qo'shish",
            "sql": "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255)"
        },
        {
            "desc": "users.google_id UNIQUE index",
            "sql": "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users(google_id) WHERE google_id IS NOT NULL"
        },
        {
            "desc": "users.full_name ustuni qo'shish",
            "sql": "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255)"
        },
        {
            "desc": "users.avatar_url ustuni qo'shish",
            "sql": "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512)"
        },
        {
            "desc": "users.auth_provider ustuni qo'shish",
            "sql": "ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(20) DEFAULT 'local' NOT NULL"
        },
    ]

    async with engine.begin() as conn:
        for m in migrations:
            try:
                await conn.execute(text(m["sql"]))
                print(f"  OK: {m['desc']}")
            except Exception as e:
                err = str(e).strip()
                # Ba'zi xatolar normal (masalan, ustun allaqachon bor)
                if "already exists" in err or "duplicate" in err.lower():
                    print(f"  SKIP (allaqachon mavjud): {m['desc']}")
                else:
                    print(f"  XATO: {m['desc']}")
                    print(f"        {err}")

    await engine.dispose()
    print("\nMigratsiya tugadi!")

asyncio.run(migrate_production())
