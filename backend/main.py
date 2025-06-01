from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from config import FRONTEND_ORIGINS
from routes import router

class DevToolsFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if ".well-known/appspecific/com.chrome.devtools" in request.url.path:
            # Return 404 without logging
            return await call_next(request)
        return await call_next(request)

app = FastAPI(
    title="Spotify Playlist App API",
    description="API for managing Spotify playlists with enhanced features",
    version="1.0.0",
    docs_url="/docs",  # Enable Swagger UI at /docs
    redoc_url="/redoc"  # Enable ReDoc at /redoc
)

# Configure CORS
origins = str(FRONTEND_ORIGINS).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add DevTools filter middleware
app.add_middleware(DevToolsFilterMiddleware)

app.include_router(router)