async def get_list_surveys(db_user: dict) -> dict:
    try:
        # Get user profile from DB
        # SELECT token, user_id_pwd FROM user_profile WHERE user_id = db_user["id"]
        username = db_user.get("username")
        user_profile = db_user.get("user_profile")

        token = None
        user_id_pwd = None

        # Use existing token if available
        if user_profile and user_profile.get("token"):
            logging.info(f"{SERVICE_DMIS_AUTH} - username={username}")
            token = user_profile.get("token")
            user_id_pwd = user_profile.get("user_id_pwd")

        # login to DMIS
        else:
            logging.info(f"{SERVICE_DMIS_AUTH} - No token found, login to DMIS | username={username}")

            login_response = await _get_dmis_token({
                "username": db_user.get("username"),
                "password": db_user.get("password")
            })

            if login_response.get("error"):
                return {"error": True, "message": "Failed to authenticate with DMIS API"}

            token = login_response.get("user", {}).get("token")
            user_id_pwd = login_response.get("user", {}).get("id")

        if not token:
            return {"error": True, "message": "DMIS token is missing"}

        # Call DMIS Survey API
        url = f"{DMIS_API_BASE_URL}/surveys/index"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        body = {
            "user_id": user_id_pwd
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                json=body,
                headers=headers,
                timeout=30
            ) as response:

                dmis_response = await response.json()

                logging.info(
                    f"{SERVICE_DMIS_AUTH} - Survey response | status={response.status}"
                )

                if response.status == 400:
                    return {"error": True, "message": "Request validation failed"}

                if response.status == 404:
                    return {"error": True, "message": "DATA NOT FOUND"}

                return dmis_response

    except Exception as e:
        logging.error(f"{SERVICE_DMIS_AUTH} - Unexpected error | {str(e)}")
        return {"error": True, "message": "Unexpected server error"}

===============================================================================================================


# List Surveys
# async def get_list_surveys(db_user) -> dict:
#     try:
#         # Prepare DMIS login parameters
#         userProfile_params = {
#             "username": db_user.get("username"),
#             "password": db_user.get("password")
#         }

#         # logging.info(
#         #     userProfile_params.get("username"),
#         #     userProfile_params.get("password")
#         # )

#         pwd_token = None

#         # Check
#         # user_profile = select (token, user_id_pwd) from UserProfile where user_id = db_user["id"]

#         if user_profile:
#             pwd_token = user_profile["token"]
#         else:
#             login_response = await _get_dmis_token(userProfile_params)

#             if login_response.get("error"):
#                 return {"error": True, "message": "Failed to authenticate with DMIS API"}
            
#             pwd_token = login_response.get("user", {}).get("token", "")

#         token = pwd_token()  #login_response.get("user", {}).get("token", "")
#         if not token:
#             return {"error": True, "message": "DMIS login did not return token."}

#         body = json.dumps({
#             "user_id": user_profile["user_id_pwd"]
#         })

#         url = f"{DMIS_API_BASE_URL}/surveys/index"
#         headers = {
#             "Authorization": f"Bearer {token}",
#             "Content-Type": "application/json"
#         }

#         async with aiohttp.ClientSession() as session:
#             async with session.get(url, data=body, headers=headers, timeout=30) as response:

#                 dmis_response = await response.json()

#                 if response.status == 400:
#                     return {"error": True, "message": "Request validate failed, please fill in all required fields"}

#                 if response.status == 404:
#                     return {"error": True, "message": "DATA NOT FOUND!"}

#                 return dmis_response

#     except Exception as e:
#         return {"error": True, "message": f"Unexpected error: {str(e)}"}
