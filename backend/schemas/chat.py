"""
Schema definitions for chat endpoints.
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    thread_id: str | None = None


class SummaryRequest(BaseModel):
    """Request model for summary endpoint"""
    thread_id: str


class PatternInfo(BaseModel):
    """Pattern structure for common errors"""
    pattern: str
    frequency: int
    suggestion: str


class SummaryResponse(BaseModel):
    """Response model for summary endpoint"""
    corrections: list[dict]
    tips: str
    common_patterns: list[PatternInfo]
