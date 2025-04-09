from fastapi import APIRouter # APIRouter instance
from fastapi.responses import RedirectResponse # HTTP response that redirects the user to another URL
import os # environment variables
from urllib.parse import urlencode # converts a dictionary into a properly formated url query string
from dotenv import load_dotenv # loads the .env variables into the python process
import httpx # async friendly requests
import json # need to w

# Router instance - will use it to call GET, PUSH, PULL and DELETE routes
router = APIRouter()

# Taking the environment variables stored in .env file
load_dotenv()
CLIENT_ID=os.getenv("CLIENT_ID")
REDIRECT_URI=os.getenv("REDIRECT_URI")
CLIENT_SECRET=os.getenv("CLIENT_SECRET")

# Login get request which when hit redirects the user to authorize their spotify account. If logged in then just authorize else log in option too.
@router.get("/login", summary="Redirect user to Spotify login")
async def spotify_login():
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

# Callback function when the user authorize the login using spotify
@router.get("/callback", summary="Callback url returns with the code needed for further usage of the user's spotify data")
async def spotify_callback_code(code: str):
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
        return {"error": "Failed to get token", "details": response.text}
    
    # Save the tokens - access token, refresh token
    tokens = response.json()

    # Writing the refresh token in a file - js file
    refresh_token = tokens.get("refresh_token")
    if refresh_token:
        try:
            with open("refresh_token.json", "w") as f:
                json.dump({"refresh_token": refresh_token}, f)
        except Exception as e:
            return {
                "error": "Failed to save the refresh token in the backend",
                "details": str(e)
            }
        
    # Writing the access token in a file - js file
        access_token = tokens.get("access_token")
        if access_token:
            try:
                with open("access_token.json", "w") as f:
                    json.dump({"access_token": access_token}, f)
            except Exception as e:
                return {
                    "error": "Failed to save the access token in the backend",
                    "details": str(e)
                }

    return tokens

# When the access token expires then we will need to get a new access token to avoid the user's re-login.
# Will use the stored refresh token to get one
@router.get("/refresh-token", summary="Getting a new access token by using the stored refresh token")
async def spotify_token_access_using_refresh():
    try:
        # Reading the refresh token from the storage json file
        with open("refresh_token.json","r") as f:
            token_data = json.load(f)
            refresh_token = token_data.get("refresh_token")

        # Throw error if not found
        if not refresh_token:
            return {
                "error": "Refresh token not found in storage"
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

        # Sending all the data to the token_url through a POST request to received the access token
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, headers=headers)
        
        # Return if faced with any error
        if response.status_code!=200:
            return {"error": "Failed to get token", "details": response.text}
        
        # Save the tokens - access token, refresh token
        tokens = response.json()
        # Writing the access token in a file - js file
        access_token = tokens.get("access_token")
        if access_token:
            try:
                with open("access_token.json", "w") as f:
                    json.dump({"access_token": access_token}, f)
            except Exception as e:
                return {
                    "error": "Failed to save the access token in the backend",
                    "details": str(e)
                }

        return tokens

    except Exception as e:
        return {
            "error": "Unable to get the token",
            "details": str(e)
        }
    
# Fetching the username
@router.get("/me", summary="To get the user's Spotify username")
async def spotify_get_username():
    try:
        # Reading the refresh token from the storage json file
        with open("access_token.json","r") as f:
            token_data = json.load(f)
            access_token = token_data.get("access_token")

        # Throw error if not found
        if not access_token:
            return {
                "error": "Access token not found in storage"
            }
        
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
            return {"error": "Failed to get token", "details": response.text}
        
        return response.json()
    except Exception as e:
        return {
            "error": "Unable to get the user's profile name",
            "details": str(e)
        }