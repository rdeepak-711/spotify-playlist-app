import httpx
from cryptography.fernet import Fernet

from .tokens import spotify_token_access_using_refresh
from database.tracks_db import db_update_track_details
from config import FERNET_SECRET_KEY

async def spotify_tracks_workflow(spotify_user_id, playlist_id, access_token):
    try:
        fernet_key = Fernet(FERNET_SECRET_KEY)
        access_token = fernet_key.decrypt(access_token).decode()
        # GET endpoint to get all the tracks using the playlist id
        tracks_endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?market='IN'"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        limit=100
        offset=0
        all_tracks=[]

        async with httpx.AsyncClient() as client:
            while True:
                params = {"limit": limit, "offset": offset}
                response = await client.get(tracks_endpoint, headers=headers, params=params) 

                # Handle expired token - get new access token
                if response.status_code == 401:
                    print("Access token expired. Refreshing ...")
                    refreshed = await spotify_token_access_using_refresh()
                    if "access_token" in refreshed.get("details",{}):
                        access_token = refreshed["details"]["access_token"]
                        headers["Authorization"] = f"Bearer {access_token}"
                        continue
                    else:
                        raise Exception(f"details {refreshed.get("details")}")

                # Return if faced with any error
                if response.status_code!=200:
                    raise Exception(f"details {response.text}")
            
                data = response.json()
                items = data.get("items",[])
                for item in items:
                    track = item.get("track", {})
                    if not track:
                        continue
                    track_data = {
                        "spotify_user_id": spotify_user_id,
                        "playlist_spotify_id": playlist_id,
                        "track_spotify_id": track.get("id"),
                        "track_name": track.get("name"),
                        "track_artists": [artist["name"] for artist in track.get("artists", [])],
                        "track_album_name": (track.get("album") or {}).get("name", ""),
                        "track_external_url": track.get("external_urls",{}).get("spotify"),
                        "track_preview_url": track.get("preview_url"),
                        "track_genre": [],
                        "track_language": [],
                        "track_duration_ms": track.get("duration_ms"),
                        "is_enriched": False
                    }
                    all_tracks.append(track_data)
                if len(items)<limit:
                    break
                offset+=limit
        # Save tracks to DB
        for track_data in all_tracks:
            response = await db_update_track_details(track_data)
            if response["success"]==False:
                raise Exception(response["details"])
        return {
            "success": True,
            "message": "Added all the tracks to the database",
            "details": str(response)
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to work on track details",
            "details": str(e)
        }