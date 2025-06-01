from .models import SpotifyUserDetails # user details schema format needed for database
from datetime import datetime # datetime needed to store the creation time
from .database import users_collection # users collection stored in the mongodb database

async def db_update_user_details(data, access_token_encrypted, refresh_token_encrypted):
    try:
        # Saving the details to the database in SpotifyUserDetails format
        user_data = {
            "spotify_user_id": data.get("id"),
            "user_external_url": data.get("external_urls", {}).get("spotify"),
            "username": data.get("display_name"),
            "email": data.get("email"),
            "country": data.get("country"),
            "profile_picture": str(data.get("images")[0]["url"]) if data.get("images") and len(data.get("images")) > 0 else None,
            "created_at": datetime.utcnow(),
            "is_enriched": False,
            "access_token": access_token_encrypted,
            "refresh_token": refresh_token_encrypted,
            "credits": 0,
            "signup_enriched": False
        }

        # Validate required fields
        if not user_data["spotify_user_id"]:
            return {
                "success": False,
                "message": "Missing spotify_user_id in user data",
                "details": "spotify_user_id is required"
            }

        # Create a SpotifyUserDetails model instance using the user_data variable
        user_model = SpotifyUserDetails(**user_data)

        # Updating(just making sure to not add duplicated) the data to users collection
        result = await users_collection.update_one(
            {"spotify_user_id": user_model.spotify_user_id},  # finding the user - using spotify id to name the documents
            {"$set": user_model.dict()}, # set or update the fields
            upsert=True # if not found insert a new entry and name the document to the spotify_id
        )

        return {
            "success": True,
            "message": "User details saved successfully",
            "details": {
                "username": user_model.username,
                "email": user_model.email,
                "spotify_user_id": user_model.spotify_user_id
            }
        }
    
    except Exception as ex:
        return {
            "success": False,
            "message": "Unable to save/update the user's profile to the database",
            "details": str(ex)
        }
    
async def db_get_user_details(spotify_user_id):
    user = await users_collection.find_one({"spotify_user_id": spotify_user_id})
    return user