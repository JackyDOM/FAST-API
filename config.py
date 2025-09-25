import os

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
