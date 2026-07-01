# Chorva mollari savdo platformasi (MVP Backend)

FastAPI yordamida chorva mollari oldi-sotdisi uchun mo'ljallangan onlayn savdo platformasining MVP backend qismi.

## Texnologiyalar tarkibi
* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **Ma'lumotlar bazasi:** PostgreSQL
* **ORM:** SQLAlchemy (Async)
* **Avtorizatsiya:** JWT (Access Token 30 daqiqa) & Kriptografik xavfsiz Refresh Token (7 kun) + Token Rotation & Logout
* **Admin Panel:** SQLAdmin

---

## Loyiha Strukturasi
```text
chorva/
├── app/
│   ├── admin.py           # SQLAdmin paneli sozlamalari, formalar va hotfixlar
│   ├── config.py          # Pydantic Settings orqali konfiguratsiya (token umri va hkz)
│   ├── database.py        # DB ulanishi va async session helper
│   ├── main.py            # FastAPI ilovasi va CORS sozlamalari
│   ├── auth/              # Avtorizatsiya & xavfsizlik logikasi va dependencies
│   ├── models/            # SQLAlchemy modellar (User, Ad, Category, Region, Image, RefreshToken, Offer)
│   ├── schemas/           # Pydantic validation sxemalari
│   └── routers/           # API Endpointlar (auth, ads, directories, offers)
├── docker-compose.yml     # PostgreSQL uchun Docker sozlamalari
├── requirements.txt       # Loyiha kutubxonalari
├── scripts/migrate_db.py  # Ma'lumotlar bazasini migratsiya qilish va ustunlarni yangilash skripti
├── scripts/seed.py        # Jadvallar yaratish va boshlang'ich ma'lumotlar yuklash
├── test_api.py            # Front API-ni sinovdan o'tkazish uchun integratsion test
├── test_mobile_api.py     # Mobile API-ni sinovdan o'tkazish uchun integratsion test
├── test_refresh_token.py  # Access/Refresh Token aylanishi va Logoutni tekshirish testi
└── run.py                 # Loyihani ishga tushiruvchi uvicorn serveri
```

---

## O'rnatish va Ishga tushirish

### 1. Virtual muhit yaratish va kutubxonalarni o'rnatish:
```bash
python -m venv venv
venv\Scripts\activate      # Windows uchun
pip install -r requirements.txt
```

### 2. Ma'lumotlar bazasini sozlash va migratsiya:
Mahalliy sozlamalar uchun `.env` faylidan foydalaniladi. Standart holatda PostgreSQL bazasi ishlatiladi.
Avval PostgreSQL konteynerini ishga tushiring:
```bash
docker-compose up -d
```

Keyin jadvallarni yaratish va eng oxirgi o'zgarishlar (ustunlar) bazada aks etishi uchun quyidagi buyruqni ishga tushiring:
```bash
python scripts/migrate_db.py
```

### 3. Boshlang'ich ma'lumotlarni yuklash (Seed):
```bash
python scripts/seed.py
```
*Tizimda avtomatik tarzda quyidagi admin profili yaratiladi:*
* **Email:** `admin@chorva.uz`
* **Telefon:** `+998901234567`
* **Parol:** `admin123`

### 4. Loyihani ishga tushirish:
```bash
python run.py
```

Runtime loglar `logs/app.log` fayliga, xatoliklar esa `logs/error.log` fayliga yoziladi.

* **Veb-sayt API Hujjatlari (Swagger):** [http://127.0.0.1:8000/front-docs](http://127.0.0.1:8000/front-docs) (Redoc: `/front-redoc`)
* **Mobil Ilova API Hujjatlari (Swagger):** [http://127.0.0.1:8000/mobile-docs](http://127.0.0.1:8000/mobile-docs) (Redoc: `/mobile-redoc`)
* **Admin REST API Hujjatlari (Swagger):** [http://127.0.0.1:8000/admin-docs](http://127.0.0.1:8000/admin-docs) (Redoc: `/admin-redoc`)
* **Admin Panel (SQLAdmin):** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

### 5. API Integratsion Testlarini ishga tushirish:
Tizim to'g'ri ishlayotganini tekshirish uchun barcha testlarni ketma-ketlikda ishga tushiring:
```bash
python test_api.py            # Front API testlari
python test_mobile_api.py     # Mobil API testlari
python test_refresh_token.py  # Access/Refresh token aylanishi va xavfsizlik testlari
```
