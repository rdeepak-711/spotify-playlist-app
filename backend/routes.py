from core.auth import spotify_user_login, spotify_callback_code, spotify_fetch_and_store_user_playlists, spotify_fetch_and_store_playlists_tracks
from database.user_db import db_get_user_details
from database.database import users_collection
from core.tracks import fetch_and_store_liked_songs_tracks

from fastapi import APIRouter
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
    
    response = RedirectResponse(url=f"/me?spotify_user_id={spotify_user_id}")
    return response

# Fetching the user details and adding it to database
@router.get("/me", summary="To get the user's Spotify user details and adding it to database")
async def spotify_user_details(spotify_user_id: str):
    try:
        # Fetch user data from the database (assuming you have a method to do this)
        user_data = await db_get_user_details(spotify_user_id)
        # If no user found, return an error message
        if not user_data:
            return {
                "success": False,
                "message": "User data not found."
            }
        return {
            "success": True,
            "message": "User found"
        }
    
    except Exception as e:
        return {"message": "An error occurred while fetching user data", "error": str(e)}
    
# Fetching the user's playlist and storing it in the database
@router.get("/me/playlists", summary="To get the user's spotify playlists and store it in the database")
async def spotify_user_playlist_details(spotify_user_id: str):
    try:
        # Fetch user data from the database
        response = await spotify_fetch_and_store_user_playlists(spotify_user_id)
        if response["success"]:
            return {
                "success": True,
                "message": "Successfully added playlist data to database",
                "details": str(response)
            }
        else:
            raise Exception(response["details"])
    
    except Exception as e:
        return {
            "success": False,
            "message": "An error occurred while fetching user playlist",
            "details": str(e)
        }

# Fetching the tracks given the playlist id
@router.get("/me/playlists/tracks", summary="To get the tracks given the spotify playlists and store it in the database")
async def spotify_user_tracks_details(spotify_user_id: str, playlist_spotify_id: str):
    try:
        # Fetch user data from the database (assuming you have a method to do this)
        response = await spotify_fetch_and_store_playlists_tracks(spotify_user_id, playlist_spotify_id)
        if response["success"]:
            return {
                "success": True,
                "message": "Successfully added playlist data to database",
                "details": str(response)
            }
        else:
            raise Exception(response["details"])
    
    except Exception as e:
        return {
            "success": False,
            "message": "An error occurred while fetching user playlist",
            "details": str(e)
        }

@router.get("/me/tracks", summary="Fetch and enrich user's liked songs, returning the count")
async def enrich_liked_songs(spotify_user_id: str):
    result = await fetch_and_store_liked_songs_tracks(spotify_user_id)
    if result.get("success"):
        return {
            "success": True,
            "message": f"Successfully processed {result.get('tracks_saved', 0)} liked songs.",
            "details": result.get("details", "")
        }
    else:
        return {
            "success": False,
            "message": result.get("message", "Failed to process liked songs."),
            "details": result.get("details", ""),
            "tracks_saved": result.get("tracks_saved", 0)
        }