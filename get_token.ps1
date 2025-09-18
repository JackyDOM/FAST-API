# Replace these values with your Keycloak setup
$client_id     = "fastapi-client"
$client_secret = "nPjrfiNNyUZAdJIANHyMPKEXEjdPl3vU"
$username      = "testuser"
$password      = "test123"

# Body for the token request
$body = @{
    client_id     = $client_id
    client_secret = $client_secret
    grant_type    = "password"
    username      = $username
    password      = $password
}

# Token endpoint
$token_url = "http://localhost:8081/realms/myrealm/protocol/openid-connect/token"

# Request token
$response = Invoke-RestMethod -Method Post -Uri $token_url -Body $body -ContentType "application/x-www-form-urlencoded"

# Output the access token
$response.access_token
