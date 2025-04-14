from fastapi.responses import RedirectResponse # HTTP response that redirects the user to another URL
from urllib.parse import urlencode # converts a dictionary into a properly formated url query string
import httpx
from config import REDIRECT_URI, CLIENT_ID, CLIENT_SECRET

from .user import spotify_users_workflow
from .playlist import spotify_playlists_workflow
from database.database import users_collection

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

        # Spotify USER details added to database
        response = await spotify_users_workflow(access_token, refresh_token)

        if response["success"]:
            return response["details"]
        else:
            raise Exception(response["details"])
    
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to get tokens/Save user details",
            "details": str(e)
        }
    
async def spotify_fetch_and_store_user_playlists(spotify_user_id: str):
    try:
        user_cursor = await users_collection.find_one({"spotify_user_id": spotify_user_id})
        if not user_cursor:
            raise Exception("User not found")
        access_token = user_cursor["access_token"]
        response = await spotify_playlists_workflow(access_token)
        if response["success"]:
            return response
        else:
            raise Exception(response["details"])
    
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to save playlist",
            "details": str(e)
        }