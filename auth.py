from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# DATABASE FILE
DB_FILE = "users.db"

# PASSWORD CONTEXT
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT CONFIG
SECRET_KEY = os.getenv("SECRET_KEY", "secret123")  # default key if not in .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute("SELECT id, hashed_password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return False
    user_id, hashed_password = user
    if not pwd_context.verify(password, hashed_password):
        return False
    return user_id

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
