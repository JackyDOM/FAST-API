import sqlite3
from contextlib import asynccontextmanager
from config import DB_FILE

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS villages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name_kh TEXT,
            name_en TEXT,
            age INTEGER,
            gender TEXT,
            dob TEXT,
            image_path TEXT
        )
    """)
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield
