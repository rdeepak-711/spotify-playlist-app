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
        
        # Decrypt the stored refresh token
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
        if response.status_code != 200:
            return {"success": False, "message": "Failed to get token", "details": response.text}
        
        # Save the tokens - access token, refresh token
        tokens = response.json()
        
        # Encrypt the new access token
        new_access_token = tokens["access_token"]
        encrypted_access_token = fernet_key.encrypt(new_access_token.encode())
        
        # Update data for database
        update_data = {"access_token": encrypted_access_token}
        
        # If we got a new refresh token, encrypt and store it too
        if "refresh_token" in tokens:
            new_refresh_token = tokens["refresh_token"]
            encrypted_refresh_token = fernet_key.encrypt(new_refresh_token.encode())
            update_data["refresh_token"] = encrypted_refresh_token

        # Update the database with encrypted tokens
        await users_collection.update_one(
            {"spotify_user_id": spotify_user_id},
            {"$set": update_data}
        )

        return {
            "success": True,
            "message": "Successfully refreshed tokens",
            "details": {
                "access_token": new_access_token  # Return unencrypted token for frontend use
            }
        }

    except Exception as e:
        print(f"Token refresh error: {str(e)}")
        return {
            "success": False,
            "message": "Unable to refresh token",
            "details": str(e)
        }