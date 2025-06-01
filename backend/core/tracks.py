import httpx
from cryptography.fernet import Fernet
import anthropic
import json
import re

from .tokens import spotify_token_access_using_refresh
from database.tracks_db import db_update_track_details
from config import FERNET_SECRET_KEY, ANTHROPIC_API_KEY
from database.genres import SUBGENRES, GENRES
from database.playlist_db import db_update_playlists_details
from database.database import tracks_collection, playlists_collection, users_collection

SPOTIFY_LIKED_SONGS_ENDPOINT = "https://api.spotify.com/v1/me/tracks"
LIKED_SONGS_PLAYLIST_ID = "liked_songs"  # Use a constant or generate a unique ID

async def fetch_and_store_liked_songs_tracks(spotify_user_id):
    try:
        user_cursor = await users_collection.find_one({"spotify_user_id": spotify_user_id})
        if not user_cursor:
            raise Exception("User not found")
        encrypted_access_token = user_cursor["access_token"]
        fernet_key = Fernet(FERNET_SECRET_KEY)
        access_token = fernet_key.decrypt(encrypted_access_token).decode()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        limit = 50
        offset = 0
        track_errors = []
        all_tracks = []
        playlist_data = {
            "owner_spotify_id": spotify_user_id,
            "playlist_name": "Liked Songs",
            "playlist_tracks_count": 0,  # Will update after fetching
            "playlist_dp": None,
            "playlist_spotify_id": LIKED_SONGS_PLAYLIST_ID,
            "external_url_playlist": "",  # Liked Songs doesn't have a public URL
            "is_public": False,
            "playlist_description": "Your liked songs on Spotify",
            "is_enriched": False
        }
        # Save the Liked Songs playlist to DB
        response = await db_update_playlists_details(playlist_data)
        
        while True:
            try:
                params = {"limit": limit, "offset": offset}
                async with httpx.AsyncClient() as client:
                    response = await client.get(SPOTIFY_LIKED_SONGS_ENDPOINT, headers=headers, params=params)  
                if response.status_code != 200:
                    raise Exception(f"Spotify API error: {response.status_code} {response.text}")
                data = response.json()
                items = data.get("items", [])
                if not items:
                    break
                for item in items:
                    track = item.get("track")
                    if not track:
                        track_errors.append(f"Missing track data in item: {item}")
                        continue
                    track_spotify_id = track.get("id")
                    existing_track = await tracks_collection.find_one({"track_spotify_id": track_spotify_id})

                    if existing_track and existing_track.get("is_enriched", True):
                        # Track is already enriched, just add user to users_with_track if not present
                        users_with_track = existing_track.get("users_with_track", [])
                        if spotify_user_id not in users_with_track:
                            users_with_track.append(spotify_user_id)
                            await tracks_collection.update_one(
                                {"track_spotify_id": track_spotify_id},
                                {"$set": {"users_with_track": users_with_track}}
                            )
                        continue  # Skip adding new track
                    
                    # Track not present, add basic details without enrichment
                    track_data = {
                        "spotify_user_id": spotify_user_id,
                        "playlist_spotify_id": LIKED_SONGS_PLAYLIST_ID,
                        "track_spotify_id": track.get("id"),
                        "track_name": track.get("name"),
                        "track_artists": [artist["name"] for artist in track.get("artists", [])],
                        "track_album_name": track.get("album", {}).get("name"),
                        "track_external_url": track.get("external_urls", {}).get("spotify"),
                        "track_preview_url": track.get("preview_url"),
                        "track_genre": [],  # Empty until enriched
                        "track_language": "",  # Empty until enriched
                        "track_duration_ms": track.get("duration_ms"),
                        "is_enriched": False,
                        "connected_ids": [],
                        "users_with_track": [spotify_user_id]
                    }
                    # Save track to DB
                    await db_update_track_details(track_data)
                    all_tracks.append(track_data)
                # Pagination
                if data.get("next"):
                    offset += limit
                else:
                    break
            except Exception as e:
                raise Exception(f"Exception: {str(e)}")

        # Update playlist track count
        playlist_data["playlist_tracks_count"] = len(all_tracks)
        await db_update_playlists_details(playlist_data)

        return {
            "success": True,
            "tracks_saved": len(all_tracks),
            "details": track_errors
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to fetch and store liked songs tracks",
            "details": str(e)
        }

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
                            track_language = lang_result["details"]["language"]
                            track_genre = lang_result["details"]["genre"] if lang_result["details"]["genre"] else ""
                            track_subgenre = lang_result["details"]["subgenre"] if lang_result["details"]["subgenre"] else ""
                        else:
                            track_language = []
                            track_genre = ""
                            track_subgenre = "" 
                    except Exception:
                        track_language = []
                    track_data = {
                        "spotify_user_id": spotify_user_id,
                        "playlist_spotify_id": playlist_id,
                        "track_spotify_id": track.get("id"),
                        "track_name": track.get("name"),
                        "track_artists": [artist["name"] for artist in track.get("artists", [])],
                        "track_album_name": (track.get("album") or {}).get("name", ""),
                        "track_album_img": (track.get("album") or {}).get("images", [{}])[0].get("url", ""),
                        "track_external_url": track.get("external_urls",{}).get("spotify"),
                        "track_preview_url": track.get("preview_url"),
                        "track_genre": [track_genre, track_subgenre],
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
        await update_playlist_enriched_status(playlist_id)
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

        # Step 1: Get initial classification without constraints (shorter prompt)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Cheaper model
            max_tokens=80,
            temperature=0.1,
            system="You are a music expert. Detect the language, main genre, and specific subgenre of songs.",
            messages=[
                {"role": "user", "content": f"For the song '{track_name}' by {artists} from '{track_album_name}', return JSON with: language (full English name), genre (main category like Pop, Rock, Hip Hop, etc.), subgenre (specific style). Format: {{\"language\": \"...\", \"genre\": \"...\", \"subgenre\": \"...\"}}"}
            ]
        )

        # Parse response
        raw_result = None
        if hasattr(response, "content") and response.content:
            for block in response.content:
                if hasattr(block, "text"):
                    json_str = block.text.strip()
                    if json_str.startswith('```'):
                        match = re.search(r"```json\n(.*?)\n```", json_str, re.DOTALL)
                        json_str = match.group(1).strip() if match else json_str
                    
                    try:
                        raw_result = json.loads(json_str)
                        break
                    except:
                        continue

        if not raw_result:
            raise ValueError("Could not parse API response")

        # Step 2: Map to your allowed genres/subgenres
        detected_genre = raw_result.get("genre", "").strip()
        detected_subgenre = raw_result.get("subgenre", "").strip()
        
        # Map to closest allowed genre
        mapped_genre = map_to_allowed_genre(detected_genre)
        mapped_subgenre = map_to_allowed_subgenre(mapped_genre, detected_subgenre)

        return {
            "success": True,
            "message": "Song language, genre, and subgenre detected successfully",
            "details": {
                "language": raw_result.get("language", ""),
                "genre": mapped_genre,
                "subgenre": mapped_subgenre
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to work on song language/genre detection",
            "details": str(e)
        }

def map_to_allowed_genre(detected_genre):
    detected_lower = detected_genre.lower()
    
    # Direct matches
    for genre in GENRES:
        if detected_lower == genre.lower():
            return genre
    
    # Fuzzy matching
    genre_mappings = {
        "pop": "Pop", "rock": "Rock", "hip hop": "Hip Hop", "rap": "Hip Hop",
        "r&b": "R&B", "rnb": "R&B", "country": "Country", "electronic": "Electronic",
        "edm": "Electronic", "classical": "Classical", "jazz": "Jazz",
        "reggae": "Reggae", "blues": "Blues", "latin": "Latin", "folk": "Folk",
        "metal": "Metal", "punk": "Punk", "gospel": "Gospel", "world": "World",
        "kpop": "K-Pop", "k-pop": "K-Pop", "afrobeat": "Afrobeats", 
        "indie": "Indie", "alternative": "Alternative", "alt": "Alternative"
    }
    
    for key, value in genre_mappings.items():
        if key in detected_lower:
            return value
    
    return "Pop"  # Default fallback

def map_to_allowed_subgenre(genre, detected_subgenre):
    if genre not in SUBGENRES:
        return ""
    
    allowed_subgenres = SUBGENRES[genre]
    detected_lower = detected_subgenre.lower()
    
    # Direct match
    for subgenre in allowed_subgenres:
        if detected_lower == subgenre.lower():
            return subgenre
    
    # Partial match
    for subgenre in allowed_subgenres:
        if any(word in detected_lower for word in subgenre.lower().split()):
            return subgenre
    
    return ""  # No match found

async def update_playlist_enriched_status(playlist_spotify_id, track_count):
    # Count total tracks in playlist
    total_tracks = await tracks_collection.count_documents({"playlist_spotify_id": playlist_spotify_id})
    # Count enriched tracks in playlist
    enriched_tracks = await tracks_collection.count_documents({
        "playlist_spotify_id": playlist_spotify_id,
        "is_enriched": True
    })
    # If all tracks are enriched, set playlist is_enriched to True
    if total_tracks > 0 and total_tracks == enriched_tracks:
        await playlists_collection.update_one(
            {"playlist_spotify_id": playlist_spotify_id},
            {"$set": {"is_enriched": True}}
        )
    else:
        await playlists_collection.update_one(
            {"playlist_spotify_id": playlist_spotify_id},
            {"$set": {"is_enriched": False}}
        )

async def enrich_track(track_spotify_id: str, contributor_id: str = None):
    try:
        # Get track from database
        track = await tracks_collection.find_one({"track_spotify_id": track_spotify_id})
        if not track:
            raise Exception("Track not found in database")
        
        if track.get("is_enriched", False):
            return {
                "success": True,
                "message": "Track already enriched",
                "details": track
            }

        # Detect language and genre
        lang_result = await detect_song_language_genre_subgenre(
            track["track_name"],
            track["track_artists"],
            track["track_album_name"]
        )

        if lang_result["success"]:
            # Update track with enriched data
            update_data = {
                "track_language": lang_result["details"]["language"],
                "track_genre": [
                    lang_result["details"]["genre"] if lang_result["details"]["genre"] else "",
                    lang_result["details"]["subgenre"] if lang_result["details"]["subgenre"] else ""
                ],
                "is_enriched": True
            }
            
            if contributor_id:
                update_data["contributor"] = contributor_id

            # Update track in database
            await tracks_collection.update_one(
                {"track_spotify_id": track_spotify_id},
                {"$set": update_data}
            )

            # Update playlist enrichment status
            playlists = await tracks_collection.distinct(
                "playlist_spotify_id",
                {"track_spotify_id": track_spotify_id}
            )
            for playlist_id in playlists:
                await update_playlist_enriched_status(playlist_id)

            return {
                "success": True,
                "message": "Track enriched successfully",
                "details": {**track, **update_data}
            }
        else:
            raise Exception(f"Language detection failed: {lang_result['details']}")

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to enrich track",
            "details": str(e)
        }

async def check_and_create_liked_songs_playlist(spotify_user_id):
    """Quickly check if user has any liked songs and create a playlist entry."""
    try:
        user_cursor = await users_collection.find_one({"spotify_user_id": spotify_user_id})
        if not user_cursor:
            raise Exception("User not found")
        encrypted_access_token = user_cursor["access_token"]
        fernet_key = Fernet(FERNET_SECRET_KEY)
        access_token = fernet_key.decrypt(encrypted_access_token).decode()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # Just fetch one song to check if there are any liked songs
        params = {"limit": 1, "offset": 0}
        async with httpx.AsyncClient() as client:
            response = await client.get(SPOTIFY_LIKED_SONGS_ENDPOINT, headers=headers, params=params)
            
        if response.status_code != 200:
            raise Exception(f"Spotify API error: {response.status_code} {response.text}")
            
        data = response.json()
        total_tracks = data.get("total", 0)
        
        if total_tracks > 0:
            # Create/Update the Liked Songs playlist entry
            playlist_data = {
                "owner_spotify_id": spotify_user_id,
                "playlist_name": "Liked Songs",
                "playlist_tracks_count": total_tracks,  # Use the total count from API
                "playlist_dp": None,
                "playlist_spotify_id": LIKED_SONGS_PLAYLIST_ID,
                "external_url_playlist": "",
                "is_public": False,
                "playlist_description": "Your liked songs on Spotify",
                "is_enriched": False
            }
            await db_update_playlists_details(playlist_data)
            
            return {
                "success": True,
                "has_liked_songs": True,
                "total_tracks": total_tracks
            }
        
        return {
            "success": True,
            "has_liked_songs": False,
            "total_tracks": 0
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to check liked songs",
            "details": str(e)
        }