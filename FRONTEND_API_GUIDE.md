# Chorva.uz — Frontend API Integration Guide

> **Versiya:** 2.0  
> **Bazaviy URL (Front):** `http://localhost:8000/api/v1/front`  
> **Bazaviy URL (Mobile):** `http://localhost:8000/api/v1/mobile`  
> **Muhit:** Development

---

## Mundarija

1. [Autentifikatsiya strategiyasi](#1-autentifikatsiya-strategiyasi)
2. [Email OTP — parolsiz kirish](#2-email-otp--parolsiz-kirish)
3. [Parol bilan ro'yxat (klassik flow)](#3-parol-bilan-royxat-klassik-flow)
4. [Google orqali kirish](#4-google-orqali-kirish)
5. [Token boshqaruvi](#5-token-boshqaruvi)
6. [Tizimdan chiqish](#6-tizimdan-chiqish)
7. [Foydalanuvchi profili](#7-foydalanuvchi-profili)
8. [Xato kodlari](#8-xato-kodlari)
9. [Muhim eslatmalar](#9-muhim-eslatmalar)

---

## 1. Autentifikatsiya strategiyasi

Tizimda **3 xil** kirish usuli mavjud:

| Usul | Endpoint | Parol kerakmi? | Tavsiya |
|------|----------|----------------|---------|
| **Email OTP** | `/auth/email/request-otp` | Yo'q | ✅ Asosiy |
| Parol bilan | `/auth/register` + `/auth/login` | Ha | Legacy |
| **Google** | `/auth/google` | Yo'q | ✅ Asosiy |

**Token saqlash:** `localStorage` yoki `httpOnly cookie`  
**Authorization sarlavhasi:** `Authorization: Bearer <access_token>`

---

## 2. Email OTP — parolsiz kirish

> **Bu usul tavsiya etiladi.** Foydalanuvchi parol o'rnatmaydi.  
> Yangi user bo'lsa — avtomatik ro'yxatdan o'tadi.  
> Mavjud user bo'lsa — login bo'ladi.

### 2.1 OTP so'rash

```
POST /api/v1/front/auth/email/request-otp
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Muvaffaqiyatli javob (200):**
```json
{
  "message": "Tasdiqlash kodi user@example.com manziliga yuborildi.",
  "expires_in": 300
}
```

**Frontend logikasi:**
```javascript
async function requestOtp(email) {
  const res = await fetch('/api/v1/front/auth/email/request-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Xatolik yuz berdi');
  }

  const data = await res.json();
  // data.expires_in = 300 (sekund)
  // OTP input sahifasiga o'tish
  return data;
}
```

**UI holatlari:**
- Loading spinner ko'rsatish
- Muvaffaqiyatli bo'lsa → OTP kiritish sahifasiga o'tish
- Xato bo'lsa → xato xabarini ko'rsatish

---

### 2.2 OTP tasdiqlash va token olish

```
POST /api/v1/front/auth/email/verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```

**Muvaffaqiyatli javob (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "phone_number": null,
    "full_name": null,
    "first_name": null,
    "last_name": null,
    "avatar_url": null,
    "auth_provider": "local",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2026-08-19T11:00:00"
  }
}
```

**Frontend logikasi:**
```javascript
async function verifyOtp(email, code) {
  const res = await fetch('/api/v1/front/auth/email/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code })
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail);
  }

  const data = await res.json();

  // Tokenlarni saqlash
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  // Foydalanuvchi ma'lumotlarini saqlash
  localStorage.setItem('user', JSON.stringify(data.user));

  // Dashboard yoki bosh sahifaga yo'naltirish
  window.location.href = '/dashboard';

  return data;
}
```

**Xato kodlari:**
| Status | detail | Nima qilish |
|--------|--------|-------------|
| 404 | "Bu email uchun OTP so'ralmagan..." | request-otp ga qaytarish |
| 400 | "Tasdiqlash kodi muddati tugagan..." | Qaytadan OTP so'rash tugmasi |
| 400 | "Tasdiqlash kodi noto'g'ri." | Xato xabari ko'rsatish |

---

### 2.3 OTP sahifasi UI tavsiyasi

```
┌─────────────────────────────────┐
│  Tasdiqlash kodi yuborildi!     │
│  user@example.com               │
│                                 │
│  [  _  ] [  _  ] [  _  ]       │
│  [  _  ] [  _  ] [  _  ]       │
│                                 │
│  Kod 4:58 da tugaydi  ⏱        │
│                                 │
│  [   Tasdiqlash   ]             │
│                                 │
│  Kodni olmadingizmi?            │
│  [ Qaytadan yuborish ] (30s)    │
└─────────────────────────────────┘
```

**Timer logikasi:**
```javascript
// expires_in = 300 (5 daqiqa)
let timeLeft = 300;
const timer = setInterval(() => {
  timeLeft--;
  if (timeLeft <= 0) {
    clearInterval(timer);
    // "Kod muddati tugadi" ko'rsatish
  }
}, 1000);
```

**Resend OTP logikasi:**
- Resend tugmasini bosishda qaytadan `request-otp` endpointiga so'rov yuborish
- Resend tugmasini 30 soniya cooldown bilan ko'rsatish

---

## 3. Parol bilan ro'yxat (klassik flow)

> Bu flow hozirda ham ishlaydi. Eski integratsiya uchun.

### 3.1 Ro'yxatdan o'tish

```
POST /api/v1/front/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "accepted_offer": true
}
```

**Javob (201):**
```json
{
  "user": { "id": "...", "email": "user@example.com", ... },
  "message": "Tasdiqlash kodi user@example.com elektron pochta manzilingizga yuborildi.",
  "otp_channel": "email"
}
```

### 3.2 OTP tasdiqlash (klassik)

```
POST /api/v1/front/auth/verify
Content-Type: application/json

{
  "username": "user@example.com",
  "code": "123456"
}
```

**Javob (200):** `{ "access_token": "...", "refresh_token": "...", "token_type": "bearer" }`

### 3.3 Login (parol bilan)

```
POST /api/v1/front/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword123
```

> **Eslatma:** Bu endpoint `OAuth2PasswordRequestForm` formatida so'rov qabul qiladi (`x-www-form-urlencoded`).

---

## 4. Google orqali kirish

> **Bu usul ham tavsiya etiladi.** Foydalanuvchi hech qanday parol kiritmaydi.

### Oqim diagrammasi

```
Frontend          Backend           Google
   │                  │                │
   │─ GET /auth/google ─►              │
   │◄─ {authorization_url} ──────────── │
   │                  │                │
   │──────────────── Foydalanuvchi Google URL ga o'tadi ────────►│
   │                  │                │
   │◄─────────────── /auth/google/callback?code=...&state=... ───│
   │                  │                │
   │◄─ {access_token, refresh_token} ──│
```

### 4.1 Authorization URL olish

```
GET /api/v1/front/auth/google
```

**Javob (200):**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&state=abc123..."
}
```

**Frontend logikasi:**
```javascript
async function loginWithGoogle() {
  const res = await fetch('/api/v1/front/auth/google');
  const data = await res.json();
  // Foydalanuvchini Google sahifasiga yo'naltirish
  window.location.href = data.authorization_url;
}
```

### 4.2 Callback — token olish

Google foydalanuvchini tasdiqlangandan so'ng `GOOGLE_REDIRECT_URI` ga yuboradi:

```
GET /api/v1/front/auth/google/callback?code=4%2F0...&state=abc123...
```

Backend:
1. `state` parametrini CSRF tekshiruvi uchun validates qiladi
2. Google'dan `code` ni `access_token` ga almashtiradi
3. Foydalanuvchi ma'lumotlarini oladi
4. User yaratadi yoki topadi (email bo'yicha linking)
5. JWT tokenlar qaytaradi

**Javob (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
  "token_type": "bearer"
}
```

> **Muhim:** Callback JSON qaytaradi. Agar frontend SPA bo'lsa, callback URL uchun alohida sahifa yarating yoki `state` parametrida `redirect_to` URL ni encode qilishingiz mumkin.

**SPA uchun tavsiya:**

Backend callbackdan keyin frontendga redirect qilishi uchun backend kodini o'zgartirish mumkin — bu maxsus so'rov asosida.

---

### 4.3 Account linking (Email + Google)

Agar foydalanuvchi avval `user@example.com` bilan Email OTP orqali ro'yxatdan o'tgan bo'lsa va keyin aynan shu email bilan Google orqali kirsa:

- **Ikkinchi account yaratilmaydi**
- Backend `email` bo'yicha mavjud userni topadi
- `google_id` va `avatar_url` yangilanadi
- Foydalanuvchi login bo'ladi

---

## 5. Token boshqaruvi

### 5.1 Access Token muddati

- **Access Token:** `ACCESS_TOKEN_EXPIRE_MINUTES` (standart: 1440 daqiqa = 24 soat)
- **Refresh Token:** 7 kun

### 5.2 Har bir so'rovda token yuborish

```javascript
const response = await fetch('/api/v1/front/ads', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});
```

### 5.3 Token yangilash (Refresh Token Rotation)

```
POST /api/v1/front/auth/refresh
Content-Type: application/json

{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
}
```

**Javob (200):**
```json
{
  "access_token": "yangi_access_token...",
  "refresh_token": "yangi_refresh_token...",
  "token_type": "bearer"
}
```

> **Muhim:** Har yangilanishda **eski refresh_token bekor qilinadi** va yangi biri beriladi. Yangi refresh_tokenni saqlashni unutmang.

**Auto-refresh logikasi:**
```javascript
async function fetchWithAuth(url, options = {}) {
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  });

  if (response.status === 401) {
    // Access token eskirgan — refresh qilish
    const refreshed = await refreshAccessToken();
    if (!refreshed) {
      // Refresh ham ishlamadi — login sahifasiga yo'naltirish
      window.location.href = '/login';
      return;
    }
    // Qaytadan so'rov
    response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
  }

  return response;
}

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) return false;

  const res = await fetch('/api/v1/front/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  if (!res.ok) return false;

  const data = await res.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return true;
}
```

---

## 6. Tizimdan chiqish

```
POST /api/v1/front/auth/logout
Content-Type: application/json

{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
}
```

**Javob (200):**
```json
{
  "message": "Tizimdan muvaffaqiyatli chiqildi."
}
```

**Frontend logikasi:**
```javascript
async function logout() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  await fetch('/api/v1/front/auth/logout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  // Local ma'lumotlarni tozalash
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');

  // Login sahifasiga yo'naltirish
  window.location.href = '/login';
}
```

---

## 7. Foydalanuvchi profili

### 7.1 Profilni olish

```
GET /api/v1/front/auth/me
Authorization: Bearer <access_token>
```

**Javob (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "phone_number": null,
  "full_name": "Bobur Karimov",
  "first_name": "Bobur",
  "last_name": "Karimov",
  "avatar_url": "https://lh3.googleusercontent.com/...",
  "auth_provider": "local",
  "preferred_lang": "uz",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-08-19T11:00:00"
}
```

### 7.2 Ism yangilash

```
PUT /api/v1/front/auth/me/name
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "Bobur",
  "last_name": "Karimov"
}
```

### 7.3 Avatar yuklash

```
POST /api/v1/front/auth/me/avatar
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <rasm fayli> (jpg/png/webp, max 5MB)
```

---

## 8. Xato kodlari

| HTTP Status | Nima uchun | Nima qilish |
|------------|------------|-------------|
| 400 | So'rov noto'g'ri (validation xatosi) | `detail` xabarini foydalanuvchiga ko'rsating |
| 401 | Token yo'q, eskirgan yoki noto'g'ri | Token yangilash, kerak bo'lsa login sahifasiga yo'naltirish |
| 403 | Ruxsat yo'q | Xato xabari ko'rsatish |
| 404 | Ma'lumot topilmadi | Tegishli xabar ko'rsatish |
| 422 | Request body noto'g'ri format | So'rov tuzilishini tekshiring |
| 429 | Juda ko'p so'rov (rate limit) | Kutib, qaytadan urinish |
| 500 | Server xatosi | Xato loglash, qaytadan urinish |
| 503 | Servis ishlamayapti (SMTP, Google) | Xato xabari ko'rsatish |

**Xato javobi formati:**
```json
{
  "detail": "Xato haqida ma'lumot"
}
```

---

## 9. Muhim eslatmalar

### SMTP konfiguratsiyasi

Email OTP ishlashi uchun `.env` da quyidagilar to'ldirilgan bo'lishi kerak:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password  # 2FA + App Password
SMTP_FROM_NAME=Chorva.uz
```

> Gmail App Password olish: Google Account → Security → 2-Step Verification → App passwords

### Google OAuth konfiguratsiyasi

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/front/auth/google/callback
```

> Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs

> **Google Consent Screen:** Agar "TESTING" holatida bo'lsa, faqat Test Users ro'yxatidagi emaillar Google bilan kira oladi. Production'ga publish qiling.

### Token saqlash xavfsizligi

- `localStorage` — oddiy SPA uchun
- `httpOnly cookie` — XSS ga qarshi himoya kerak bo'lsa (backend sozlamasi kerak)

### CORS

Development uchun barcha originlarga ruxsat berilgan (`*`).  
Production'da faqat frontend domeni ruxsat etilishi kerak.

---

## Barcha Auth Endpointlar

| Method | URL | Tavsif |
|--------|-----|--------|
| `POST` | `/auth/email/request-otp` | Email OTP so'rash (YANGI) |
| `POST` | `/auth/email/verify-otp` | Email OTP tasdiqlash (YANGI) |
| `POST` | `/auth/register` | Parol bilan ro'yxat |
| `POST` | `/auth/verify` | OTP tasdiqlash (register uchun) |
| `POST` | `/auth/login` | Parol bilan kirish |
| `GET` | `/auth/me` | Profilni olish |
| `PUT` | `/auth/me` | Profilni yangilash |
| `PUT` | `/auth/me/name` | Ism yangilash |
| `POST` | `/auth/me/email/request-change` | Email o'zgartirish OTP |
| `POST` | `/auth/me/email/confirm-change` | Email o'zgartirish tasdiqlash |
| `PUT` | `/auth/me/password` | Parol o'zgartirish |
| `POST` | `/auth/me/avatar` | Avatar yuklash |
| `POST` | `/auth/me/phone/request-change` | Telefon o'zgartirish OTP |
| `POST` | `/auth/me/phone/confirm-change` | Telefon o'zgartirish tasdiqlash |
| `POST` | `/auth/refresh` | Token yangilash |
| `POST` | `/auth/logout` | Tizimdan chiqish |
| `GET` | `/auth/google` | Google OAuth URL olish |
| `GET` | `/auth/google/callback` | Google OAuth callback |
| `POST` | `/auth/telegram/login` | Telegram Mini App login |
