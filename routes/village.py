from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
import sqlite3, os, shutil
from config import DB_FILE, UPLOAD_DIR
from models import VillageResponse
from keycloak_utils import get_current_user
from typing import Optional, List

router = APIRouter()

@router.get("/village", response_model=List[VillageResponse])
async def get_all_villages(user: dict = Depends(get_current_user)):
    user_id = user["sub"]
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    villages = conn.execute("SELECT * FROM villages WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return [dict(v) for v in villages]

@router.post("/village", response_model=VillageResponse)
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

@router.delete("/village/{village_id}")
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
