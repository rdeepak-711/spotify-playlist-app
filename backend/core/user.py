from config import FERNET_SECRET_KEY
from database.user_db import db_update_user_details

from cryptography.fernet import Fernet
import httpx

async def spotify_users_workflow(access_token, refresh_token):
    try:
        # Current user's profile api endpoint
        profile_endpoint = "https://api.spotify.com/v1/me"

        # headers
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        # Sending a GET request to get the username
        async with httpx.AsyncClient() as client:
            response = await client.get(profile_endpoint, headers=headers)

            # Return if faced with any error
            if response.status_code!=200:
                return {"message": "Failed to get user's playlists", "details": response.text}
            
            # Storing the user details
            data = response.json()
        
        fernet = Fernet(FERNET_SECRET_KEY)

        access_token_encrypted = fernet.encrypt(access_token.encode())
        refresh_token_encrypted = fernet.encrypt(refresh_token.encode())
        # Add user details to the database
        response = await db_update_user_details(data, access_token_encrypted, refresh_token_encrypted)

        return {
            "success": True,
            "message": "Added the details to database",
            "details": response["details"]
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to work on user details",
            "details": str(e)
        }