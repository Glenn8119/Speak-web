"""
Speak Chat App - Backend API
English practice application with AI-powered conversation and grammar correction.
"""

from endpoints import router
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(
    title="Speak Chat API",
    description="AI-powered English practice with real-time grammar corrections",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(router)
