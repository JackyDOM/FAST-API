from fastapi import FastAPI, Depends, HTTPException, Header, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import sqlite3
import os
import shutil
import httpx

# ---------------------------
# Configuration
# ---------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

KEYCLOAK_SERVER_URL = "http://localhost:8081"
REALM = "myrealm"
KEYCLOAK_CLIENT_ID = "fastapi-client"
KEYCLOAK_CLIENT_SECRET = "70lIri8vmq0xXLvR5FnASqUOOQhJjWGf"
KEYCLOAK_ADMIN_USER = "admin"
KEYCLOAK_ADMIN_PASSWORD = "admin"

DB_FILE = "database.db"

# ---------------------------
# Models
# ---------------------------
class VillageResponse(BaseModel):
    id: int
    user_id: str
    name_kh: str
    name_en: str
    age: int
    gender: str
    dob: str
    image_path: Optional[str]

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    email: str

# ---------------------------
# Database helpers
# ---------------------------
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
# FastAPI app
# ---------------------------
app = FastAPI(title="Village API with Keycloak", version="1.0.0", lifespan=lifespan)

# ---------------------------
# Global exception handler
# ---------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": str(exc), "data": None}
    )

# ---------------------------
# Keycloak helpers
# ---------------------------
def get_admin_token():
    url = f"{KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": KEYCLOAK_ADMIN_USER,
        "password": KEYCLOAK_ADMIN_PASSWORD
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = httpx.post(url, data=data, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Admin login failed: {response.text}")
    return response.json()["access_token"]

def register_user(username: str, email: str, password: str):
    token = get_admin_token()
    url = f"{KEYCLOAK_SERVER_URL}/admin/realms/{REALM}/users"
    data = {
        "username": username,
        "email": email,
        "enabled": True,
        "emailVerified": True,
        "credentials": [],
        "requiredActions": []
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = httpx.post(url, json=data, headers=headers)
    if response.status_code not in (201, 204):
        raise HTTPException(status_code=response.status_code, detail=f"User creation failed: {response.text}")

    users = httpx.get(f"{KEYCLOAK_SERVER_URL}/admin/realms/{REALM}/users?username={username}", headers=headers).json()
    if not users:
        raise HTTPException(status_code=500, detail="Failed to fetch newly created user")
    user_id = users[0]["id"]

    pwd_url = f"{KEYCLOAK_SERVER_URL}/admin/realms/{REALM}/users/{user_id}/reset-password"
    pwd_data = {"type": "password", "value": password, "temporary": False}
    httpx.put(pwd_url, json=pwd_data, headers=headers)

    return {"error": False, "message": "User registered successfully", "data": {"username": username, "user_id": user_id}}

def login_user(username: str, email: str):
    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}

    users = httpx.get(f"{KEYCLOAK_SERVER_URL}/admin/realms/{REALM}/users?username={username}", headers=headers).json()
    if not users or users[0]["email"] != email:
        raise HTTPException(status_code=401, detail="Invalid username or email")

    user_id = users[0]["id"]

    # Get Keycloak access token for user (passwordless login is not secure; here just demo)
    # For real login you would normally also verify password, or send a temp code
    token_url = f"{KEYCLOAK_SERVER_URL}/realms/{REALM}/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": KEYCLOAK_CLIENT_ID,
        "client_secret": KEYCLOAK_CLIENT_SECRET,
        "username": username,
        "password": "user-known-password"  # Replace with actual password
    }
    # For demo, we'll just return the user ID as "token"
    token = f"{user_id}-keycloak-token-placeholder"

    return {"error": False, "message": "success", "token": token}

def get_current_user(token: str = Header(...)):
    # For demo, just return user_id from token
    user_id = token.replace("-keycloak-token-placeholder", "")
    return {"sub": user_id}

# ---------------------------
# Auth routes
# ---------------------------
@app.post("/register")
async def register(request: RegisterRequest):
    return register_user(request.username, request.email, request.password)

@app.post("/login")
async def login(request: LoginRequest):
    return login_user(request.username, request.email)

@app.get("/users")
async def get_all_users():
    """
    Get all users from Keycloak (no pagination in request).
    """
    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Force Keycloak to return "all" by setting max to a large number
    url = f"{KEYCLOAK_SERVER_URL}/admin/realms/{REALM}/users?first=0&max=9999"

    response = httpx.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch users: {response.text}")

    return {
        "error": False,
        "message": "success",
        "data": response.json()
    }



@app.delete("/user/{user_id}")
async def delete_user_by_id(user_id: str):
    """
    Delete a user by their Keycloak user_id.
    Requires admin token.
    """
    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}
    url = f"{KEYCLOAK_SERVER_URL}/admin/realms/{REALM}/users/{user_id}"

    response = httpx.delete(url, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=f"Failed to delete user: {response.text}")

    return {"error": False, "message": f"User {user_id} deleted successfully"}


# ---------------------------
# Village routes
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
    return {"error": False, "message": f"Village with id {village_id} deleted successfully", "data": None}

# ---------------------------
# Run server
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
