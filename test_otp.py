"""
test_otp.py - OTP yuborish ishlayotganini test qilish
"""
import sys, asyncio
sys.path.insert(0, '.')

async def test():
    from app.database import AsyncSessionLocal
    from app.models.telegram_link import TelegramLink
    from app.utils.telegram.otp import send_otp_via_telegram
    from sqlalchemy.future import select
    
    async with AsyncSessionLocal() as db:
        # 1. Bazadagi TelegramLink larni ko'rsatish
        result = await db.execute(select(TelegramLink))
        links = result.scalars().all()
        print(f"\nBazadagi TelegramLink lar ({len(links)} ta):")
        for l in links:
            print(f"  phone={l.phone_number}  chat_id={l.chat_id}")
        
        if not links:
            print("  XATO: Hech qanday TelegramLink yo'q!")
            return
        
        # 2. Birinchisiga OTP yuborib ko'rish
        link = links[0]
        print(f"\nTest OTP yuborilmoqda: chat_id={link.chat_id}...")
        sent = await send_otp_via_telegram(link.chat_id, "123456", link.phone_number)
        print(f"Natija: {'YUBORILDI!' if sent else 'XATO!'}")

asyncio.run(test())
