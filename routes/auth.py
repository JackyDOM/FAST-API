from fastapi import APIRouter, HTTPException
from models import RegisterRequest, LoginRequest
from keycloak_utils import register_user, login_user, get_admin_token
import httpx
from config import REALM, KEYCLOAK_SERVER_URL

router = APIRouter()

@router.post("/register")
async def register(request: RegisterRequest):
    return register_user(request.username, request.email, request.password)

@router.post("/login")
async def login(request: LoginRequest):
    return login_user(request.username, request.email)

@router.get("/users")
async def get_all_users():
    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}
    url = f"{KEYCLOAK_SERVER_URL}/admin/realms/{REALM}/users?first=0&max=9999"
    response = httpx.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch users: {response.text}")
    return {"error": False, "message": "success", "data": response.json()}

@router.delete("/user/{user_id}")
async def delete_user_by_id(user_id: str):
    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}
    url = f"{KEYCLOAK_SERVER_URL}/admin/realms/{REALM}/users/{user_id}"
    response = httpx.delete(url, headers=headers)
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=f"Failed to delete user: {response.text}")
    return {"error": False, "message": f"User {user_id} deleted successfully"}
