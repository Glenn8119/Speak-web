"""
Speak Chat App - Backend API
English practice application with AI-powered conversation and grammar correction.
"""

import logging
import sys
from contextlib import asynccontextmanager

from endpoints import router
from dependencies import load_ielts_index
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

# Configure logging with structured format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for server startup/shutdown.

    On startup: Load IELTS FAISS index into memory.
    """
    # Startup: Load IELTS index
    logger.info("Loading IELTS FAISS index...")
    index = load_ielts_index()
    if index is not None:
        logger.info("IELTS FAISS index loaded successfully")
    else:
        logger.warning("IELTS FAISS index not available - suggestions will be disabled")

    yield

    # Shutdown: cleanup (if needed)
    logger.info("Server shutting down")


app = FastAPI(
    title="Speak Chat API",
    description="AI-powered English practice with real-time grammar corrections",
    version="0.1.0",
    lifespan=lifespan
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
