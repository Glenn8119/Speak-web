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


class CorrectionInfo(BaseModel):
    """Correction data for history response"""
    original: str
    corrected: str
    issues: list[str]
    explanation: str


class HistoryMessage(BaseModel):
    """Message structure for history response"""
    id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: int
    correction: CorrectionInfo | None = None


class HistoryResponse(BaseModel):
    """Response model for history endpoint"""
    messages: list[HistoryMessage]
