from pydantic import BaseModel
from typing import List, Dict, Optional

class AIRequest(BaseModel):
    """Base schema for AI request"""
    query: str
    context: Optional[str] = None  # context for RAG


class SourceItem(BaseModel):
    """Base schema for each context item"""
    text: str
    score: float
    metadata: Dict


class AIResponse(BaseModel):
    """Base schema for AI response"""
    answer: str                    
    sources: Optional[List[SourceItem]] = []


class AskRequest(BaseModel):
    """Request schema for asking questions about audio transcripts."""
    query: str
    top_k: int = 10
    score_threshold: float = 0.1
    rerank_top_k: int = 3


class AskResponse(BaseModel):
    """Response schema for asking questions."""
    message: str
    sources: List[SourceItem]
    total: int

