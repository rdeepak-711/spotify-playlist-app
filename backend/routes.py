from core.auth import spotify_user_login, spotify_callback_code, spotify_fetch_and_store_user_playlists, spotify_fetch_and_store_playlists_tracks
from database.user_db import db_get_user_details
from core.tracks import fetch_and_store_liked_songs_tracks
from core.playlist import fetch_playlist_tracks_background
from config import FRONTEND_URL
from core.tokens import spotify_token_access_using_refresh
from database.database import users_collection, playlists_collection

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/")
async def root_redirect():
    return RedirectResponse(url="/login")

# Login get request which when hit redirects the user to authorize their spotify account. If logged in then just authorize else log in option too.
@router.get("/login", summary="Redirect user to Spotify login")
async def spotify_login():
    try:
        auth_url = await spotify_user_login()
        response = {"redirectUrl": auth_url}
        return response
    except Exception as e:
        print(f"Error in login endpoint: {str(e)}")
        return {
            "success": False,
            "message": "Failed to generate Spotify login URL",
            "error": str(e)
        }

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
    
    # Redirect to frontend callback URL instead of /me
    response = RedirectResponse(url=f"{FRONTEND_URL}/callback?spotify_user_id={spotify_user_id}")
    return response

# Fetching the user details and adding it to database
@router.get("/me", summary="To get the user's Spotify user details and adding it to database")
async def spotify_user_details(spotify_user_id: str):
    try:
        # Fetch user data from the database
        user_data = await db_get_user_details(spotify_user_id)
        
        # If no user found, return an error message
        if not user_data:
            print("No user data found")
            return {
                "success": False,
                "message": "User data not found."
            }
        
        # Convert MongoDB document to dict and include all relevant fields
        user_dict = {
            "spotify_user_id": str(user_data.get("spotify_user_id")),
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "country": user_data.get("country"),
            "profile_picture": user_data.get("profile_picture"),
            "created_at": user_data.get("created_at"),
            "credits": user_data.get("credits", 0),
            "is_enriched": user_data.get("is_enriched", False)
        }
        
        return {
            "success": True,
            "user_data": user_dict
        }

    except Exception as e:
        print(f"Error in /me endpoint: {str(e)}")
        return {
            "success": False,
            "message": "An error occurred while fetching user data",
            "error": str(e)
        }
    
@router.get("/auth/me", summary="Check if user is authenticated")
async def get_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return {"success": False}
    return {"success": True}
    
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
                "details": response.get("details", [])
            }
        else:
            print(f"Error in playlists response: {response['details']}")
            raise Exception(response["details"])
    
    except Exception as e:
        print(f"Error in playlists endpoint: {str(e)}")
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

@router.post("/refresh-token", summary="Refresh access token using stored refresh token")
async def refresh_access_token(request: Request):
    try:
        body = await request.json()
        spotify_user_id = body.get("spotify_user_id")
        
        if not spotify_user_id:
            return {
                "success": False,
                "message": "spotify_user_id is required"
            }
            
        refresh_result = await spotify_token_access_using_refresh(spotify_user_id)
        
        if refresh_result["success"]:
            return {
                "success": True,
                "access_token": refresh_result["details"]["access_token"]
            }
        else:
            return {
                "success": False,
                "message": "Token refresh failed",
                "error": refresh_result["details"]
            }
            
    except Exception as e:
        print(f"Error in refresh-token endpoint: {str(e)}")
        return {
            "success": False,
            "message": "Failed to refresh token",
            "error": str(e)
        }

@router.post("/me/liked-songs/fetch")
async def fetch_liked_songs_background(background_tasks: BackgroundTasks, spotify_user_id: str):
    """Endpoint to trigger background fetching of liked songs."""
    try:
        # Add the fetch_and_store_liked_songs_tracks function to background tasks
        background_tasks.add_task(fetch_and_store_liked_songs_tracks, spotify_user_id)
        
        return {
            "success": True,
            "message": "Started fetching liked songs in the background"
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to start background task",
            "details": str(e)
        }

@router.post("/me/playlists/{playlist_id}/fetch-tracks")
async def fetch_playlist_tracks_background_endpoint(
    background_tasks: BackgroundTasks, 
    spotify_user_id: str, 
    playlist_id: str
):
    try:
        # Get user's access token
        user = await users_collection.find_one({"spotify_user_id": spotify_user_id})
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Add the fetch_playlist_tracks_background function to background tasks
        background_tasks.add_task(
            fetch_playlist_tracks_background,
            spotify_user_id,
            playlist_id,
            user["access_token"]
        )
        
        return {
            "success": True,
            "message": f"Started fetching tracks for playlist {playlist_id} in the background"
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to start background task",
            "details": str(e)
        }

@router.post("/me/playlists/fetch-all-tracks")
async def fetch_all_playlists_tracks_background(
    background_tasks: BackgroundTasks, 
    spotify_user_id: str
):
    try:
        # Get user's access token
        user = await users_collection.find_one({"spotify_user_id": spotify_user_id})
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }

        # Get all playlists for the user
        playlists = await playlists_collection.find(
            {"owner_spotify_id": spotify_user_id}
        ).to_list(length=None)

        # Add background tasks for each playlist
        for playlist in playlists:
            playlist_id = playlist["playlist_spotify_id"]
            background_tasks.add_task(
                fetch_playlist_tracks_background,
                spotify_user_id,
                playlist_id,
                user["access_token"]
            )

        return {
            "success": True,
            "message": f"Started fetching tracks for {len(playlists)} playlists in the background"
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to start background tasks",
            "details": str(e)
        }