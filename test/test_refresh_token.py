import sys
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("=== Access + Refresh Token Autentifikatsiya Testlari ===\n")
    client.__enter__()
    try:
        # 1. Ro'yxatdan o'tish (Register)
        print("1. Foydalanuvchini ro'yxatdan o'tkazish...")
        test_user = {
            "email": "testtokenuser@gmail.com",
            "phone_number": "+998990000000",
            "password": "testpassword123",
            "accepted_offer": True
        }
        reg_res = client.post("/api/v1/mobile/auth/register", json=test_user)
        if reg_res.status_code == 201:
            print("   [PASS] Yangi foydalanuvchi yaratildi.")
            # Akkauntni faollashtirish (verify)
            verify_data = {
                "username": "testtokenuser@gmail.com",
                "code": reg_res.json()["verification_code"]
            }
            verify_res = client.post("/api/v1/mobile/auth/verify", json=verify_data)
            assert verify_res.status_code == 200, "Verification failed"
            tokens = verify_res.json()
            print("   [PASS] Kod tasdiqlandi va birinchi tokenlar olindi.")
        elif reg_res.status_code == 400 and "tizimda ro'yxatdan o'tgan" in reg_res.json().get("detail", ""):
            print("   [INFO] Foydalanuvchi allaqachon ro'yxatdan o'tgan, davom etamiz.")
        else:
            print(f"   [FAIL] Ro'yxatdan o'tishda kutilmagan xato: {reg_res.status_code} - {reg_res.text}")
            sys.exit(1)

        # 2. Kirish (Login) va Tokenlarni olish
        print("\n2. Login orqali Access va Refresh Tokenlarni olish...")
        login_data = {
            "username": "testtokenuser@gmail.com",
            "password": "testpassword123"
        }
        login_res = client.post("/api/v1/mobile/auth/login", data=login_data)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        
        tokens = login_res.json()
        assert "access_token" in tokens, "Access token missing"
        assert "refresh_token" in tokens, "Refresh token missing"
        assert tokens["token_type"] == "bearer", "Token type is not bearer"
        
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        print("   [PASS] Access va Refresh tokenlar muvaffaqiyatli olindi.")
        print(f"   -> Access Token (boshi): {access_token[:15]}...")
        print(f"   -> Refresh Token (boshi): {refresh_token[:15]}...")

        # 3. Access Token orqali himoyalangan endpointga murojaat qilish
        print("\n3. Access Token orqali /me endpointini chaqirish...")
        headers = {"Authorization": f"Bearer {access_token}"}
        me_res = client.get("/api/v1/mobile/auth/me", headers=headers)
        assert me_res.status_code == 200, f"Access token orqali kirib bo'lmadi: {me_res.text}"
        assert me_res.json()["email"] == "testtokenuser@gmail.com"
        print("   [PASS] Access Token yaroqli va ma'lumotlar olindi.")

        # 4. Refresh Token orqali tokenlarni yangilash (Rotation)
        print("\n4. Refresh Token yordamida tokenlarni yangilash...")
        time.sleep(1.1)  # Access token exp/timestamp o'zgarishi uchun 1 soniya kutamiz
        refresh_req = {"refresh_token": refresh_token}
        refresh_res = client.post("/api/v1/mobile/auth/refresh", json=refresh_req)
        assert refresh_res.status_code == 200, f"Token yangilashda xato: {refresh_res.text}"
        
        new_tokens = refresh_res.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        
        new_access_token = new_tokens["access_token"]
        new_refresh_token = new_tokens["refresh_token"]
        
        assert new_access_token != access_token, "Yangi access token eskisidan farq qilishi kerak"
        assert new_refresh_token != refresh_token, "Yangi refresh token eskisidan farq qilishi kerak (Rotation!)"
        
        print("   [PASS] Tokenlar yangilandi (Rotation muvaffaqiyatli ishladi).")

        # 5. Eski Refresh Token ishlatib ko'rish (Hujum tekshiruvi)
        print("\n5. Eski (ishlatib bo'lingan) Refresh Token orqali yangilashga urinish...")
        old_refresh_req = {"refresh_token": refresh_token}
        old_refresh_res = client.post("/api/v1/mobile/auth/refresh", json=old_refresh_req)
        assert old_refresh_res.status_code == 401, "Eski refresh token bekor qilinmagan!"
        print("   [PASS] Eski refresh token ishlamadi (401 Unauthorized qaytdi).")

        # 6. Yangi Access Token bilan ishlashni tekshirish
        print("\n6. Yangi Access Token yordamida profilga kirish...")
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        new_me_res = client.get("/api/v1/mobile/auth/me", headers=new_headers)
        assert new_me_res.status_code == 200
        print("   [PASS] Yangi Access Token muvaffaqiyatli ishladi.")

        # 7. Tizimdan chiqish (Logout) va bekor qilish
        print("\n7. Tizimdan chiqish (Logout) va Refresh Tokenni o'chirish...")
        logout_req = {"refresh_token": new_refresh_token}
        logout_res = client.post("/api/v1/mobile/auth/logout", json=logout_req)
        assert logout_res.status_code == 200, f"Logout failed: {logout_res.text}"
        print("   [PASS] Tizimdan chiqildi.")

        # 8. Tizimdan chiqqan Refresh Token bilan qayta refresh qilib ko'rish
        print("\n8. Chiqib ketilgan Refresh Token bilan yangilashga urinish...")
        logged_out_refresh_res = client.post("/api/v1/mobile/auth/refresh", json=logout_req)
        assert logged_out_refresh_res.status_code == 401, "Tizimdan chiqqan refresh token hamon ishlamoqda!"
        print("   [PASS] Chiqib ketilgan refresh token bekor bo'ldi (401 Unauthorized).")

        print("\n=== BARCHA TESTLAR MUVAFFAQIYATLI YAKUNLANDI [ALL PASS] ===")
    finally:
        client.__exit__(None, None, None)

if __name__ == "__main__":
    run_tests()
