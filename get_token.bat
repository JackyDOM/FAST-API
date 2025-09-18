@echo off
curl.exe -X POST "http://localhost:8081/realms/myrealm/protocol/openid-connect/token" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "client_id=fastapi-client" ^
  -d "client_secret=70lIri8vmq0xXLvR5FnASqUOOQhJjWGf" ^
  -d "grant_type=password" ^
  -d "username=testuser" ^
  -d "password=test123"
pause
