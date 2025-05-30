from dotenv import load_dotenv # loads the .env variables into the python process
import os
import logging

# Taking the environment variables stored in .env file
load_dotenv()
CLIENT_ID=os.getenv("CLIENT_ID")
REDIRECT_URI=os.getenv("REDIRECT_URI")
CLIENT_SECRET=os.getenv("CLIENT_SECRET")
FERNET_SECRET_KEY=os.getenv("FERNET_SECRET_KEY")
FRONTEND_ORIGINS=os.getenv("FRONTEND_ORIGINS")
ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY")
FRONTEND_URL=os.getenv("FRONTEND_URL")

# Configure logging
logging.getLogger("uvicorn.access").handlers = []  # Remove default handlers
logging.getLogger("uvicorn.access").propagate = False  # Don't propagate to root logger

class RequestFilter(logging.Filter):
    def filter(self, record):
        return ".well-known/appspecific/com.chrome.devtools" not in record.getMessage()

# Add filter to uvicorn error logger
logging.getLogger("uvicorn.error").addFilter(RequestFilter())