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
