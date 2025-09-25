from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from database import SessionLocal, Village
from keycloak_utils import get_current_user
from config import UPLOAD_DIR
import os, shutil
from typing import Optional, List
from models import VillageResponse

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/village")
async def get_all_villages(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        user_id = str(user["sub"])
        villages = db.query(Village).filter(Village.user_id == user_id).all()
        data = [VillageResponse.from_orm(v) for v in villages]

        return {
            "error": False,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"failed: {str(e)}",
            "data": None
        }


@router.post("/village", response_model=dict)
async def create_village(
    name_kh: str = Form(...),
    name_en: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    dob: str = Form(...),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = user["sub"]
    image_path = None

    # Handle image upload
    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        image_filename = f"{user_id}_{name_en}_{image.filename}"
        image_path = os.path.join(UPLOAD_DIR, image_filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    # Create SQLAlchemy Village object
    village = Village(
        user_id=user_id,
        name_kh=name_kh,
        name_en=name_en,
        age=age,
        gender=gender,
        dob=dob,
        image_path=image_path
    )

    # Save to DB
    db.add(village)
    db.commit()
    db.refresh(village)

    # Return custom JSON response
    return {
        "error": False,
        "message": "success",
        "data": VillageResponse.from_orm(village)
    }


@router.delete("/village/{village_id}")
async def delete_village(village_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    village = db.query(Village).filter(Village.id == village_id).first()
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")
    if village.user_id != user["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this village")
    if village.image_path:
        try:
            os.remove(village.image_path)
        except FileNotFoundError:
            pass
    db.delete(village)
    db.commit()
    return {"error": False, "message": f"Village with id {village_id} deleted successfully", "data": None}
