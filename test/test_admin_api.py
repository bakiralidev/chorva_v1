import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_admin_tests():
    print("Admin REST API Endpointlarini test qilish boshlandi...\n")
    client.__enter__()
    try:
        # 1. Admin login
        print("1. Admin hisobiga kirish test qilinmoqda (POST /api/v1/front/auth/login)...")
        admin_login_data = {
            "username": "admin@chorva.uz",
            "password": "admin123"
        }
        login_response = client.post("/api/v1/front/auth/login", data=admin_login_data)
        if login_response.status_code != 200:
            print(f"   [FAIL] Admin hisobiga kirib bo'lmadi: {login_response.status_code} - {login_response.text}")
            sys.exit(1)
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   [PASS] Admin hisobiga muvaffaqiyatli kirildi va token olindi.")

        # 2. List Users
        print("\n2. Foydalanuvchilar ro'yxatini olish test qilinmoqda (GET /api/v1/admin/users/)...")
        users_response = client.get("/api/v1/admin/users/", headers=headers)
        assert users_response.status_code == 200, f"Foydalanuvchilarni olishda xatolik: {users_response.text}"
        users = users_response.json()
        assert len(users) > 0, "Kamida bitta foydalanuvchi (admin) bo'lishi kerak"
        print(f"   [PASS] Foydalanuvchilar ro'yxati olindi. Soni: {len(users)} ta.")

        # Get single user details
        user_id = users[0]["id"]
        print(f"\n3. Bitta foydalanuvchi ma'lumotini olish test qilinmoqda (GET /api/v1/admin/users/{user_id})...")
        user_detail_response = client.get(f"/api/v1/admin/users/{user_id}", headers=headers)
        assert user_detail_response.status_code == 200, "Foydalanuvchi tafsilotini olishda xatolik"
        print("   [PASS] Foydalanuvchi tafsiloti muvaffaqiyatli olindi.")

        # 4. Test Category CRUD
        print("\n4. Kategoriyalar boshqaruvi test qilinmoqda...")
        # Create category
        cat_data = {"name": "Test Kategoriya", "slug": "test-kategoriya", "icon_url": "https://example.com/icon.png"}
        cat_create_resp = client.post("/api/v1/admin/categories/", json=cat_data, headers=headers)
        assert cat_create_resp.status_code == 201, f"Kategoriya yaratishda xatolik: {cat_create_resp.text}"
        created_cat = cat_create_resp.json()
        cat_id = created_cat["id"]
        print(f"   [PASS] Kategoriya yaratildi (POST). ID: {cat_id}")

        # Update category
        cat_update_data = {"name": "Test Kategoriya Tahrir", "slug": "test-kategoriya-tahrir", "icon_url": "https://example.com/icon-edited.png"}
        cat_update_resp = client.put(f"/api/v1/admin/categories/{cat_id}", json=cat_update_data, headers=headers)
        assert cat_update_resp.status_code == 200, f"Kategoriyani tahrirlashda xatolik: {cat_update_resp.text}"
        print(f"   [PASS] Kategoriya tahrirlandi (PUT).")

        # Delete category
        cat_delete_resp = client.delete(f"/api/v1/admin/categories/{cat_id}", headers=headers)
        assert cat_delete_resp.status_code == 204, f"Kategoriyani o'chirishda xatolik: {cat_delete_resp.text}"
        print(f"   [PASS] Kategoriya o'chirildi (DELETE).")

        # 5. Test Region CRUD
        print("\n5. Hududlar boshqaruvi test qilinmoqda...")
        # Create region
        region_data = {"name": "Test Viloyati"}
        region_create_resp = client.post("/api/v1/admin/regions/", json=region_data, headers=headers)
        assert region_create_resp.status_code == 201, f"Hudud yaratishda xatolik: {region_create_resp.text}"
        created_region = region_create_resp.json()
        region_id = created_region["id"]
        print(f"   [PASS] Hudud yaratildi (POST). ID: {region_id}")

        # Update region
        region_update_data = {"name": "Test Viloyati Tahrir"}
        region_update_resp = client.put(f"/api/v1/admin/regions/{region_id}", json=region_update_data, headers=headers)
        assert region_update_resp.status_code == 200, f"Hududni tahrirlashda xatolik: {region_update_resp.text}"
        print(f"   [PASS] Hudud tahrirlandi (PUT).")

        # Delete region
        region_delete_resp = client.delete(f"/api/v1/admin/regions/{region_id}", headers=headers)
        assert region_delete_resp.status_code == 204, f"Hududni o'chirishda xatolik: {region_delete_resp.text}"
        print(f"   [PASS] Hudud o'chirildi (DELETE).")

        # 6. List all advertisements for moderation
        print("\n6. E'lonlar moderatsiyasi test qilinmoqda (GET /api/v1/admin/ads/)...")
        ads_response = client.get("/api/v1/admin/ads/", headers=headers)
        assert ads_response.status_code == 200, f"E'lonlarni olishda xatolik: {ads_response.text}"
        print(f"   [PASS] Barcha e'lonlar ro'yxati olindi (Moderatsiya uchun). Soni: {len(ads_response.json())} ta.")

        print("\n=== Barcha admin integratsion testlari muvaffaqiyatli yakunlandi! [ALL PASSED] ===")
    finally:
        client.__exit__(None, None, None)

if __name__ == "__main__":
    run_admin_tests()
