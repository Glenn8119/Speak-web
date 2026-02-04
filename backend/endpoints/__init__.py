"""
API endpoints for Speak Chat API.
"""

from fastapi import APIRouter

from endpoints.health import router as health_router
from endpoints.chat import router as chat_router

# Main router that includes all endpoint routers
router = APIRouter()

router.include_router(health_router)
router.include_router(chat_router)
