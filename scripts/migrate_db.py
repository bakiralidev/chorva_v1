import asyncio
import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base
from app.models.offer import Offer, OfferTranslation
from app.models.verification import VerificationCode
from app.models.user import User
from app.models.refresh_token import RefreshToken

async def migrate():
    try:
        conn = sqlite3.connect("chorva.db")
        cursor = conn.cursor()
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass 
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN accepted_offer BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass 
            
        try:
            cursor.execute("ALTER TABLE offers ADD COLUMN has_file BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass 

        try:
            cursor.execute("ALTER TABLE offers ADD COLUMN file_url VARCHAR(255)")
        except sqlite3.OperationalError:
            pass 
            
        conn.commit()
        conn.close()
        print("Updated tables (users, offers) successfully.")
    except Exception as e:
        print(f"Error updating tables: {e}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("New tables (offers, verification_codes) checked/created successfully.")

if __name__ == "__main__":
    asyncio.run(migrate())
