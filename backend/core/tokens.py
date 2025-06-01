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
            error_msg = "User not found in database"
            print(f"Token refresh error: {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "details": error_msg
            }
        if "refresh_token" not in user:
            error_msg = "Refresh token not found for user"
            print(f"Token refresh error: {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "details": "Database doesn't have refresh token for the user"
            }
        
        try:
            # Decrypt the stored refresh token
            refresh_token = fernet_key.decrypt(user["refresh_token"]).decode()
        except Exception as e:
            error_msg = f"Failed to decrypt refresh token: {str(e)}"
            print(f"Token refresh error: {error_msg}")
            return {
                "success": False,
                "message": "Failed to decrypt refresh token",
                "details": error_msg
            }

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

        try:
            # Sending all the data to the token_url through a POST request to received the access token
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data, headers=headers)
            
            # Return if faced with any error
            if response.status_code != 200:
                error_msg = f"Spotify API error: {response.status_code} - {response.text}"
                print(f"Token refresh error: {error_msg}")
                return {
                    "success": False,
                    "message": "Failed to get token from Spotify",
                    "details": error_msg
                }
            
            # Save the tokens - access token, refresh token
            tokens = response.json()
        except Exception as e:
            error_msg = f"Failed to make request to Spotify: {str(e)}"
            print(f"Token refresh error: {error_msg}")
            return {
                "success": False,
                "message": "Failed to communicate with Spotify",
                "details": error_msg
            }
        
        try:
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
        except Exception as e:
            error_msg = f"Failed to update tokens in database: {str(e)}"
            print(f"Token refresh error: {error_msg}")
            return {
                "success": False,
                "message": "Failed to save new tokens",
                "details": error_msg
            }

        return {
            "success": True,
            "message": "Successfully refreshed tokens",
            "details": {
                "access_token": new_access_token  # Return unencrypted token for frontend use
            }
        }

    except Exception as e:
        error_msg = f"Unexpected error during token refresh: {str(e)}"
        print(f"Token refresh error: {error_msg}")
        return {
            "success": False,
            "message": "Unable to refresh token",
            "details": error_msg
        }