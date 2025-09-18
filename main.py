from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta
from contextlib import asynccontextmanager
import sqlite3
from auth import get_password_hash, authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, DB_FILE, ALGORITHM, SECRET_KEY
from jose import jwt, JWTError

# ---------------------------
# Models
# ---------------------------
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    error: str  # "true" or "false"
    message: str
    token: Optional[str] = None

class VillageCreate(BaseModel):
    name_kh: str
    name_en: str
    age: int
    gender: str
    dob: str  # YYYY-MM-DD

# ---------------------------
# Database helpers
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS villages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name_kh TEXT,
            name_en TEXT,
            age INTEGER,
            gender TEXT,
            dob TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

# ---------------------------
# App instance
# ---------------------------
app = FastAPI(
    title="Authentication & Village API",
    description="API with JWT-based authentication and simple Bearer token for /village",
    version="1.0.0",
    lifespan=lifespan
)

# ---------------------------
# Custom Bearer token dependency
# ---------------------------
def get_current_user(token: str = Header(..., description="Enter JWT token as 'Bearer <token>'")):
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    actual_token = token[len("Bearer "):]
    try:
        payload = jwt.decode(actual_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# ---------------------------
# Exception handler
# ---------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "true", "message": "Fail", "data": None}
    )

# ---------------------------
# Routes
# ---------------------------
@app.post("/register", response_model=TokenResponse)
async def register(user: UserCreate):
    conn = sqlite3.connect(DB_FILE)
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (user.username,)).fetchone()
    if existing:
        conn.close()
        return TokenResponse(error="true", message="Username already exists", token=None)

    hashed_password = get_password_hash(user.password)
    cursor = conn.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)",
                          (user.username, hashed_password))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user_id)}, expires_delta=access_token_expires)

    return TokenResponse(error="false", message="User registered successfully", token=access_token)

@app.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    user_id = authenticate_user(user.username, user.password)
    if not user_id:
        return TokenResponse(error="true", message="Invalid username or password", token=None)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user_id)}, expires_delta=access_token_expires)

    return TokenResponse(error="false", message="Login success", token=access_token)

@app.post("/village")
async def create_village(village: VillageCreate, user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # <-- ensure dict-like rows
    cursor = conn.execute("""
        INSERT INTO villages (user_id, name_kh, name_en, age, gender, dob)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, village.name_kh, village.name_en, village.age, village.gender, village.dob))
    conn.commit()
    village_id = cursor.lastrowid
    result = conn.execute("SELECT * FROM villages WHERE id = ?", (village_id,)).fetchone()
    conn.close()

    return {
        "error": "false",
        "message": "Success",
        "data": dict(result)
    }

# ---------------------------
# Run server
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
