import asyncio
import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("API Endpointlarini test qilish boshlandi...\n")

    # 1. Test registration
    print("1. /api/v1/auth/register test qilinmoqda...")
    test_user_data = {
        "email": "testuser@gmail.com",
        "phone_number": "+998991234567",
        "password": "testpassword123"
    }
    # Register request
    reg_response = client.post("/api/v1/auth/register", json=test_user_data)
    if reg_response.status_code == 201:
        print("   [PASS] Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi.")
    elif reg_response.status_code == 400 and "tizimda ro'yxatdan o'tgan" in reg_response.json().get("detail", ""):
        print("   [INFO] Foydalanuvchi allaqachon mavjud, davom etamiz.")
    else:
        print(f"   [FAIL] Ro'yxatdan o'tishda xatolik: {reg_response.status_code} - {reg_response.text}")
        sys.exit(1)

    # 2. Test login
    print("\n2. /api/v1/auth/login test qilinmoqda...")
    login_data = {
        "username": "testuser@gmail.com",
        "password": "testpassword123"
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200, f"Login muvaffaqiyatsiz bo'ldi: {login_response.text}"
    token = login_response.json()["access_token"]
    print("   [PASS] Tizimga kirildi va JWT token olindi.")
    
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Test Directories (categories & regions)
    print("\n3. /api/v1/directories/categories va /regions test qilinmoqda...")
    cat_response = client.get("/api/v1/directories/categories")
    assert cat_response.status_code == 200, "Kategoriyalarni olishda xatolik"
    categories = cat_response.json()
    print(f"   [PASS] Kategoriyalar olindi. Soni: {len(categories)} ta.")
    
    reg_response = client.get("/api/v1/directories/regions")
    assert reg_response.status_code == 200, "Hududlarni olishda xatolik"
    regions = reg_response.json()
    print(f"   [PASS] Hududlar olindi. Soni: {len(regions)} ta.")

    # Select first category and region for the advertisement
    category_id = categories[0]["id"]
    region_id = regions[0]["id"]

    # 4. Test Create Ad (POST /api/v1/ads)
    print("\n4. /api/v1/ads (POST) test qilinmoqda...")
    ad_data = {
        "title": "Simmental sigir, sog'lom",
        "description": "Juda yaxshi holatdagi zotdor sigir. 3 yoshli, sut berishi a'lo darajada.",
        "price": 12000000.0,
        "is_negotiable": True,
        "age": "3 yosh",
        "weight": "450 kg",
        "color": "Qizil-ola",
        "quantity": 1,
        "contact_phone": "+998901112233",
        "category_id": category_id,
        "region_id": region_id,
        "images": [
            {"image_url": "https://example.com/sigir1.jpg", "is_main": True},
            {"image_url": "https://example.com/sigir2.jpg", "is_main": False}
        ]
    }
    
    ad_create_response = client.post("/api/v1/ads/", json=ad_data, headers=headers)
    assert ad_create_response.status_code == 201, f"E'lon qo'shishda xatolik: {ad_create_response.text}"
    ad_created = ad_create_response.json()
    ad_id = ad_created["id"]
    print(f"   [PASS] E'lon yaratildi. ID: {ad_id}")

    # 5. Test Get Ads List with Filters (GET /api/v1/ads)
    print("\n5. /api/v1/ads (GET - filtrlash bilan) test qilinmoqda...")
    # Filter by category
    filter_cat_slug = categories[0]["slug"]
    list_response = client.get(f"/api/v1/ads/?category={filter_cat_slug}&min_price=1000000&max_price=15000000")
    assert list_response.status_code == 200, f"Ro'yxat olishda xatolik: {list_response.text}"
    ads_list = list_response.json()
    assert len(ads_list) > 0, "Filtrlangan ro'yxat bo'sh bo'lmasligi kerak"
    print(f"   [PASS] Filtrlangan e'lonlar ro'yxati olindi. Soni: {len(ads_list)} ta.")

    # 6. Test Get Ad Detail & View Count (GET /api/v1/ads/{id})
    print("\n6. /api/v1/ads/{id} (GET - batafsil ko'rish) test qilinmoqda...")
    detail_response1 = client.get(f"/api/v1/ads/{ad_id}")
    assert detail_response1.status_code == 200, f"Detail olishda xatolik: {detail_response1.text}"
    views_before = detail_response1.json()["views_count"]
    
    # Fetch again to verify views_count increments
    detail_response2 = client.get(f"/api/v1/ads/{ad_id}")
    assert detail_response2.status_code == 200
    views_after = detail_response2.json()["views_count"]
    
    assert views_after == views_before + 1, f"Views count bittaga oshmadi: before={views_before}, after={views_after}"
    print(f"   [PASS] E'lon detali yuklandi va views_count oshishi tekshirildi (Oldin: {views_before}, Hozir: {views_after}).")

    print("\nBarcha testlar muvaffaqiyatli yakunlandi! [ALL PASSED]")

if __name__ == "__main__":
    run_tests()
