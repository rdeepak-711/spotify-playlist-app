import httpx
from cryptography.fernet import Fernet
import anthropic

from .tokens import spotify_token_access_using_refresh
from database.tracks_db import db_update_track_details
from config import FERNET_SECRET_KEY, ANTHROPIC_API_KEY
from database.genres import SUBGENRES, GENRES

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
                    # Detect language
                    try:
                        lang_result = await detect_song_language_genre_subgenre(
                            track.get("name"),
                            [artist["name"] for artist in track.get("artists", [])],
                            (track.get("album") or {}).get("name", "")
                        )
                        if lang_result["success"]:
                            track_language_genre_subgenre = [lang_result["details"]]
                        else:
                            track_language_genre_subgenre = []
                    except Exception:
                        track_language = []
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
                        "track_language": track_language,
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
    
async def detect_song_language_genre_subgenre(track_name, track_artists, track_album_name):
    try:
        # Input validation
        if not track_name or not track_artists or not track_album_name:
            raise ValueError("track_name, track_artists, and track_album_name must all be provided.")

        artists = ", ".join(track_artists)
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        genres_str = ", ".join(GENRES)
        subgenres_str = "; ".join([f"{k}: {', '.join(v)}" for k, v in SUBGENRES.items()])

        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=100,
            temperature=0.1,
            system=(
                "You are a world-class music expert. You are given a song name, artist name, album name, and must detect the language, genre, and subgenre of the song. "
                "You must choose the genre from this list: [" + genres_str + "] and the subgenre from this mapping: {" + subgenres_str + "}. "
                "Return a JSON object with keys: language (ISO 639-1), genre (from the list), subgenre (from the mapping)."
            ),
            messages=[
                {"role": "user", "content": f"Detect the language, genre, and subgenre of the song '{track_name}' by {artists} from the album '{track_album_name}'. Return a JSON object with keys: language, genre, subgenre. The genre must be from the provided list, and the subgenre must be from the mapping for the chosen genre. If unsure, leave subgenre as an empty string."}
            ]
        )

        # Parse the response for JSON
        import json
        language_code = None
        genre = None
        subgenre = None
        if hasattr(response, "content") and response.content:
            for block in response.content:
                if hasattr(block, "text"):
                    try:
                        result = json.loads(block.text.strip())
                        language_code = result.get("language", "")
                        genre = result.get("genre", "")
                        subgenre = result.get("subgenre", "")
                        break
                    except Exception:
                        continue

        if not language_code or len(language_code) != 2 or not language_code.isalpha():
            language_code = ""
        if not genre or genre not in GENRES:
            genre = ""
        if not subgenre or (genre and subgenre not in SUBGENRES.get(genre, [])):
            subgenre = ""

        return {
            "success": True,
            "message": "Song language, genre, and subgenre detected successfully",
            "details": {
                "language": language_code,
                "genre": genre,
                "subgenre": subgenre
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to work on song language/genre detection",
            "details": str(e)
        }