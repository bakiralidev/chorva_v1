# Chorva mollari savdo platformasi (MVP Backend)

FastAPI yordamida chorva mollari oldi-sotdisi uchun mo'ljallangan onlayn savdo platformasining MVP backend qismi.

## Texnologiyalar tarkibi
* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **Ma'lumotlar bazasi:** PostgreSQL (yoki SQLite local sinovlar uchun)
* **ORM:** SQLAlchemy (Async)
* **Avtorizatsiya:** JWT (JSON Web Token) & Bcrypt
* **Admin Panel:** SQLAdmin

---

## Loyiha Strukturasi
```text
chorva/
├── app/
│   ├── admin.py           # SQLAdmin paneli sozlamalari va hotfixlar
│   ├── config.py          # Pydantic Settings orqali konfiguratsiya
│   ├── database.py        # DB ulanishi va async session helper
│   ├── main.py            # FastAPI ilovasi va CORS sozlamalari
│   ├── auth/              # Avtorizatsiya & xavfsizlik logikasi
│   ├── models/            # SQLAlchemy modellar (User, Ad, Category, Region, Image)
│   ├── schemas/           # Pydantic validation sxemalari
│   └── routers/           # API Endpointlar (auth, ads, directories)
├── docker-compose.yml     # PostgreSQL uchun Docker sozlamalari
├── requirements.txt       # Loyiha kutubxonalari
├── seed.py                # Jadvallar yaratish va boshlang'ich ma'lumotlar yuklash
├── test_api.py            # API-ni sinovdan o'tkazish uchun integratsion test
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

### 2. Ma'lumotlar bazasini sozlash:
Mahalliy sozlamalar uchun `.env` faylidan foydalaniladi. Standart holatda SQLite bazasi ishlatiladi.
Agar PostgreSQL ishlatmoqchi bo'lsangiz:
```bash
docker-compose up -d       # Docker orqali Postgres-ni yoqish
```
Va `.env` faylida ulanish manzilini PostgreSQL ga o'zgartiring.

### 3. Jadvallarni yaratish va boshlang'ich ma'lumotlarni yuklash:
```bash
python seed.py
```
*Tizimda avtomatik tarzda quyidagi admin profili yaratiladi:*
* **Email:** `admin@chorva.uz`
* **Telefon:** `+998901234567`
* **Parol:** `admin123`

### 4. Loyihani ishga tushirish:
```bash
python run.py
```

* **Swagger API Hujjatlari:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Admin Panel:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

### 5. API Testini ishga tushirish:
Yozilgan barcha routerlarni tekshirib chiqish uchun integratsion testni ishga tushiring:
```bash
python test_api.py
```
