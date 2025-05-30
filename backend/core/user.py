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
            if response.status_code != 200:
                return {
                    "success": False,
                    "message": "Failed to get user profile from Spotify",
                    "details": response.text
                }
            
            # Storing the user details
            data = response.json()
            
            if not data.get("id"):
                return {
                    "success": False,
                    "message": "Missing user ID in Spotify response",
                    "details": "Spotify API did not return a user ID"
                }
        
        try:
            fernet = Fernet(FERNET_SECRET_KEY)
            access_token_encrypted = fernet.encrypt(access_token.encode())
            refresh_token_encrypted = fernet.encrypt(refresh_token.encode())
        except Exception as e:
            return {
                "success": False,
                "message": "Failed to encrypt tokens",
                "details": str(e)
            }

        # Add user details to the database
        db_response = await db_update_user_details(data, access_token_encrypted, refresh_token_encrypted)
        
        if not db_response.get("success", False):
            return {
                "success": False,
                "message": "Failed to save user details to database",
                "details": db_response.get("details", "Unknown database error")
            }

        return {
            "success": True,
            "message": "User details saved successfully",
            "details": {
                "spotify_user_id": data.get("id"),
                "username": data.get("display_name"),
                "email": data.get("email")
            }
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to process user details",
            "details": str(e)
        }