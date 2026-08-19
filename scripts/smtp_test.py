"""
smtp_test.py - Gmail SMTP ulanishini va boshqa emailga yuborishni test qilish
"""
import asyncio
import sys

async def test_smtp(target_email: str):
    """Gmail SMTP orqali berilgan emailga test xabar yuboradi."""
    import aiosmtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    # .env dan o'qish
    import os
    from dotenv import load_dotenv
    load_dotenv()

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    from_name = os.getenv("SMTP_FROM_NAME", "Chorva.uz")

    print(f"SMTP Host    : {smtp_host}:{smtp_port}")
    print(f"SMTP Username: {smtp_user}")
    print(f"SMTP Password: {'*' * len(smtp_pass) if smtp_pass else 'EMPTY!'}")
    print(f"From Name    : {from_name}")
    print(f"To Email     : {target_email}")
    print()

    if not smtp_user or not smtp_pass:
        print("ERROR: SMTP_USERNAME yoki SMTP_PASSWORD bo'sh!")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Test OTP: 999888"
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = target_email
    msg.attach(MIMEText("Test OTP kodi: 999888. Bu test xabari.", "plain", "utf-8"))

    try:
        print("Ulanish sinab ko'rilmoqda...")
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_pass,
            start_tls=True,
        )
        print(f"SUCCESS: Email yuborildi -> {target_email}")
    except aiosmtplib.SMTPAuthenticationError as e:
        print(f"AUTH ERROR: Gmail App Password noto'g'ri yoki 2FA yoqilmagan: {e}")
    except aiosmtplib.SMTPConnectError as e:
        print(f"CONNECT ERROR: SMTP serverga ulanib bo'lmadi: {e}")
    except Exception as e:
        print(f"GENERAL ERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    asyncio.run(test_smtp(email))
