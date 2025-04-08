from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from routes import router

load_dotenv()

app = FastAPI()
FRONTEND_ORIGINS=os.getenv("FRONTEND_ORIGINS")


app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)