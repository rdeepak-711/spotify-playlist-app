from dotenv import load_dotenv # loads the .env variables into the python process
import os

# Taking the environment variables stored in .env file
load_dotenv()
CLIENT_ID=os.getenv("CLIENT_ID")
REDIRECT_URI=os.getenv("REDIRECT_URI")
CLIENT_SECRET=os.getenv("CLIENT_SECRET")
FERNET_SECRET_KEY=os.getenv("FERNET_SECRET_KEY")
FRONTEND_ORIGINS=os.getenv("FRONTEND_ORIGINS")
ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY")
FRONTEND_URL=os.getenv("FRONTEND_URL")