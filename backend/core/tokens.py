from config import CLIENT_SECRET, CLIENT_ID, FERNET_SECRET_KEY
from database.database import users_collection
import httpx
from cryptography.fernet import Fernet

async def spotify_token_access_using_refresh(spotify_user_id: str):
    try:
        fernet_key = Fernet(FERNET_SECRET_KEY)
        # Getting the refresh token
        user = await users_collection.find_one({"spotify_user_id": spotify_user_id})
        if not user:
            return {
                "success": False,
                "message": "User not found in database",
                "details": "User not found in database"
            }
        if "refresh_token" not in user:
            return {
                "success": False,
                "message": "Refresh token not found for user",
                "details": "Database doesn't have refresh for the user"
            }
        refresh_token = fernet_key.decrypt(user["refresh_token"]).decode()

        # Token URL to get the access token
        token_url = "https://accounts.spotify.com/api/token"

        # Headers for the sending POST request for access token retrieval
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # POST body needed to validate so the access token can be given using refresh token
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }

        # Sending all the data to the token_url through a POST request to received the access token
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, headers=headers)
        
        # Return if faced with any error
        if response.status_code!=200:
            return {"message": "Failed to get token", "details": response.text}
        
        # Save the tokens - access token, refresh token
        tokens = response.json()
        # Update the user with new access token (Spotify may or may not send new refresh_token)
        update_data = {"access_token": tokens.get("access_token")}
        if "refresh_token" in tokens:
            update_data["refresh_token"] = fernet_key.encrypt(tokens["refresh_token"].encode())

        await users_collection.update_one({"spotify_id": spotify_user_id}, {"$set": update_data})

        return {
            "success": True,
            "message": "Successfully got tokens",
            "details": str(tokens)
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Unable to get the token",
            "details": str(e)
        }