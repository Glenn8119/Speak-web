"""
Health check endpoints.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Speak Chat API is running"}


@router.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "speak-chat-api",
        "version": "0.1.0"
    }
