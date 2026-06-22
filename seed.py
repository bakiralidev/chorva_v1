import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import engine, Base, async_session_local
from app.models.category import Category
from app.models.region import Region
from app.models.user import User
from app.auth.security import hash_password

async def seed_data():
    # Ma'lumotlar bazasi jadvallarini yaratish (ayniqsa SQLite uchun juda foydali)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Barcha jadvallar yaratildi yoki tekshirildi.")

    async with async_session_local() as session:
        # 1. Kategoriyalarni yuklash
        categories_data = [
            {"name": "Qoramol", "slug": "qoramol", "icon_url": "https://img.icons8.com/color/96/cow.png"},
            {"name": "Qo'y", "slug": "qoy", "icon_url": "https://img.icons8.com/color/96/sheep.png"},
            {"name": "Echki", "slug": "echki", "icon_url": "https://img.icons8.com/color/96/goat.png"},
            {"name": "Ot", "slug": "ot", "icon_url": "https://img.icons8.com/color/96/horse.png"},
            {"name": "Parranda", "slug": "parranda", "icon_url": "https://img.icons8.com/color/96/chicken.png"},
            {"name": "Boshqa", "slug": "boshqa", "icon_url": "https://img.icons8.com/color/96/pawprints.png"},
        ]

        for cat in categories_data:
            q = select(Category).where(Category.slug == cat["slug"])
            res = await session.execute(q)
            if not res.scalar_one_or_none():
                db_cat = Category(name=cat["name"], slug=cat["slug"], icon_url=cat["icon_url"])
                session.add(db_cat)
                print(f"Kategoriya qo'shildi: {cat['name']}")

        # 2. Hududlarni (viloyatlarni) yuklash
        regions_data = [
            "Toshkent shahri", "Toshkent viloyati", "Samarqand", "Buxoro", 
            "Andijon", "Farg'ona", "Namangan", "Qashqadaryo", 
            "Surxondaryo", "Jizzax", "Sirdaryo", "Xorazm", 
            "Navoiy", "Qoraqalpog'iston Respublikasi"
        ]

        for r_name in regions_data:
            q = select(Region).where(Region.name == r_name)
            res = await session.execute(q)
            if not res.scalar_one_or_none():
                db_reg = Region(name=r_name)
                session.add(db_reg)
                print(f"Hudud qo'shildi: {r_name}")

        # 3. Superuser (Admin) yaratish
        admin_email = "admin@chorva.uz"
        admin_phone = "+998901234567"
        admin_pass = "admin123"
        
        q_admin = select(User).where(User.email == admin_email)
        res_admin = await session.execute(q_admin)
        if not res_admin.scalar_one_or_none():
            admin_user = User(
                email=admin_email,
                phone_number=admin_phone,
                hashed_password=hash_password(admin_pass),
                is_active=True,
                is_superuser=True
            )
            session.add(admin_user)
            print(f"Admin yaratildi: Email={admin_email}, Telefon={admin_phone}, Parol={admin_pass}")

        await session.commit()
        print("\nBoshlang'ich ma'lumotlar muvaffaqiyatli saqlandi!")

if __name__ == "__main__":
    asyncio.run(seed_data())
