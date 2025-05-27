from .database import tracks_collection
from .models import SpotifyTrackDetails

async def db_update_track_details(track_data):
    track_model = SpotifyTrackDetails(**track_data)
    try:
        existing = await tracks_collection.find_one({"track_spotify_id": track_model.track_spotify_id, "playlist_spotify_id": track_model.playlist_spotify_id})
        if not existing:
            result=await tracks_collection.insert_one(track_model.dict())
        else:
            result=await tracks_collection.update_one(
                {"track_spotify_id": track_model.track_spotify_id, "playlist_spotify_id": track_model.playlist_spotify_id},
                {"$set": track_model.dict()}
            )
        return {
                "success": True,
                "message": "User details saved successfully",
                "details": {
                    "spotify_user_id": track_model.spotify_user_id,
                    "track_name": track_model.track_name,
                    "track_album_name": track_model.track_album_name
                }
            }
    
    except Exception as ex:
        return {
            "success": False,
            "message": "Unable to save/update the track's data to the database",
            "details": str(ex)
        }
