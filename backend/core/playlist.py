from cryptography.fernet import Fernet
import httpx
import asyncio
from database.database import playlists_collection, users_collection
from pymongo import UpdateOne

from config import FERNET_SECRET_KEY
from .tokens import spotify_token_access_using_refresh
from .tracks import check_and_create_liked_songs_playlist, spotify_tracks_workflow

async def fetch_playlist_tracks_background(spotify_user_id: str, playlist_id: str, access_token: str):
    try:
        await spotify_tracks_workflow(spotify_user_id, playlist_id, access_token)
        return {
            "success": True,
            "message": f"Successfully fetched tracks for playlist {playlist_id}"
        }
    except Exception as e:
        print(f"Error fetching tracks for playlist {playlist_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to fetch tracks for playlist {playlist_id}",
            "details": str(e)
        }

async def fetch_playlist_batch(client, offset, limit, headers, playlists_endpoint):
    try:
        params = {"limit": limit, "offset": offset}
        response = await client.get(playlists_endpoint, headers=headers, params=params)
        return response
    except Exception as e:
        print(f"Error fetching batch at offset {offset}: {str(e)}")
        return None

async def db_batch_update_playlists(playlists):
    try:
        operations = [
            UpdateOne(
                {"playlist_spotify_id": playlist["playlist_spotify_id"]},
                {"$set": playlist},
                upsert=True
            ) for playlist in playlists
        ]
        result = await playlists_collection.bulk_write(operations)
        return {
            "success": True,
            "modified_count": result.modified_count,
            "upserted_count": result.upserted_count
        }
    except Exception as e:
        print(f"Error in batch update: {str(e)}")
        return {"success": False, "error": str(e)}

async def spotify_playlists_workflow(access_token: str):
    try:
        # Get user_id from database using the access token
        fernet_key = Fernet(FERNET_SECRET_KEY)
        decrypted_access_token = fernet_key.decrypt(access_token).decode()
        
        # Find user by access token
        user = await users_collection.find_one({"access_token": access_token})
        if not user:
            raise Exception("User not found in database")
        spotify_user_id = user["spotify_user_id"]

        # Fetch playlists from Spotify API
        playlists_endpoint = "https://api.spotify.com/v1/me/playlists"
        headers = {
            "Authorization": f"Bearer {decrypted_access_token}"
        }
        
        # First, get total number of playlists
        async with httpx.AsyncClient() as client:
            initial_response = await client.get(playlists_endpoint, headers=headers, params={"limit": 1, "offset": 0})
            
            if initial_response.status_code == 401:
                refreshed = await spotify_token_access_using_refresh()
                if "access_token" in refreshed.get("details", {}):
                    decrypted_access_token = refreshed["details"]["access_token"]
                    headers["Authorization"] = f"Bearer {decrypted_access_token}"
                    initial_response = await client.get(playlists_endpoint, headers=headers, params={"limit": 1, "offset": 0})
                else:
                    raise Exception(f"Token refresh failed: {refreshed.get('details')}")

            if initial_response.status_code != 200:
                raise Exception(f"Failed to get initial playlist count: {initial_response.text}")

            total_playlists = initial_response.json().get("total", 0)
            
            # Prepare parallel batch requests
            batch_size = 50
            tasks = []
            for offset in range(0, total_playlists, batch_size):
                task = fetch_playlist_batch(client, offset, batch_size, headers, playlists_endpoint)
                tasks.append(task)

            # Execute all requests in parallel
            responses = await asyncio.gather(*tasks)

        # Process all responses
        all_playlists = []
        for response in responses:
            if response and response.status_code == 200:
                items = response.json().get("items", [])
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

        # Batch update all playlists at once
        if all_playlists:
            update_result = await db_batch_update_playlists(all_playlists)
            if not update_result["success"]:
                print(f"Warning: Some playlists may not have been saved: {update_result}")

        # Check and create Liked Songs playlist if user has any
        liked_songs_result = await check_and_create_liked_songs_playlist(spotify_user_id)
        if liked_songs_result["success"] and liked_songs_result["has_liked_songs"]:
            liked_songs_playlist = {
                "owner_spotify_id": spotify_user_id,
                "playlist_name": "Liked Songs",
                "playlist_tracks_count": liked_songs_result["total_tracks"],
                "playlist_dp": None,
                "playlist_spotify_id": "liked_songs",
                "external_url_playlist": "",
                "is_public": False,
                "playlist_description": "Your liked songs on Spotify",
                "is_enriched": False
            }
            all_playlists.append(liked_songs_playlist)

        return {
            "success": True,
            "message": "Successfully added playlists to database",
            "details": all_playlists
        }
    except Exception as e:
        print(f"Error in playlist workflow: {str(e)}")
        return {
            "success": False,
            "message": "Unable to get the user's playlists details",
            "details": str(e)
        }