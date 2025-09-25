import os

# Upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Keycloak config
KEYCLOAK_SERVER_URL = "http://localhost:8081"
REALM = "myrealm"
KEYCLOAK_CLIENT_ID = "fastapi-client"
KEYCLOAK_CLIENT_SECRET = "70lIri8vmq0xXLvR5FnASqUOOQhJjWGf"
KEYCLOAK_ADMIN_USER = "admin"
KEYCLOAK_ADMIN_PASSWORD = "admin"

# PostgreSQL config
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "12345"
POSTGRES_DB = "FastAPI"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
