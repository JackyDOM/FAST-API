# from pydantic import BaseModel
# from typing import Optional, List

# class VillageResponse(BaseModel):
#     id: int
#     user_id: str
#     name_kh: str
#     name_en: str
#     age: int
#     gender: str
#     dob: str
#     image_path: Optional[str]

# class RegisterRequest(BaseModel):
#     username: str
#     email: str
#     password: str

# class LoginRequest(BaseModel):
#     username: str
#     email: str


from pydantic import BaseModel
from typing import Optional

# Response model for Village
class VillageResponse(BaseModel):
    id: int
    user_id: str
    name_kh: str
    name_en: str
    age: int
    gender: str
    dob: str
    image_path: Optional[str]

    class Config:
        orm_mode = True  # <-- critical for SQLAlchemy integration

# Request model for registering a user
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

# Request model for logging in a user
class LoginRequest(BaseModel):
    username: str
    email: str
