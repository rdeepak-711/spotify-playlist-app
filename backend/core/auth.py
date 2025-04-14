from fastapi.responses import RedirectResponse # HTTP response that redirects the user to another URL
from urllib.parse import urlencode # converts a dictionary into a properly formated url query string
import httpx
from config import REDIRECT_URI, CLIENT_ID, CLIENT_SECRET, FERNET_SECRET_KEY
from database.user_db import db_update_user_details
from cryptography.fernet import Fernet

async def spotify_user_login():
    spotify_authorize_url = "https://accounts.spotify.com/authorize"
    params_dict = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "user-read-private user-read-email"
    }
    query_string = urlencode(params_dict)

    redirect_url = f"{spotify_authorize_url}?{query_string}"

    return RedirectResponse(redirect_url)

async def spotify_callback_code(code: str):
    try:
        # Send the code to get the access token for the spotify account
        token_url = "https://accounts.spotify.com/api/token"

        # Spotify needs this encoding to form data
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # POST body needed to validate so the token can be given
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }

        # Sending all the data to the token_url through a POST request to received the access token
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, headers=headers)

        # Return if faced with any error
        if response.status_code!=200:
            return {
                "success": False,
                "message": "Failed to get token", 
                "details": response.text
            }
        
        # Save the tokens - access token, refresh token
        tokens = response.json()
        refresh_token = tokens["refresh_token"]
        access_token = tokens["access_token"]

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
        return response["details"]
    
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to get tokens",
            "details": str(e)
        }