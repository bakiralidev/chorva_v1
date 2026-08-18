# Chorva Market — Frontend API Qo'llanmasi

> **Versiya:** 2.0  
> **Sana:** 2026-08-18  
> **API Dokumentatsiya:** `http://localhost:8000/api/v1/front/redoc` (production: `https://api.chorva.uz/api/v1/front/redoc`)

---

## 📋 Umumiy ma'lumotlar

### Base URL
```
http://localhost:8000/api/v1/front
```

### Autentifikatsiya
Barcha himoyalangan endpointlar uchun `Authorization` headerini yuboring:
```
Authorization: Bearer <access_token>
```

### Kirishning ikki yo'li

| Kanal | Ro'yxat usuli | Kirish usuli |
|-------|--------------|-------------|
| 🌐 **Sayt (Web)** | Email + parol | Email + parol |
| 📱 **Telegram Bot** | Bot orqali (ism + telefon) | Bot Mini App tugmasi |

---

## 🌐 SAYT (WEB) ORQALI KIRISH

### 1. Ro'yxatdan o'tish

**`POST /auth/register`**

```json
{
  "email": "user@example.com",
  "password": "strongpass123",
  "accepted_offer": true
}
```

**Javob (201):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "is_active": false,
    "auth_provider": "local"
  },
  "message": "Tasdiqlash kodi user@example.com elektron pochta manzilingizga yuborildi.",
  "otp_channel": "email"
}
```

> ⚠️ Foydalanuvchi `is_active: false` bo'ladi — OTP tasdiqlash kerak!

---

### 2. OTP tasdiqlash

**`POST /auth/verify`**

```json
{
  "username": "user@example.com",
  "code": "123456"
}
```

**Javob (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "uuid-token",
  "token_type": "bearer"
}
```

---

### 3. Tizimga kirish

**`POST /auth/login`**

```
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=strongpass123
```

**Javob (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "uuid-token",
  "token_type": "bearer"
}
```

---

### 4. Token yangilash

**`POST /auth/refresh`**

```json
{
  "refresh_token": "uuid-token"
}
```

---

### 5. Tizimdan chiqish

**`POST /auth/logout`**

```json
{
  "refresh_token": "uuid-token"
}
```

---

## 📱 TELEGRAM BOT ORQALI KIRISH

Bot: **[@chorva_uzbot](https://t.me/chorva_uzbot)**

### Bot onboarding oqimi:

```
Foydalanuvchi /start bosadi
        ↓
🌐 Til tanlang: [🇺🇿 O'zbek] [🇷🇺 Русский]
        ↓
✍️ "To'liq ismingizni kiriting" (kamida 5 belgi)
        ↓
📱 "Telefon raqamingizni ulashing" → [📱 Telefon raqamimni ulashish]
        ↓
✅ Ro'yxat muvaffaqiyatli!
        ↓
[🛒 Chorva Market'ni ochish] → Mini App ochiladi
```

### Bot foydalanuvchisi Mini App ochganda — avtomatik login:

**`POST /auth/telegram/login`** ← **ENG MUHIM ENDPOINT**

```json
{
  "init_data": "query_id=AAH...&user=%7B%22id%22...&hash=abc123"
}
```

**Javob (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "uuid-token",
  "token_type": "bearer"
}
```

**Frontend JS kodi (app yuklanganda birinchi ishlashi kerak):**
```javascript
const tg = window.Telegram?.WebApp;

if (tg && tg.initData) {
  // Telegram Mini App ichida
  const res = await fetch('/api/v1/front/auth/telegram/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: tg.initData })
  });

  if (res.ok) {
    const { access_token, refresh_token } = await res.json();
    localStorage.setItem('access_token', access_token);
    // → Login sahifasini ko'rsatma, foydalanuvchi kirgan!
  } else {
    // → Bot da ro'yxatdan o'tmagan
    tg.showAlert("Avval @chorva_uzbot da ro'yxatdan o'ting!");
  }
} else {
  // → Oddiy sayt → email login ko'rsat
}
```

| Xatolik | Sabab |
|---------|-------|
| 400 | initData noto'g'ri yoki muddati tugagan |
| 404 | Foydalanuvchi topilmadi (avval /start bosish kerak) |

---

## 👤 PROFIL MA'LUMOTLARI

### Profilni olish

**`GET /auth/me`**

**Javob:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "phone_number": "+998901234567",
  "full_name": "Bobur Karimov",
  "first_name": "Bobur",
  "last_name": "Karimov",
  "avatar_url": "/uploads/avatars/uuid.jpg",
  "auth_provider": "local",
  "preferred_lang": "uz",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-08-18T10:00:00Z"
}
```

---

## ✏️ PROFIL TAHRIRLASH

### 1. Ism va familyani yangilash

**`PUT /auth/me/name`**

```json
{
  "first_name": "Bobur",
  "last_name": "Karimov"
}
```

**Javob (200):** yangilangan `UserResponse`

| Xatolik | Sabab |
|---------|-------|
| 401 | Token yo'q yoki noto'g'ri |

---

### 2. Email o'zgartirish

> Email o'zgartirish **2 bosqich**li:

#### Bosqich 1: OTP yuborish

**`POST /auth/me/email/request-change`**

```json
{
  "new_email": "newemail@example.com"
}
```

**Javob (200):**
```json
{
  "message": "Tasdiqlash kodi newemail@example.com manziliga yuborildi."
}
```

| Xatolik | Sabab |
|---------|-------|
| 400 | Bu email allaqachon ro'yxatdan o'tgan |
| 401 | Token yo'q yoki noto'g'ri |

#### Bosqich 2: OTP tasdiqlash

**`POST /auth/me/email/confirm-change`**

```json
{
  "new_email": "newemail@example.com",
  "code": "123456"
}
```

**Javob (200):** yangilangan `UserResponse` (email yangilangan)

| Xatolik | Sabab |
|---------|-------|
| 400 | Kod noto'g'ri |
| 400 | Kod muddati tugagan (10 daqiqa) |

---

### 3. Parolni o'zgartirish

**`PUT /auth/me/password`**

```json
{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

**Javob (200):**
```json
{
  "message": "Parol muvaffaqiyatli o'zgartirildi."
}
```

| Xatolik | Sabab |
|---------|-------|
| 400 | Eski parol noto'g'ri |
| 400 | Google OAuth2 foydalanuvchisi (paroli yo'q) |
| 401 | Token yo'q yoki noto'g'ri |

---

### 4. Avatar (profil rasmi) yuklash

**`POST /auth/me/avatar`**

```
Content-Type: multipart/form-data

file: <rasm fayli>
```

**Qabul qilinadigan formatlar:** `jpg`, `jpeg`, `png`, `webp`  
**Maksimal hajm:** 5 MB

**Javob (200):** yangilangan `UserResponse`  
(`avatar_url` = `/uploads/avatars/uuid.jpg`)

**Avatar URL ni ko'rsatish:**
```
https://api.chorva.uz/uploads/avatars/uuid.jpg
```

| Xatolik | Sabab |
|---------|-------|
| 400 | Noto'g'ri format (faqat jpg/png/webp) |
| 400 | 5 MB dan katta |
| 401 | Token yo'q yoki noto'g'ri |

---

### 5. Telefon raqam qo'shish / o'zgartirish

> **Muhim:** Telefon raqam faqat Telegram bot orqali tasdiqlash bilan qo'shiladi.
> Foydalanuvchi avval **@chorva_uzbot** ga `/start` bosib telefon ulashgan bo'lishi kerak!

#### Oqim diagrammasi:

```
Foydalanuvchi saytda telefon raqam kiritadi
              ↓
POST /auth/me/phone/request-change
              ↓
Telegram botga OTP kodi keladi (@chorva_uzbot)
              ↓
Foydalanuvchi kodni saytda kiritadi
              ↓
POST /auth/me/phone/confirm-change
              ↓
✅ Telefon raqam saqlandi
```

#### Bosqich 1: OTP yuborish (Telegram orqali)

**`POST /auth/me/phone/request-change`**

```json
{
  "phone_number": "+998901234567"
}
```

**Javob (200):**
```json
{
  "message": "Tasdiqlash kodi Telegram botga yuborildi. @chorva_uzbot ni tekshiring."
}
```

| Xatolik | Sabab |
|---------|-------|
| 400 | Bu raqam boshqa foydalanuvchida |
| 404 | Bu raqam Telegram botda topilmadi (avval /start bosish kerak) |
| 401 | Token yo'q yoki noto'g'ri |

#### Bosqich 2: OTP tasdiqlash

**`POST /auth/me/phone/confirm-change`**

```json
{
  "phone_number": "+998901234567",
  "code": "123456"
}
```

**Javob (200):** yangilangan `UserResponse` (phone_number yangilangan)

| Xatolik | Sabab |
|---------|-------|
| 400 | Kod noto'g'ri |
| 400 | Kod muddati tugagan (10 daqiqa) |

---

## 🔄 TOKENLAR BOSHQARUVI

### Access Token muddati
`.env` dagi `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 1440 daqiqa = 24 soat)

### Refresh Token muddati
`.env` dagi `REFRESH_TOKEN_EXPIRE_DAYS` (default: 7 kun)

### Token yangilash oqimi:
```
Access token muddati tugadi (401 javob)
              ↓
POST /auth/refresh { "refresh_token": "..." }
              ↓
Yangi access_token + yangi refresh_token
              ↓
Eski refresh_token bekor qilinadi (Token Rotation)
```

---

## 📊 UserResponse sxemasi

Barcha profil endpointlari shu strukturani qaytaradi:

```typescript
interface UserResponse {
  id: string;               // UUID
  email: string | null;
  phone_number: string | null;
  telegram_username: string | null;
  full_name: string | null;
  first_name: string | null;
  last_name: string | null;
  avatar_url: string | null;  // /uploads/avatars/uuid.jpg
  auth_provider: "local" | "google" | "telegram";
  preferred_lang: "uz" | "ru" | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;       // ISO 8601
}
```

---

## 🔗 Qo'shimcha endpointlar

| Endpoint | Tavsif |
|----------|--------|
| `GET /auth/google` | Google OAuth2 kirish URL olish |
| `GET /directories/categories` | Kategoriyalar ro'yxati |
| `GET /directories/regions` | Hududlar ro'yxati |
| `GET /ads` | E'lonlar ro'yxati |
| `GET /sliders` | Slider rasmlari |
| `GET /favorites` | Sevimlilar ro'yxati |

---

## 🌐 API Dokumentatsiya linklari

| Tur | URL |
|-----|-----|
| **ReDoc** (tavsiya etiladi) | `/api/v1/front/redoc` |
| **Swagger UI** | `/api/v1/front/front-docs` |
