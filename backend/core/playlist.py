from cryptography.fernet import Fernet
import httpx

from config import FERNET_SECRET_KEY
from .tokens import spotify_token_access_using_refresh
from database.playlist_db import db_update_playlists_details

async def spotify_playlists_workflow(access_token):
    try:
        fernet_key = Fernet(FERNET_SECRET_KEY)
        access_token = fernet_key.decrypt(access_token).decode()
        # Current user's profile api endpoint
        playlists_endpoint = "https://api.spotify.com/v1/me/playlists"

        # headers
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        # We are setting a limit at each point and offset signifies the skip
        # Spotify only allows 50 playlists at a time
        # We will get all the playlists
        limit = 50
        offset = 0
        all_playlists = []
        # Sending a GET request to get the username
        async with httpx.AsyncClient() as client:
            while True:
                # Setting the parameters for the API call
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
                    raise Exception(f"Failed to get user's playlists{response.text}")

                # Getting the playlist items and extending the array to store the items
                data = response.json()
                items = data.get("items", [])
                all_playlists.extend(items) 
                
                # The api responds with the total amount
                # Using that will move the offset and extract all the playlists
                total = data.get("total", 0)
                offset += limit

                if offset >= total:
                    break

        for playlist in all_playlists:
            await db_update_playlists_details(playlist)

        if all_playlists:
            first_playlist = all_playlists[0]
            playlist_id = first_playlist.get("id")
            playlist_name = first_playlist.get("name")
            # one_track = await spotify_enrich_playlist_tracks(playlist_id=playlist_id)
        # else:
        #     one_track = None
        return {
            "success": True,
            "message": "Successfully added playlists to database",
            "details": str(len(all_playlists)),
            "playlist name": playlist_name
            # "sample_track_from_first_playlist": one_track
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Unable to get the user's playlists details",
            "details": str(e)
        }