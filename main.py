from fastapi import FastAPI, Depends, HTTPException, status, Header, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import sqlite3
import os
import shutil
import httpx
from jose import jwt, JWTError

# ---------------------------
# Configuration for image storage
# ---------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------
# Keycloak Configuration
# ---------------------------
KEYCLOAK_SERVER_URL = "http://localhost:8080/auth/"
KEYCLOAK_REALM = "myrealm"
KEYCLOAK_CLIENT_ID = "fastapi-client"
KEYCLOAK_PUBLIC_KEY = None  # will be fetched

def get_keycloak_public_key():
    global KEYCLOAK_PUBLIC_KEY
    if KEYCLOAK_PUBLIC_KEY:
        return KEYCLOAK_PUBLIC_KEY

    url = f"{KEYCLOAK_SERVER_URL}realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
    try:
        with httpx.Client() as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Keycloak connection error: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Keycloak returned error: {str(e)}")

    # Using the first key (production: handle kid properly)
    x5c = data['keys'][0]['x5c'][0]
    KEYCLOAK_PUBLIC_KEY = f"-----BEGIN CERTIFICATE-----\n{x5c}\n-----END CERTIFICATE-----"
    return KEYCLOAK_PUBLIC_KEY

# ---------------------------
# Models
# ---------------------------
class VillageCreate(BaseModel):
    name_kh: str
    name_en: str
    age: int
    gender: str
    dob: str  # YYYY-MM-DD

# ---------------------------
# Database helpers
# ---------------------------
DB_FILE = "users.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create villages table
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
async def lifespan(app: FastAPI):
    init_db()
    yield

# ---------------------------
# App instance
# ---------------------------
app = FastAPI(
    title="Village API with Keycloak",
    version="1.0.0",
    lifespan=lifespan
)

# ---------------------------
# Keycloak Bearer dependency
# ---------------------------
def get_current_user(token: str = Header(..., description="Enter JWT token as 'Bearer <token>'")):
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    actual_token = token[len("Bearer "):]
    try:
        payload = jwt.decode(actual_token, get_keycloak_public_key(), algorithms=["RS256"], audience=KEYCLOAK_CLIENT_ID)
        return payload  # contains 'sub', 'preferred_username', etc.
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Keycloak token")

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
@app.get("/village")
async def get_all_villages(user: dict = Depends(get_current_user)):
    user_id = user["sub"]
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    villages = conn.execute("SELECT * FROM villages WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    data = [dict(village) for village in villages]
    return {"error": "false", "message": "Success", "data": data}

@app.post("/village")
async def create_village(
    name_kh: str = Form(...),
    name_en: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    dob: str = Form(...),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    village = VillageCreate(name_kh=name_kh, name_en=name_en, age=age, gender=gender, dob=dob)
    user_id = user["sub"]

    image_path = None
    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        image_filename = f"{user_id}_{village.name_en}_{image.filename}"
        image_path = os.path.join(UPLOAD_DIR, image_filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("""
        INSERT INTO villages (user_id, name_kh, name_en, age, gender, dob, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, village.name_kh, village.name_en, village.age, village.gender, village.dob, image_path))
    conn.commit()
    village_id = cursor.lastrowid
    result = conn.execute("SELECT * FROM villages WHERE id = ?", (village_id,)).fetchone()
    conn.close()

    return {"error": "false", "message": "Success", "data": dict(result)}

@app.delete("/village/{village_id}")
async def delete_village(village_id: int, user: dict = Depends(get_current_user)):
    user_id = user["sub"]
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    village = conn.execute("SELECT * FROM villages WHERE id = ?", (village_id,)).fetchone()
    if not village:
        conn.close()
        raise HTTPException(status_code=404, detail="Village not found")
    if village["user_id"] != user_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized to delete this village")
    if village["image_path"]:
        try:
            os.remove(village["image_path"])
        except FileNotFoundError:
            pass
    conn.execute("DELETE FROM villages WHERE id = ?", (village_id,))
    conn.commit()
    conn.close()
    return {"error": "false", "message": f"Village with id {village_id} deleted successfully", "data": None}

# ---------------------------
# Run server
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
