"""
Chat Models
Pydantic schemas for chat operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    """Schema for a chat message"""
    role: str  # user, assistant
    content: str


class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str = Field(..., min_length=1)
    notebook_id: str
    chat_history: Optional[List[ChatMessage]] = None
    enable_web_search: bool = False  # NEW: Force enable web search


class SourceReference(BaseModel):
    """Schema for source reference in answer"""
    document_id: str
    filename: str
    chunk_index: int
    text_preview: str
    relevance_score: float
    source_type: str = "document"  # "document" or "web"


class WebSourceReference(BaseModel):
    """Schema for web search source"""
    title: str
    url: str
    content: str
    score: float = 0.0


class Citation(BaseModel):
    """Enhanced citation with file-type-specific metadata"""
    citation_id: int
    document_id: str
    filename: str
    file_type: str  # pdf, docx, txt
    raw_text: str
    chunk_index: int
    relevance_score: float
    source_type: str = "document"
    citation_text: str  # Formatted citation like "[1] file.pdf, page 5"

    # PDF-specific fields
    page_number: Optional[int] = None
    paragraph_start: Optional[int] = None
    paragraph_end: Optional[int] = None

    # DOCX-specific fields
    heading: Optional[str] = None
    heading_level: Optional[int] = None
    section_path: Optional[str] = None
    is_table: Optional[bool] = None
    table_name: Optional[str] = None

    # TXT-specific fields
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    # Common position fields
    char_start: Optional[int] = None
    char_end: Optional[int] = None


class ChatResponse(BaseModel):
    """Schema for chat response"""
    message: str
    sources: List[SourceReference] = []  # Backward compatible
    citations: List[Citation] = []  # Enhanced citations
    web_sources: List[WebSourceReference] = []
    metadata: Dict[str, Any] = {}
    chat_history: Optional[List[ChatMessage]] = []
