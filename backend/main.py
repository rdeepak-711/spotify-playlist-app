from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import FRONTEND_ORIGINS
from routes import router

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=str(FRONTEND_ORIGINS).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)