from .models import SpotifyUserPlaylistDetails
from .database import playlists_collection

async def db_update_playlists_details(data):
    playlist_data = {
        "owner_spotify_id": data.get("owner").get("id"),
        "playlist_name": data.get("name"),
        "playlist_tracks_count": data.get("tracks").get("total"),
        "playlist_dp": str(data.get("images")[0]["url"]) if data.get("images") else None,
        "playlist_spotify_id": data.get("id"),
        "external_url_playlist": data.get("external_urls").get("spotify"),
        "is_public": bool(data.get("public")),
        "playlist_description": data.get("description"),
        "is_enriched": False
    }

    playlist_model = SpotifyUserPlaylistDetails(**playlist_data)

    try:
        await playlists_collection.update_one(
            {"playlist_spotify_id": playlist_model.playlist_spotify_id},
            {"$set": playlist_model.dict()},
            upsert=True
        )

        return {
            "message": "Playlist details saved successfully",
            "details": {
                "playlist name": playlist_model.playlist_name,
                "playlist tracks url": playlist_model.playlist_tracks_url,
                "playlists track count": playlist_model.playlist_tracks_count
            }
        }
    
    except Exception as e:
        return {
            "data": "Unable to save/update the playlist data to the database",
            "details": str(e)
        }