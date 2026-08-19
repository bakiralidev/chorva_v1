"""
audit_db.py - Database audit va bakiralizokirov@gmail.com ni topish
"""
import sqlite3

TARGET_EMAIL = "bakiralizokirov@gmail.com"

conn = sqlite3.connect("test.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Barcha tablelarni ko'rsatish
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("=== TABLES ===")
for t in tables:
    print(" ", t[0])

# Users
print()
print("=== ALL USERS ===")
cur.execute("SELECT id, email, phone_number, auth_provider, is_active, is_verified, google_id FROM users")
users = cur.fetchall()
target_user_id = None
for u in users:
    gid = str(u["google_id"])[:20] if u["google_id"] else None
    is_target = u["email"] == TARGET_EMAIL
    marker = " <-- TARGET" if is_target else ""
    print(f"  id={u['id'][:8]}... email={u['email']} phone={u['phone_number']} "
          f"provider={u['auth_provider']} active={u['is_active']} "
          f"verified={u['is_verified']} google_id={gid}{marker}")
    if is_target:
        target_user_id = u["id"]

print()
print(f"Target user ID: {target_user_id}")

# Verification codes
print()
print("=== VERIFICATION CODES ===")
cur.execute("SELECT id, user_id, expires_at FROM verification_codes")
vcodes = cur.fetchall()
for v in vcodes:
    marker = " <-- TARGET USER" if target_user_id and v["user_id"] == target_user_id else ""
    print(f"  user_id={v['user_id'][:8]}... expires={v['expires_at']}{marker}")

# Refresh tokens
print()
print("=== REFRESH TOKENS ===")
cur.execute("SELECT id, user_id, is_revoked, expires_at FROM refresh_tokens")
rtokens = cur.fetchall()
for r in rtokens:
    marker = " <-- TARGET USER" if target_user_id and r["user_id"] == target_user_id else ""
    print(f"  user_id={r['user_id'][:8]}... revoked={r['is_revoked']} expires={r['expires_at']}{marker}")

conn.close()
