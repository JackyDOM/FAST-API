from fastapi import FastAPI, Depends, HTTPException, status, Header, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import sqlite3
import os
import shutil
import httpx
from jose import jwt, JWTError, jwk

# ---------------------------
# Configuration for image storage
# ---------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------
# Keycloak Configuration
# ---------------------------
KEYCLOAK_SERVER_URL = "http://localhost:8081/realms/myrealm"
KEYCLOAK_CLIENT_ID = "fastapi-client"

def get_keycloak_jwk():
    """Fetch the first JWK from Keycloak JWKS endpoint."""
    url = f"{KEYCLOAK_SERVER_URL}/protocol/openid-connect/certs"
    try:
        with httpx.Client() as client:
            resp = client.get(url)
            resp.raise_for_status()
            jwks = resp.json()
        return jwks['keys'][0]  # take the first key
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keycloak connection error: {str(e)}")

def get_current_user(token: str = Header(...)):
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    actual_token = token[len("Bearer "):]

    jwk_data = get_keycloak_jwk()  # get the JWK from Keycloak
    try:
        payload = jwt.decode(
            actual_token,
            jwk_data,                  # pass the JWK directly
            algorithms=["RS256"],
            audience="account"
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Keycloak token: {str(e)}")

# ---------------------------
# Models
# ---------------------------
class VillageCreate(BaseModel):
    name_kh: str
    name_en: str
    age: int
    gender: str
    dob: str  # YYYY-MM-DD

class VillageResponse(BaseModel):
    id: int
    user_id: str
    name_kh: str
    name_en: str
    age: int
    gender: str
    dob: str
    image_path: Optional[str]

# ---------------------------
# Database helpers
# ---------------------------
DB_FILE = "users.db"

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
# Global exception handler
# ---------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": "true", "message": str(exc), "data": None}
    )

# ---------------------------
# Routes
# ---------------------------
@app.get("/village", response_model=List[VillageResponse])
async def get_all_villages(user: dict = Depends(get_current_user)):
    user_id = user["sub"]
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    villages = conn.execute("SELECT * FROM villages WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return [dict(v) for v in villages]

@app.post("/village", response_model=VillageResponse)
async def create_village(
    name_kh: str = Form(...),
    name_en: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    dob: str = Form(...),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    user_id = user["sub"]

    image_path = None
    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        image_filename = f"{user_id}_{name_en}_{image.filename}"
        image_path = os.path.join(UPLOAD_DIR, image_filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO villages (user_id, name_kh, name_en, age, gender, dob, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name_kh, name_en, age, gender, dob, image_path))
    conn.commit()
    village_id = cursor.lastrowid
    result = conn.execute("SELECT * FROM villages WHERE id = ?", (village_id,)).fetchone()
    conn.close()
    return dict(result)

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
