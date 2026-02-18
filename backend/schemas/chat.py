"""
Schema definitions for chat endpoints.
"""

from pydantic import BaseModel


class SummaryRequest(BaseModel):
    """Request model for summary endpoint"""
    thread_id: str


class PatternInfo(BaseModel):
    """Pattern structure for common errors"""
    pattern: str
    frequency: int
    suggestion: str


class WordSuggestion(BaseModel):
    """A single IELTS vocabulary suggestion"""
    target_word: str  # The word being replaced
    ielts_word: str  # The suggested IELTS word
    definition: str  # Definition of the IELTS word
    example: str  # Example sentence from IELTS word list
    improved_sentence: str  # The corrected sentence with IELTS word substituted


class IELTSSuggestion(BaseModel):
    """Result of the IELTS RAG pipeline"""
    suggestions: list[WordSuggestion]


class SummaryResponse(BaseModel):
    """Response model for summary endpoint"""
    corrections: list[dict]
    tips: str
    common_patterns: list[PatternInfo]
    ielts_suggestions: list[WordSuggestion] = []


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
