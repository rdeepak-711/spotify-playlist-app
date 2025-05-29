from cryptography.fernet import Fernet
import httpx
from database.database import playlists_collection

from config import FERNET_SECRET_KEY
from .tokens import spotify_token_access_using_refresh
from database.playlist_db import db_update_playlists_details

async def spotify_playlists_workflow(access_token: str):
    try:
        fernet_key = Fernet(FERNET_SECRET_KEY)
        access_token = fernet_key.decrypt(access_token).decode()
        # Current user's profile api endpoint
        playlists_endpoint = "https://api.spotify.com/v1/me/playlists"

        # Get user profile to get spotify_user_id
        profile_endpoint = "https://api.spotify.com/v1/me"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        # Get user profile first to get spotify_user_id
        async with httpx.AsyncClient() as client:
            profile_response = await client.get(profile_endpoint, headers=headers)
            if profile_response.status_code != 200:
                print(f"Failed to get user profile: {profile_response.text}")
                raise Exception("Failed to get user profile")
            user_data = profile_response.json()
            spotify_user_id = user_data.get("id")

        # We are setting a limit at each point and offset signifies the skip
        # Spotify only allows 50 playlists at a time
        # We will get all the playlists
        limit = 50
        offset = 0
        all_playlists = []
        
        # Sending a GET request to get the playlists
        async with httpx.AsyncClient() as client:
            while True:
                params = {
                    "limit": limit,
                    "offset": offset
                }
                response = await client.get(playlists_endpoint, headers=headers, params=params) 

                # Handle expired token - get new access token
                if response.status_code == 401:
                    print("Access token expired. Refreshing ...")
                    refreshed = await spotify_token_access_using_refresh()
                    if "access_token" in refreshed.get("details",{}):
                        access_token = refreshed["details"]["access_token"]
                        headers["Authorization"] = f"Bearer {access_token}"
                        continue
                    else:
                        raise Exception(f"Token refresh failed: {refreshed.details}")

                # Return if faced with any error
                if response.status_code!=200:
                    print(f"Failed to get playlists: {response.text}")
                    raise Exception(f"Failed to get user's playlists{response.text}")

                # Getting the playlist items and extending the array to store the items
                data = response.json()
                items = data.get("items", [])
                
                # Transform each playlist to match our model
                transformed_playlists = [{
                    "owner_spotify_id": spotify_user_id,
                    "playlist_name": playlist.get("name", ""),
                    "playlist_tracks_count": playlist.get("tracks", {}).get("total", 0),
                    "playlist_dp": playlist.get("images", [{}])[0].get("url") if playlist.get("images") else None,
                    "playlist_spotify_id": playlist.get("id", ""),
                    "external_url_playlist": playlist.get("external_urls", {}).get("spotify", ""),
                    "is_public": playlist.get("public", True),
                    "playlist_description": playlist.get("description", ""),
                    "is_enriched": False
                } for playlist in items]
                
                all_playlists.extend(transformed_playlists)
                
                # The api responds with the total amount
                # Using that will move the offset and extract all the playlists
                total = data.get("total", 0)
                offset += limit

                if offset >= total:
                    break

        # Save each transformed playlist
        saved_count = 0
        for playlist in all_playlists:
            result = await db_update_playlists_details(playlist)
            if "message" in result and "Playlist details saved successfully" in result["message"]:
                saved_count += 1
            else:
                print(f"Failed to save playlist: {playlist['playlist_name']}, Error: {result}")

        return {
            "success": True,
            "message": "Successfully added playlists to database",
            "details": all_playlists,  # Return the transformed playlists
        }
    except Exception as e:
        print(f"Error in playlist workflow: {str(e)}")
        return {
            "success": False,
            "message": "Unable to get the user's playlists details",
            "details": str(e)
        }