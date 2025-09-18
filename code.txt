from fastapi import FastAPI, Depends, HTTPException, status, Header, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta
from contextlib import asynccontextmanager
import sqlite3
from auth import get_password_hash, authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, DB_FILE, ALGORITHM, SECRET_KEY
from jose import jwt, JWTError
import os
import shutil

# ---------------------------
# Configuration for image storage
# ---------------------------
UPLOAD_DIR = "uploads"  # Directory to store images
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create uploads directory if it doesn't exist

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
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """)
    
    # Create villages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS villages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name_kh TEXT,
            name_en TEXT,
            age INTEGER,
            gender TEXT,
            dob TEXT,
            image_path TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Check if image_path column exists and add it if not
    cursor.execute("PRAGMA table_info(villages)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'image_path' not in columns:
        cursor.execute("ALTER TABLE villages ADD COLUMN image_path TEXT")
    
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

@app.get("/village")
async def get_all_villages(user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Dict-like rows
    villages = conn.execute("SELECT * FROM villages WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()

    # Convert all rows to dict
    data = [dict(village) for village in villages]

    return {
        "error": "false",
        "message": "Success",
        "data": data
    }

@app.post("/village")
async def create_village(
    name_kh: str = Form(...),
    name_en: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    dob: str = Form(...),
    image: Optional[UploadFile] = File(None),
    user_id: int = Depends(get_current_user)
):
    # Create VillageCreate object from form data
    village = VillageCreate(name_kh=name_kh, name_en=name_en, age=age, gender=gender, dob=dob)

    # Validate image type if provided
    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Ensure dict-like rows

    # Save image to filesystem if provided
    image_path = None
    if image:
        image_filename = f"{user_id}_{village.name_en}_{image.filename}"
        image_path = os.path.join(UPLOAD_DIR, image_filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    # Insert village data into database
    cursor = conn.execute("""
        INSERT INTO villages (user_id, name_kh, name_en, age, gender, dob, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, village.name_kh, village.name_en, village.age, village.gender, village.dob, image_path))
    conn.commit()
    village_id = cursor.lastrowid
    result = conn.execute("SELECT * FROM villages WHERE id = ?", (village_id,)).fetchone()
    conn.close()

    return {
        "error": "false",
        "message": "Success",
        "data": dict(result)
    }

@app.delete("/village/{village_id}")
async def delete_village(village_id: int, user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    # Check if village exists and belongs to user
    village = conn.execute("SELECT * FROM villages WHERE id = ?", (village_id,)).fetchone()
    if not village:
        conn.close()
        raise HTTPException(status_code=404, detail="Village not found")

    if village["user_id"] != user_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized to delete this village")

    # Delete the image file if it exists
    if village["image_path"]:
        try:
            os.remove(village["image_path"])
        except FileNotFoundError:
            pass  # Ignore if file doesn't exist

    # Delete the village
    conn.execute("DELETE FROM villages WHERE id = ?", (village_id,))
    conn.commit()
    conn.close()

    return {
        "error": "false",
        "message": f"Village with id {village_id} deleted successfully",
        "data": None
    }

# ---------------------------
# Run server
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)