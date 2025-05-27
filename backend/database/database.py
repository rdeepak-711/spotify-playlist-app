from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_CONNECTION_URL = os.getenv("MONGODB_CONNECTION_URL")

MONGODB_CLIENT = AsyncIOMotorClient(MONGODB_CONNECTION_URL)

database = MONGODB_CLIENT.spotify_playlists_db

users_collection = database.users
playlists_collection = database.playlists
tracks_collection = database.tracks