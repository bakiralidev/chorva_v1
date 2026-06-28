"""
Admin panel UI matni uchun tarjimalar lug'ati.
Barcha qo'llab-quvvatlanadigan tillar: uz, ru, en, tr
"""

ADMIN_TRANSLATIONS: dict[str, dict[str, str]] = {
    "uz": {
        # Layout
        "logout": "Chiqish",
        "language": "Til",
        "lang_uz": "O'zbekcha",
        "lang_ru": "Русский",
        "lang_en": "English",
        "lang_tr": "Türkçe",

        # List page
        "actions": "Amallar",
        "export": "Eksport",
        "search": "Qidirish",
        "search_placeholder": "Qidirish...",
        "filters": "Filtrlar",
        "delete_selected": "Tanlanganlarni o'chirish",
        "showing": "Ko'rsatilmoqda",
        "to": "dan",
        "of": "/",
        "items": "ta yozuv",
        "prev": "Oldingi",
        "next": "Keyingi",
        "per_page": "sahifada",
        "select_all": "Hammasini tanlash",
        "view": "Ko'rish",
        "edit": "Tahrirlash",
        "delete": "O'chirish",

        # Create / Edit page
        "new": "Yangi",
        "edit_title": "Tahrirlash",
        "save": "Saqlash",
        "save_and_continue": "Saqlash va davom etish",
        "save_and_add": "Saqlash va yangi qo'shish",
        "save_as_new": "Yangi sifatida saqlash",
        "cancel": "Bekor qilish",

        # Details page
        "column": "Ustun",
        "value": "Qiymat",
        "go_back": "Orqaga",

        # Login page
        "login_title": "Tizimga kirish",
        "username": "Foydalanuvchi nomi",
        "username_placeholder": "Email yoki telefon",
        "password": "Parol",
        "password_placeholder": "Parolingizni kiriting",
        "login_btn": "Kirish",
        "invalid_credentials": "Login yoki parol noto'g'ri",

        # Model names
        "user": "Foydalanuvchi",
        "users": "Foydalanuvchilar",
        "category": "Kategoriya",
        "categories": "Kategoriyalar",
        "region": "Hudud",
        "regions": "Hududlar",
        "advertisement": "E'lon",
        "advertisements": "E'lonlar",
        "image": "Rasm",
        "images": "Rasmlar",

        # Column labels
        "col_id": "ID",
        "col_email": "Email",
        "col_phone": "Telefon raqami",
        "col_is_active": "Faol",
        "col_is_superuser": "Super-foydalanuvchi",
        "col_created_at": "Yaratilgan sana",
        "col_name": "Nomi",
        "col_slug": "Slug",
        "col_icon": "Belgi (Icon)",
        "col_title": "Sarlavha",
        "col_price": "Narx",
        "col_status": "Holati",
        "col_views": "Ko'rishlar",
        "col_is_top": "Top e'lon",
        "col_image_url": "Rasm URL",
        "col_is_main": "Asosiy rasm",
        "col_ad_id": "E'lon ID",
        "col_accepted_offer": "Ofertani qabul qilgan",
        "filter_accepted_offer": "Ofertani qabul qilganlar",

        # Filter labels
        "filter_status": "Holati",
        "filter_is_top": "Top e'lon",
        "filter_category": "Kategoriya",
        "filter_region": "Hudud",
        "filter_all": "Barchasi",
        "filter_active": "Faol",
        "filter_sold": "Sotilgan",
        "filter_inactive": "Faol emas",
    },

    "ru": {
        # Layout
        "logout": "Выйти",
        "language": "Язык",
        "lang_uz": "O'zbekcha",
        "lang_ru": "Русский",
        "lang_en": "English",
        "lang_tr": "Türkçe",

        # List page
        "actions": "Действия",
        "export": "Экспорт",
        "search": "Поиск",
        "search_placeholder": "Поиск...",
        "filters": "Фильтры",
        "delete_selected": "Удалить выбранные",
        "showing": "Показано",
        "to": "до",
        "of": "из",
        "items": "записей",
        "prev": "Назад",
        "next": "Вперёд",
        "per_page": "на стр.",
        "select_all": "Выбрать всё",
        "view": "Просмотр",
        "edit": "Редактировать",
        "delete": "Удалить",

        # Create / Edit page
        "new": "Новый",
        "edit_title": "Редактирование",
        "save": "Сохранить",
        "save_and_continue": "Сохранить и продолжить",
        "save_and_add": "Сохранить и добавить",
        "save_as_new": "Сохранить как новый",
        "cancel": "Отмена",

        # Details page
        "column": "Поле",
        "value": "Значение",
        "go_back": "Назад",

        # Login page
        "login_title": "Вход в систему",
        "username": "Имя пользователя",
        "username_placeholder": "Email или телефон",
        "password": "Пароль",
        "password_placeholder": "Введите пароль",
        "login_btn": "Войти",
        "invalid_credentials": "Неверный логин или пароль",

        # Model names
        "user": "Пользователь",
        "users": "Пользователи",
        "category": "Категория",
        "categories": "Категории",
        "region": "Регион",
        "regions": "Регионы",
        "advertisement": "Объявление",
        "advertisements": "Объявления",
        "image": "Изображение",
        "images": "Изображения",

        # Column labels
        "col_id": "ID",
        "col_email": "Email",
        "col_phone": "Номер телефона",
        "col_is_active": "Активен",
        "col_is_superuser": "Суперпользователь",
        "col_created_at": "Дата создания",
        "col_name": "Название",
        "col_slug": "Slug",
        "col_icon": "Иконка",
        "col_title": "Заголовок",
        "col_price": "Цена",
        "col_status": "Статус",
        "col_views": "Просмотры",
        "col_is_top": "Топ объявление",
        "col_image_url": "URL изображения",
        "col_is_main": "Главное фото",
        "col_ad_id": "ID объявления",
        "col_accepted_offer": "Принял оферту",
        "filter_accepted_offer": "Принявшие оферту",

        # Filter labels
        "filter_status": "Статус",
        "filter_is_top": "Топ объявление",
        "filter_category": "Категория",
        "filter_region": "Регион",
        "filter_all": "Все",
        "filter_active": "Активные",
        "filter_sold": "Продано",
        "filter_inactive": "Неактивные",
    },

    "en": {
        # Layout
        "logout": "Logout",
        "language": "Language",
        "lang_uz": "O'zbekcha",
        "lang_ru": "Русский",
        "lang_en": "English",
        "lang_tr": "Türkçe",

        # List page
        "actions": "Actions",
        "export": "Export",
        "search": "Search",
        "search_placeholder": "Search...",
        "filters": "Filters",
        "delete_selected": "Delete selected",
        "showing": "Showing",
        "to": "to",
        "of": "of",
        "items": "items",
        "prev": "Previous",
        "next": "Next",
        "per_page": "/ Page",
        "select_all": "Select all",
        "view": "View",
        "edit": "Edit",
        "delete": "Delete",

        # Create / Edit page
        "new": "New",
        "edit_title": "Edit",
        "save": "Save",
        "save_and_continue": "Save and continue editing",
        "save_and_add": "Save and add another",
        "save_as_new": "Save as new",
        "cancel": "Cancel",

        # Details page
        "column": "Column",
        "value": "Value",
        "go_back": "Go Back",

        # Login page
        "login_title": "Sign in",
        "username": "Username",
        "username_placeholder": "Email or phone",
        "password": "Password",
        "password_placeholder": "Enter your password",
        "login_btn": "Login",
        "invalid_credentials": "Invalid username or password",

        # Model names
        "user": "User",
        "users": "Users",
        "category": "Category",
        "categories": "Categories",
        "region": "Region",
        "regions": "Regions",
        "advertisement": "Advertisement",
        "advertisements": "Advertisements",
        "image": "Image",
        "images": "Images",

        # Column labels
        "col_id": "ID",
        "col_email": "Email",
        "col_phone": "Phone Number",
        "col_is_active": "Active",
        "col_is_superuser": "Superuser",
        "col_created_at": "Created At",
        "col_name": "Name",
        "col_slug": "Slug",
        "col_icon": "Icon",
        "col_title": "Title",
        "col_price": "Price",
        "col_status": "Status",
        "col_views": "Views",
        "col_is_top": "Top Ad",
        "col_image_url": "Image URL",
        "col_is_main": "Main Image",
        "col_ad_id": "Ad ID",
        "col_accepted_offer": "Accepted Offer",
        "filter_accepted_offer": "Accepted Offer Status",

        # Filter labels
        "filter_status": "Status",
        "filter_is_top": "Top Ad",
        "filter_category": "Category",
        "filter_region": "Region",
        "filter_all": "All",
        "filter_active": "Active",
        "filter_sold": "Sold",
        "filter_inactive": "Inactive",
    },

    "tr": {
        # Layout
        "logout": "Çıkış",
        "language": "Dil",
        "lang_uz": "O'zbekcha",
        "lang_ru": "Русский",
        "lang_en": "English",
        "lang_tr": "Türkçe",

        # List page
        "actions": "İşlemler",
        "export": "Dışa Aktar",
        "search": "Ara",
        "search_placeholder": "Ara...",
        "filters": "Filtreler",
        "delete_selected": "Seçilenleri sil",
        "showing": "Gösterilen",
        "to": "-",
        "of": "/",
        "items": "kayıt",
        "prev": "Önceki",
        "next": "Sonraki",
        "per_page": "/ Sayfa",
        "select_all": "Tümünü seç",
        "view": "Görüntüle",
        "edit": "Düzenle",
        "delete": "Sil",

        # Create / Edit page
        "new": "Yeni",
        "edit_title": "Düzenle",
        "save": "Kaydet",
        "save_and_continue": "Kaydet ve düzenlemeye devam et",
        "save_and_add": "Kaydet ve yeni ekle",
        "save_as_new": "Yeni olarak kaydet",
        "cancel": "İptal",

        # Details page
        "column": "Sütun",
        "value": "Değer",
        "go_back": "Geri Dön",

        # Login page
        "login_title": "Giriş Yap",
        "username": "Kullanıcı Adı",
        "username_placeholder": "Email veya telefon",
        "password": "Şifre",
        "password_placeholder": "Şifrenizi girin",
        "login_btn": "Giriş",
        "invalid_credentials": "Geçersiz kullanıcı adı veya şifre",

        # Model names
        "user": "Kullanıcı",
        "users": "Kullanıcılar",
        "category": "Kategori",
        "categories": "Kategoriler",
        "region": "Bölge",
        "regions": "Bölgeler",
        "advertisement": "İlan",
        "advertisements": "İlanlar",
        "image": "Resim",
        "images": "Resimler",

        # Column labels
        "col_id": "ID",
        "col_email": "Email",
        "col_phone": "Telefon Numarası",
        "col_is_active": "Aktif",
        "col_is_superuser": "Süper kullanıcı",
        "col_created_at": "Oluşturma Tarihi",
        "col_name": "Ad",
        "col_slug": "Slug",
        "col_icon": "İkon",
        "col_title": "Başlık",
        "col_price": "Fiyat",
        "col_status": "Durum",
        "col_views": "Görüntülemeler",
        "col_is_top": "Öne Çıkan İlan",
        "col_image_url": "Resim URL",
        "col_is_main": "Ana Fotoğraf",
        "col_ad_id": "İlan ID",
        "col_accepted_offer": "Sözleşmeyi Kabul Etti",
        "filter_accepted_offer": "Sözleşmeyi Kabul Edenler",

        # Filter labels
        "filter_status": "Durum",
        "filter_is_top": "Öne Çıkan",
        "filter_category": "Kategori",
        "filter_region": "Bölge",
        "filter_all": "Tümü",
        "filter_active": "Aktif",
        "filter_sold": "Satıldı",
        "filter_inactive": "Pasif",
    },
}


def get_admin_t(lang: str) -> dict[str, str]:
    """Berilgan til uchun tarjima lug'atini qaytaradi. Topilmasa 'uz' ni qaytaradi."""
    return ADMIN_TRANSLATIONS.get(lang, ADMIN_TRANSLATIONS["uz"])
