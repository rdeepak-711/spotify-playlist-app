from .models import SpotifyUserPlaylistDetails
from .database import playlists_collection

async def db_update_playlists_details(data):
    playlist_model = SpotifyUserPlaylistDetails(**data)

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
                "playlists track count": playlist_model.playlist_tracks_count
            }
        }
    
    except Exception as e:
        return {
            "data": "Unable to save/update the playlist data to the database",
            "details": str(e)
        }