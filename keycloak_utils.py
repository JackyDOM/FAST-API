import httpx
from fastapi import HTTPException, Header
from config import (
    KEYCLOAK_SERVER_URL, REALM, KEYCLOAK_CLIENT_ID,
    KEYCLOAK_CLIENT_SECRET, KEYCLOAK_ADMIN_USER, KEYCLOAK_ADMIN_PASSWORD
)

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
    token = f"{user_id}-keycloak-token-placeholder"
    return {"error": False, "message": "success", "token": token}

def get_current_user(token: str = Header(...)):
    user_id = token.replace("-keycloak-token-placeholder", "")
    return {"sub": user_id}
