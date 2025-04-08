from fastapi import APIRouter # APIRouter instance
from fastapi.responses import RedirectResponse # HTTP response that redirects the user to another URL
import os # environment variables
from urllib.parse import urlencode # converts a dictionary into a properly formated url query string
from dotenv import load_dotenv # loads the .env variables into the python process
import httpx # async friendly requests

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
    
    tokens = response.json()
    return tokens