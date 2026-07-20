"""
email_service.py — Gmail SMTP orqali OTP va boshqa xabarlar yuborish.

Gmail App Password ni olish tartibi:
1. Google akkauntingizga kiring: myaccount.google.com
2. "Xavfsizlik" (Security) bo'limiga o'ting
3. "2 bosqichli tekshiruv"ni yoqing (agar yoqilmagan bo'lsa)
4. "Ilovalar paroli" (App passwords) bo'limini toping
5. "Ilova tanlash" → "Boshqa (maxsus nom)" → "Chorva" → "Yaratish"
6. Ko'rsatilgan 16 ta belgidan iborat parolni .env ga SMTP_PASSWORD ga kiriting

Misol:
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  (bo'shliqsiz)
"""
import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings

logger = logging.getLogger("app.email")


def _build_otp_html(otp_code: str, recipient_email: str) -> str:
    """OTP uchun chiroyli HTML email template."""
    return f"""
<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tasdiqlash kodi — Chorva.uz</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="520" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td style="background:#2563eb;padding:28px 40px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-size:24px;letter-spacing:1px;">🐄 Chorva.uz</h1>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <h2 style="margin:0 0 12px;color:#1e293b;font-size:20px;">Tasdiqlash kodi</h2>
              <p style="margin:0 0 24px;color:#475569;font-size:15px;line-height:1.6;">
                Salom! Chorva.uz ro'yxatdan o'tishni tasdiqlash uchun quyidagi
                <strong>6 xonali kodni</strong> kiriting:
              </p>
              <!-- OTP Code Box -->
              <div style="background:#f1f5f9;border:2px dashed #2563eb;border-radius:10px;
                          padding:24px;text-align:center;margin-bottom:24px;">
                <span style="font-size:42px;font-weight:bold;color:#2563eb;
                             letter-spacing:10px;font-family:monospace;">{otp_code}</span>
              </div>
              <p style="margin:0 0 8px;color:#64748b;font-size:13px;">
                ⏱ Bu kod <strong>5 daqiqa</strong> ichida amal qiladi.
              </p>
              <p style="margin:0;color:#64748b;font-size:13px;">
                🚫 Ushbu kodni hech kimga bermang. Chorva.uz xodimlari kodni so'ramaydi.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#f8fafc;padding:20px 40px;text-align:center;
                       border-top:1px solid #e2e8f0;">
              <p style="margin:0;color:#94a3b8;font-size:12px;">
                Bu xabar <strong>{recipient_email}</strong> manziliga yuborildi.<br>
                &copy; 2024 Chorva.uz — Barcha huquqlar himoyalangan.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


async def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Gmail SMTP orqali OTP kodi yuboradi.

    Args:
        to_email: Qabul qiluvchi email manzili
        otp_code: 6 xonali OTP kodi

    Returns:
        True — yuborildi, False — xatolik yuz berdi
    """
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning("SMTP sozlanmagan — email yuborilmadi (console ga chiqarildi)")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔐 Chorva.uz — Tasdiqlash kodi: {otp_code}"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USERNAME}>"
        msg["To"] = to_email

        # Plain text fallback
        plain_text = (
            f"Chorva.uz tasdiqlash kodi: {otp_code}\n"
            f"Bu kod 5 daqiqa ichida amal qiladi.\n"
            f"Kodni hech kimga bermang!"
        )
        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(_build_otp_html(otp_code, to_email), "html", "utf-8"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("OTP email yuborildi: to=%s", to_email)
        return True

    except Exception as e:
        logger.error("Email yuborishda xatolik: to=%s error=%s", to_email, str(e))
        return False
