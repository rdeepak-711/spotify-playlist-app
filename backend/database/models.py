from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class SpotifyUserDetails(BaseModel):
    spotify_user_id: str
    username: str
    email: EmailStr
    country: str
    profile_picture: Optional[str] = None # Some users might not have one
    created_at: datetime
    access_token: str
    refresh_token: str
    credits: int = 0
    signup_enriched: bool = False
    is_enriched: bool = False

class SpotifyUserPlaylistDetails(BaseModel):
    owner_spotify_id: str
    playlist_name: str
    playlist_tracks_count: int
    playlist_dp: Optional[str] = None
    playlist_spotify_id: str
    external_url_playlist: str
    is_public: bool
    playlist_description: str
    is_enriched: bool = False

class SpotifyTrackDetails(BaseModel):
    spotify_user_id: str
    playlist_spotify_id: str
    track_spotify_id: str
    track_name: str
    track_artists: list[str]
    track_album_name: str
    track_external_url: str
    track_preview_url: Optional[str]
    track_genre: list[str]
    track_language: str
    track_duration_ms: int
    is_enriched: bool = False
    connected_ids: list[str] = []
    contributor: str | None = None  # Spotify user ID who enriched this track
    users_with_track: list[str] = []  # All user IDs who have this track