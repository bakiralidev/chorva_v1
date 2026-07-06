import asyncio
import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("Front API Endpointlarini test qilish boshlandi...\n")
    client.__enter__()
    try:
        # 1. Test registration
        print("1. /api/v1/front/auth/register test qilinmoqda...")
        test_user_data = {
            "email": "testuser@gmail.com",
            "phone_number": "+998991234567",
            "password": "testpassword123",
            "accepted_offer": True
        }
        # Register request
        reg_response = client.post("/api/v1/front/auth/register", json=test_user_data)
        if reg_response.status_code == 201:
            print("   [PASS] Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi.")
            # Akkauntni faollashtirish (verify)
            verify_data = {
                "username": test_user_data["email"],
                "code": reg_response.json()["verification_code"]
            }
            verify_res = client.post("/api/v1/front/auth/verify", json=verify_data)
            assert verify_res.status_code == 200, f"Verification failed: {verify_res.text}"
            print("   [PASS] Foydalanuvchi akkaunti faollashtirildi.")
        elif reg_response.status_code == 400 and "tizimda ro'yxatdan o'tgan" in reg_response.json().get("detail", ""):
            print("   [INFO] Foydalanuvchi allaqachon mavjud, davom etamiz.")
        else:
            print(f"   [FAIL] Ro'yxatdan o'tishda xatolik: {reg_response.status_code} - {reg_response.text}")
            sys.exit(1)

        # 2. Test login
        print("\n2. /api/v1/front/auth/login test qilinmoqda...")
        login_data = {
            "username": "testuser@gmail.com",
            "password": "testpassword123"
        }
        login_response = client.post("/api/v1/front/auth/login", data=login_data)
        assert login_response.status_code == 200, f"Login muvaffaqiyatsiz bo'ldi: {login_response.text}"
        token = login_response.json()["access_token"]
        print("   [PASS] Tizimga kirildi va JWT token olindi.")
        
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Test Directories (categories & regions)
        print("\n3. /api/v1/front/directories/categories va /regions test qilinmoqda...")
        cat_response = client.get("/api/v1/front/directories/categories")
        assert cat_response.status_code == 200, "Kategoriyalarni olishda xatolik"
        categories = cat_response.json()
        print(f"   [PASS] Kategoriyalar olindi. Soni: {len(categories)} ta.")

        # Multilingual tests
        # Accept-Language: ru
        cat_response_ru = client.get("/api/v1/front/directories/categories", headers={"Accept-Language": "ru"})
        assert cat_response_ru.status_code == 200
        categories_ru = cat_response_ru.json()
        assert categories_ru[0]["name"] == "Крупный рогатый скот", "Kategoriya nomi ruschada xato"
        print("   [PASS] Ruscha tarjima Accept-Language orqali muvaffaqiyatli olindi.")

        # Query param ?lang=en
        cat_response_en = client.get("/api/v1/front/directories/categories?lang=en")
        assert cat_response_en.status_code == 200
        categories_en = cat_response_en.json()
        assert categories_en[0]["name"] == "Cattle", "Kategoriya nomi inglizchada xato"
        print("   [PASS] Inglizcha tarjima ?lang=en query parametri orqali muvaffaqiyatli olindi.")

        # Fallback to default (uz) for unsupported language (fr)
        cat_response_fallback = client.get("/api/v1/front/directories/categories", headers={"Accept-Language": "fr"})
        assert cat_response_fallback.status_code == 200
        categories_fallback = cat_response_fallback.json()
        assert categories_fallback[0]["name"] == "Qoramol", "Fallback standart til (uz)ga o'tmadi"
        print("   [PASS] Fallback strategiyasi muvaffaqiyatli tekshirildi (fr -> uz).")
        
        reg_response = client.get("/api/v1/front/directories/regions")
        assert reg_response.status_code == 200, "Hududlarni olishda xatolik"
        regions = reg_response.json()
        print(f"   [PASS] Hududlar olindi. Soni: {len(regions)} ta.")

        # Select first category and region for the advertisement
        category_id = categories[0]["id"]
        region_id = regions[0]["id"]

        # 4. Test Create Ad (POST /api/v1/front/ads)
        print("\n4. /api/v1/front/ads (POST) test qilinmoqda...")
        import io
        ad_data = {
            "title": "Simmental sigir, sog'lom",
            "description": "Juda yaxshi holatdagi zotdor sigir. 3 yoshli, sut berishi a'lo darajada.",
            "price": "12000000.0",
            "is_negotiable": "true",
            "age": "3 yosh",
            "weight": "450 kg",
            "color": "Qizil-ola",
            "quantity": "1",
            "contact_phone": "+998901112233",
            "category_id": str(category_id),
            "region_id": str(region_id)
        }
        files = [
            ("images", ("sigir1.jpg", io.BytesIO(b"fake_image_bytes_1"), "image/jpeg")),
            ("images", ("sigir2.jpg", io.BytesIO(b"fake_image_bytes_2"), "image/jpeg"))
        ]
        
        ad_create_response = client.post("/api/v1/front/ads/", data=ad_data, files=files, headers=headers)
        assert ad_create_response.status_code == 201, f"E'lon qo'shishda xatolik: {ad_create_response.text}"
        ad_created = ad_create_response.json()
        ad_id = ad_created["id"]
        assert len(ad_created["images"]) == 2, f"Expected 2 images, but got {len(ad_created['images'])}"
        print(f"   [PASS] E'lon yaratildi. ID: {ad_id}")

        # 5. Test Get Ads List with Filters (GET /api/v1/front/ads)
        print("\n5. /api/v1/front/ads (GET - filtrlash bilan) test qilinmoqda...")
        # Filter by category
        filter_cat_slug = categories[0]["slug"]
        list_response = client.get(f"/api/v1/front/ads/?category={filter_cat_slug}&min_price=1000000&max_price=15000000")
        assert list_response.status_code == 200, f"Ro'yxat olishda xatolik: {list_response.text}"
        ads_list = list_response.json()
        assert len(ads_list) > 0, "Filtrlangan ro'yxat bo'sh bo'lmasligi kerak"
        print(f"   [PASS] Filtrlangan e'lonlar ro'yxati olindi. Soni: {len(ads_list)} ta.")

        # 6. Test Get Ad Detail & View Count (GET /api/v1/front/ads/{id})
        print("\n6. /api/v1/front/ads/{id} (GET - batafsil ko'rish) test qilinmoqda...")
        detail_response1 = client.get(f"/api/v1/front/ads/{ad_id}")
        assert detail_response1.status_code == 200, f"Detail olishda xatolik: {detail_response1.text}"
        views_before = detail_response1.json()["views_count"]
        
        # Fetch again to verify views_count increments
        detail_response2 = client.get(f"/api/v1/front/ads/{ad_id}")
        assert detail_response2.status_code == 200
        views_after = detail_response2.json()["views_count"]
        
        assert views_after == views_before + 1, f"Views count bittaga oshmadi: before={views_before}, after={views_after}"
        print(f"   [PASS] E'lon detali yuklandi va views_count oshishi tekshirildi (Oldin: {views_before}, Hozir: {views_after}).")

        # 7. Test Get My Ads (GET /api/v1/front/ads/my)
        print("\n7. /api/v1/front/ads/my (GET - mening e'lonlarim) test qilinmoqda...")
        my_ads_response = client.get("/api/v1/front/ads/my", headers=headers)
        assert my_ads_response.status_code == 200, f"Mening e'lonlarimni olishda xatolik: {my_ads_response.text}"
        my_ads = my_ads_response.json()
        assert len(my_ads) > 0, "Mening e'lonlarim ro'yxati bo'sh bo'lmasligi kerak"
        my_ad_ids = [ad["id"] for ad in my_ads]
        assert ad_id in my_ad_ids or str(ad_id) in my_ad_ids, "Yaratilgan e'lon mening e'lonlarim ro'yxatida bo'lishi kerak"
        print(f"   [PASS] Mening e'lonlarim muvaffaqiyatli olindi (Soni: {len(my_ads)} ta).")

        # 8. Test Get My Profile (GET /api/v1/front/auth/me)
        print("\n8. /api/v1/front/auth/me (GET - shaxsiy profil) test qilinmoqda...")
        profile_response = client.get("/api/v1/front/auth/me", headers=headers)
        assert profile_response.status_code == 200, f"Profilni olishda xatolik: {profile_response.text}"
        profile_data = profile_response.json()
        assert profile_data["email"] == "testuser@gmail.com", "Profil emaili noto'g'ri"
        print("   [PASS] Shaxsiy profil ma'lumotlari muvaffaqiyatli olindi.")

        # 9. Test Edit Ad (PUT /api/v1/front/ads/{id})
        print("\n9. /api/v1/front/ads/{id} (PUT - e'lonni tahrirlash) test qilinmoqda...")
        edit_data = {
            "title": "Simmental sigir, sog'lom (TAHRIRLANDI)",
            "price": 13500000.0,
            "description": "Yangi tahrirlangan ma'lumotlar bilan batafsil tavsif.",
            "contact_phone": "+998909990000"
        }
        edit_response = client.put(f"/api/v1/front/ads/{ad_id}", json=edit_data, headers=headers)
        assert edit_response.status_code == 200, f"E'lonni tahrirlashda xatolik: {edit_response.text}"
        edited_ad = edit_response.json()
        assert edited_ad["title"] == "Simmental sigir, sog'lom (TAHRIRLANDI)", "Tahrirlangan sarlavha mos kelmadi"
        assert edited_ad["price"] == 13500000.0, "Tahrirlangan narx mos kelmadi"
        assert edited_ad["updated_at"] is not None, "updated_at maydoni to'ldirilmagan"
        print("   [PASS] E'lon muvaffaqiyatli tahrirlandi.")

        # 10. Test Soft Delete Ad (DELETE /api/v1/front/ads/{id})
        print("\n10. /api/v1/front/ads/{id} (DELETE - soft delete) test qilinmoqda...")
        delete_response = client.delete(f"/api/v1/front/ads/{ad_id}", headers=headers)
        assert delete_response.status_code == 204, f"E'lonni soft-delete qilishda xatolik: {delete_response.text}"
        
        # Verify that the deleted ad is no longer visible in listings or detail APIs
        detail_response_after = client.get(f"/api/v1/front/ads/{ad_id}")
        assert detail_response_after.status_code == 404, "Soft-delete qilingan e'lon detail API orqali topilmasligi kerak"
        
        my_ads_response_after = client.get("/api/v1/front/ads/my", headers=headers)
        assert my_ads_response_after.status_code == 200
        my_ad_ids_after = [ad["id"] for ad in my_ads_response_after.json()]
        assert (str(ad_id) not in my_ad_ids_after) and (ad_id not in my_ad_ids_after), "Soft-delete qilingan e'lon shaxsiy e'lonlarda ham ko'rinmasligi kerak"
        print("   [PASS] E'lon soft-delete qilindi va tizimdan yashirildi.")

        print("\nBarcha front API testlari muvaffaqiyatli yakunlandi! [ALL PASSED]")
    finally:
        client.__exit__(None, None, None)

if __name__ == "__main__":
    run_tests()
