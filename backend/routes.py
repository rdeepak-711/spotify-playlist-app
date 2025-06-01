from core.auth import spotify_user_login, spotify_callback_code, spotify_fetch_and_store_user_playlists
from database.user_db import db_get_user_details
from core.tracks import fetch_and_store_liked_songs_tracks, enrich_track, update_playlist_enriched_status
from core.playlist import fetch_playlist_tracks_background
from config import FRONTEND_URL
from core.tokens import spotify_token_access_using_refresh
from database.database import users_collection, playlists_collection, tracks_collection

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from typing import List

router = APIRouter()

@router.get("/", tags=["Authentication"])
async def root_redirect():
    return RedirectResponse(url="/login")

# Login get request which when hit redirects the user to authorize their spotify account. If logged in then just authorize else log in option too.
@router.get("/login", summary="Redirect user to Spotify login", tags=["Authentication"])
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
@router.get("/callback", summary="Callback url returns with the code needed for further usage of the user's spotify data", tags=["Authentication"])
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
@router.get("/me", summary="Get user's Spotify user details", tags=["User"])
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
    
@router.get("/auth/me", summary="Check if user is authenticated", tags=["Authentication"])
async def get_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return {"success": False}
    return {"success": True}
    
@router.post("/refresh-token", summary="Refresh access token using stored refresh token", tags=["Authentication"])
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

# Fetching the user's playlist and storing it in the database
@router.get("/me/playlists", summary="Get user's Spotify playlists", tags=["Playlists"])
async def spotify_user_playlist_details(spotify_user_id: str, background_tasks: BackgroundTasks):
    try:
        # First, get cached playlists from database
        cached_playlists = await playlists_collection.find({
            "owner_spotify_id": spotify_user_id
        }).to_list(length=None)

        # Check if any playlist has zero tracks
        has_zero_tracks = any(
            int(playlist.get("playlist_tracks_count", 0)) == 0 
            for playlist in cached_playlists
        )

        # If any playlist has zero tracks, force an immediate update
        if has_zero_tracks:
            # This will update all playlists including the ones with zero tracks
            await spotify_fetch_and_store_user_playlists(spotify_user_id)
            # Get the updated playlists
            cached_playlists = await playlists_collection.find({
                "owner_spotify_id": spotify_user_id
            }).to_list(length=None)
        else:
            # Start background task to update playlists if no immediate update needed
            background_tasks.add_task(spotify_fetch_and_store_user_playlists, spotify_user_id)

        # Convert MongoDB documents to clean dicts with consistent field names
        playlists_data = []
        for playlist in cached_playlists:
            playlists_data.append({
                "playlist_spotify_id": playlist.get("playlist_spotify_id"),
                "playlist_name": playlist.get("playlist_name"),
                "playlist_description": playlist.get("playlist_description"),
                "playlist_dp": playlist.get("playlist_dp"),
                "playlist_tracks_count": int(playlist.get("playlist_tracks_count", 0)),
                "playlist_external_url": playlist.get("external_url_playlist"),
                "owner_spotify_id": playlist.get("owner_spotify_id"),
                "is_enriched": bool(playlist.get("is_enriched", False))
            })
        
        # Return data
        return {
            "success": True,
            "message": "Returning playlists data",
            "details": playlists_data,
            "is_background_refreshing": not has_zero_tracks  # Only true if we didn't do an immediate update
        }
    
    except Exception as e:
        print(f"Error in playlists endpoint: {str(e)}")
        return {
            "success": False,
            "message": "An error occurred while fetching user playlists",
            "details": str(e)
        }

@router.post("/me/liked-songs/fetch", tags=["Tracks"])
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

@router.post("/me/playlists/{playlist_id}/fetch-tracks", tags=["Tracks"])
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

@router.post("/me/playlists/fetch-all-tracks", tags=["Tracks"])
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

@router.get("/me/playlists/{playlist_id}/tracks/details", tags=["Tracks"])
async def get_playlist_tracks_details(
    playlist_id: str, 
    spotify_user_id: str,
    background_tasks: BackgroundTasks,
    offset: int = 0, 
    limit: int = 50
):
    """Get detailed track information for a playlist, including enhancement status."""
    try:
        # Get user's credits and access token
        user = await users_collection.find_one({"spotify_user_id": spotify_user_id})
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        user_credits = user.get("credits", 0)
        
        # Get total count first
        total_tracks = await tracks_collection.count_documents({
            "playlist_spotify_id": playlist_id
        })
        
        # If no tracks found, trigger the background fetch
        if total_tracks == 0:
            # Add the fetch_playlist_tracks_background function to background tasks
            background_tasks.add_task(
                fetch_playlist_tracks_background,
                spotify_user_id,
                playlist_id,
                user["access_token"]
            )
            
            return {
                "success": True,
                "data": {
                    "tracks": [],
                    "user_credits": user_credits,
                    "is_playlist_enriched": False,
                    "total_tracks": 0,
                    "offset": offset,
                    "limit": limit,
                    "has_more": False,
                    "is_fetching": True  # New flag to indicate tracks are being fetched
                }
            }
        
        # Get paginated tracks for the playlist
        tracks = await tracks_collection.find({
            "playlist_spotify_id": playlist_id
        }).skip(offset).limit(limit).to_list(length=None)
        
        # Get playlist details
        playlist = await playlists_collection.find_one({
            "playlist_spotify_id": playlist_id
        })
        
        if not playlist:
            return {
                "success": False,
                "message": "Playlist not found"
            }
        
        # Transform tracks data and fetch contributor details
        tracks_data = []
        for track in tracks:
            contributor_data = None
            if track.get("contributor"):
                contributor = await users_collection.find_one({"spotify_user_id": track["contributor"]})
                if contributor:
                    contributor_data = {
                        "spotify_user_id": contributor["spotify_user_id"],
                        "username": contributor.get("username"),
                        "profile_picture": contributor.get("profile_picture"),
                        "external_url": contributor.get("external_url")
                    }
            
            tracks_data.append({
                "track_id": track["track_spotify_id"],
                "name": track["track_name"],
                "artists": track["track_artists"],
                "album_name": track["track_album_name"],
                "album_image": track["track_album_img"],
                "external_url": track["track_external_url"],
                "preview_url": track["track_preview_url"],
                "genre": track["track_genre"] if track.get("is_enriched") else [],
                "language": track["track_language"] if track.get("is_enriched") else "",
                "duration_ms": track["track_duration_ms"],
                "is_enriched": track.get("is_enriched", False),
                "contributor": contributor_data
            })
        
        # Start background refresh of tracks
        background_tasks.add_task(
            fetch_playlist_tracks_background,
            spotify_user_id,
            playlist_id,
            user["access_token"]
        )
        
        return {
            "success": True,
            "data": {
                "tracks": tracks_data,
                "user_credits": user_credits,
                "is_playlist_enriched": playlist.get("is_enriched", False),
                "total_tracks": total_tracks,
                "offset": offset,
                "limit": limit,
                "has_more": offset + limit < total_tracks,
                "is_fetching": False,
                "is_background_refreshing": True
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to fetch playlist tracks",
            "details": str(e)
        }

@router.post("/me/playlists/{playlist_id}/enhance", tags=["Enhancement"])
async def enhance_playlist_tracks(
    playlist_id: str,
    spotify_user_id: str,
    track_ids: list[str]
):
    try:
        # Get user's credits
        user = await users_collection.find_one({"spotify_user_id": spotify_user_id})
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        credits_needed = len(track_ids) // 10
        if len(track_ids) % 10 > 0:
            credits_needed += 1
            
        if user.get("credits", 0) < credits_needed:
            return {
                "success": False,
                "message": f"Not enough credits. Need {credits_needed} credits but have {user.get('credits', 0)}"
            }
        
        # Enhance tracks
        enriched_count = 0
        errors = []
        for track_id in track_ids:
            result = await enrich_track(track_id, spotify_user_id)
            if result["success"]:
                enriched_count += 1
            else:
                errors.append({
                    "track_id": track_id,
                    "error": result["details"]
                })
        
        # Deduct credits only if some tracks were enriched
        if enriched_count > 0:
            await users_collection.update_one(
                {"spotify_user_id": spotify_user_id},
                {"$inc": {"credits": -credits_needed}}
            )
            
            # Update playlist enrichment status
            await update_playlist_enriched_status(playlist_id)
        
        return {
            "success": True,
            "message": f"Successfully enriched {enriched_count} tracks",
            "details": {
                "enriched_count": enriched_count,
                "credits_used": credits_needed,
                "errors": errors
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to enhance tracks",
            "details": str(e)
        }

@router.get("/me/playlists/{playlist_id}", tags=["Playlists"])
async def get_playlist_details(playlist_id: str, spotify_user_id: str):
    """Get details for a single playlist."""
    try:
        playlist = await playlists_collection.find_one({
            "playlist_spotify_id": playlist_id,
            "owner_spotify_id": spotify_user_id
        })
        
        if not playlist:
            return {
                "success": False,
                "message": "Playlist not found"
            }
        
        # Convert MongoDB ObjectId to string
        playlist["_id"] = str(playlist["_id"])
        
        return {
            "success": True,
            "data": playlist
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to fetch playlist details",
            "details": str(e)
        }

@router.get("/users/{spotify_user_id}/profile", tags=["User"])
async def get_user_profile(spotify_user_id: str):
    """Get user profile information for display in the contributor section."""
    try:
        user = await users_collection.find_one({"spotify_user_id": spotify_user_id})
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Convert MongoDB document to a clean dict with only needed fields
        profile_data = {
            "username": user.get("username"),
            "profile_picture": user.get("profile_picture"),
            "external_url": user.get("user_external_url"),
            "country": user.get("country")
        }
        
        return {
            "success": True,
            "data": profile_data
        }
    except Exception as e:
        print(f"Error in get_user_profile endpoint: {str(e)}")
        return {
            "success": False,
            "message": "Failed to fetch user profile",
            "details": str(e)
        }
