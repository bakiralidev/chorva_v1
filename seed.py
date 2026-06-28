import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import engine, Base, async_session_local
from app.models.category import Category, CategoryTranslation
from app.models.region import Region, RegionTranslation
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
            {
                "icon_url": "https://img.icons8.com/color/96/cow.png",
                "translations": [
                    {"language": "uz", "name": "Qoramol", "slug": "qoramol"},
                    {"language": "ru", "name": "Крупный рогатый скот", "slug": "krupniy-rogatiy-skot"},
                    {"language": "en", "name": "Cattle", "slug": "cattle"},
                    {"language": "tr", "name": "Sığır", "slug": "sigir"}
                ]
            },
            {
                "icon_url": "https://img.icons8.com/color/96/sheep.png",
                "translations": [
                    {"language": "uz", "name": "Qo'y", "slug": "qoy"},
                    {"language": "ru", "name": "Овцы", "slug": "ovci"},
                    {"language": "en", "name": "Sheep", "slug": "sheep"},
                    {"language": "tr", "name": "Koyun", "slug": "koyun"}
                ]
            },
            {
                "icon_url": "https://img.icons8.com/color/96/goat.png",
                "translations": [
                    {"language": "uz", "name": "Echki", "slug": "echki"},
                    {"language": "ru", "name": "Козы", "slug": "kozi"},
                    {"language": "en", "name": "Goats", "slug": "goats"},
                    {"language": "tr", "name": "Keçi", "slug": "keci"}
                ]
            },
            {
                "icon_url": "https://img.icons8.com/color/96/horse.png",
                "translations": [
                    {"language": "uz", "name": "Ot", "slug": "ot"},
                    {"language": "ru", "name": "Лошади", "slug": "loshadi"},
                    {"language": "en", "name": "Horses", "slug": "horses"},
                    {"language": "tr", "name": "At", "slug": "at"}
                ]
            },
            {
                "icon_url": "https://img.icons8.com/color/96/chicken.png",
                "translations": [
                    {"language": "uz", "name": "Parranda", "slug": "parranda"},
                    {"language": "ru", "name": "Птица", "slug": "ptica"},
                    {"language": "en", "name": "Poultry", "slug": "poultry"},
                    {"language": "tr", "name": "Kümes hayvanları", "slug": "kumes-hayvanlari"}
                ]
            },
            {
                "icon_url": "https://img.icons8.com/color/96/pawprints.png",
                "translations": [
                    {"language": "uz", "name": "Boshqa", "slug": "boshqa"},
                    {"language": "ru", "name": "Другие", "slug": "drugie"},
                    {"language": "en", "name": "Others", "slug": "others"},
                    {"language": "tr", "name": "Diğerleri", "slug": "digerleri"}
                ]
            }
        ]

        for cat in categories_data:
            uz_translation = [t for t in cat["translations"] if t["language"] == "uz"][0]
            # Check if category with this uz slug already exists
            q = select(Category).join(Category.translations).where(
                CategoryTranslation.language == "uz",
                CategoryTranslation.slug == uz_translation["slug"]
            )
            res = await session.execute(q)
            if not res.scalar_one_or_none():
                db_cat = Category(icon_url=cat["icon_url"])
                session.add(db_cat)
                await session.flush()
                for t in cat["translations"]:
                    db_t = CategoryTranslation(
                        category_id=db_cat.id,
                        language=t["language"],
                        name=t["name"],
                        slug=t["slug"]
                    )
                    session.add(db_t)
                print(f"Kategoriya qo'shildi: {uz_translation['name']}")

        # 2. Hududlarni (viloyatlarni) yuklash
        regions_data = [
            {
                "translations": [
                    {"language": "uz", "name": "Toshkent shahri"},
                    {"language": "ru", "name": "Город Ташкент"},
                    {"language": "en", "name": "Tashkent City"},
                    {"language": "tr", "name": "Taşkent Şehri"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Toshkent viloyati"},
                    {"language": "ru", "name": "Ташкентская область"},
                    {"language": "en", "name": "Tashkent Region"},
                    {"language": "tr", "name": "Taşkent Bölgesi"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Samarqand"},
                    {"language": "ru", "name": "Самарканд"},
                    {"language": "en", "name": "Samarkand"},
                    {"language": "tr", "name": "Semerkand"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Buxoro"},
                    {"language": "ru", "name": "Бухара"},
                    {"language": "en", "name": "Bukhara"},
                    {"language": "tr", "name": "Buhara"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Andijon"},
                    {"language": "ru", "name": "Андижан"},
                    {"language": "en", "name": "Andijan"},
                    {"language": "tr", "name": "Andican"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Farg'ona"},
                    {"language": "ru", "name": "Фергана"},
                    {"language": "en", "name": "Fergana"},
                    {"language": "tr", "name": "Fergana"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Namangan"},
                    {"language": "ru", "name": "Наманган"},
                    {"language": "en", "name": "Namangan"},
                    {"language": "tr", "name": "Namangan"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Qashqadaryo"},
                    {"language": "ru", "name": "Кашкадарья"},
                    {"language": "en", "name": "Kashkadarya"},
                    {"language": "tr", "name": "Kaşkaderya"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Surxondaryo"},
                    {"language": "ru", "name": "Сурхандарья"},
                    {"language": "en", "name": "Surkhandarya"},
                    {"language": "tr", "name": "Surhanderya"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Jizzax"},
                    {"language": "ru", "name": "Джизак"},
                    {"language": "en", "name": "Jizzakh"},
                    {"language": "tr", "name": "Cizzak"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Sirdaryo"},
                    {"language": "ru", "name": "Сырдарья"},
                    {"language": "en", "name": "Syrdarya"},
                    {"language": "tr", "name": "Sirderya"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Xorazm"},
                    {"language": "ru", "name": "Хорезм"},
                    {"language": "en", "name": "Khorezm"},
                    {"language": "tr", "name": "Harezm"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Navoiy"},
                    {"language": "ru", "name": "Навои"},
                    {"language": "en", "name": "Navoiy"},
                    {"language": "tr", "name": "Nevai"}
                ]
            },
            {
                "translations": [
                    {"language": "uz", "name": "Qoraqalpog'iston Respublikasi"},
                    {"language": "ru", "name": "Республика Каракалпакстан"},
                    {"language": "en", "name": "Republic of Karakalpakstan"},
                    {"language": "tr", "name": "Karakalpakistan Cumhuriyeti"}
                ]
            }
        ]

        for reg in regions_data:
            uz_translation = [t for t in reg["translations"] if t["language"] == "uz"][0]
            # Check if region with this uz name already exists
            q = select(Region).join(Region.translations).where(
                RegionTranslation.language == "uz",
                RegionTranslation.name == uz_translation["name"]
            )
            res = await session.execute(q)
            if not res.scalar_one_or_none():
                db_reg = Region()
                session.add(db_reg)
                await session.flush()
                for t in reg["translations"]:
                    db_t = RegionTranslation(
                        region_id=db_reg.id,
                        language=t["language"],
                        name=t["name"]
                    )
                    session.add(db_t)
                print(f"Hudud qo'shildi: {uz_translation['name']}")

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
                is_superuser=True,
                preferred_lang="uz"
            )
            session.add(admin_user)
            print(f"Admin yaratildi: Email={admin_email}, Telefon={admin_phone}, Parol={admin_pass}")

        await session.commit()
        print("\nBoshlang'ich ma'lumotlar muvaffaqiyatli saqlandi!")

if __name__ == "__main__":
    asyncio.run(seed_data())
