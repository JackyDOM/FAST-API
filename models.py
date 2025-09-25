from pydantic import BaseModel
from typing import Optional, List

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
