from core.auth import spotify_user_login, spotify_callback_code
from database.user_db import db_get_user_details

from fastapi import APIRouter , Request
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/")
async def root_redirect():
    return RedirectResponse(url="/login")

# Login get request which when hit redirects the user to authorize their spotify account. If logged in then just authorize else log in option too.
@router.get("/login", summary="Redirect user to Spotify login")
async def spotify_login():
    return await spotify_user_login()

# Callback function when the user authorize the login using spotify
@router.get("/callback", summary="Callback url returns with the code needed for further usage of the user's spotify data")
async def spotify_login_callback(code: str):
    user_data = await spotify_callback_code(code)
    # Handle failure case
    if not user_data or "spotify_user_id" not in user_data:
        return {
            "success": False,
            "message": "Login failed or user_data missing.",
            "details": str(user_data)
        }
    spotify_user_id = user_data["spotify_user_id"]
    
    # Store the spotify_user_id in a cookie (or session)
    response = RedirectResponse(url=f"/me?spotify_user_id={spotify_user_id}")
    return response

# Fetching the user details and adding it to database
@router.get("/me", summary="To get the user's Spotify user details and adding it to database")
async def spotify_user_details(spotify_user_id):
    try:
        # Fetch user data from the database (assuming you have a method to do this)
        user_data = await db_get_user_details(spotify_user_id)
        print(user_data)
        # If no user found, return an error message
        if not user_data:
            return {"message": "User data not found."}

        return {"message": "User successfully logged in and redirected!", "user_data": str(user_data)}
    
    except Exception as e:
        return {"message": "An error occurred while fetching user data", "error": str(e)}