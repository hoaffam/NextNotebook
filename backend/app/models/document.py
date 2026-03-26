"""
Document Models
Pydantic schemas for document operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CategoryAssignment(BaseModel):
    """Schema for a category assignment"""
    category: str
    score: float = 0.0
    confidence: str = "low"
    is_auto: bool = True
    suggested: Optional[str] = None


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: str
    filename: str
    notebook_id: str
    chunks_count: int = 0
    status: str = "processed"  # uploaded, processing, processed, error
    # New fields for summary and classification
    summary: Optional[str] = None
    key_topics: List[str] = []
    categories: List[CategoryAssignment] = []
    created_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
    """Schema for list of documents"""
    documents: List[DocumentResponse]
    total: int


class DocumentChunk(BaseModel):
    """Schema for a document chunk"""
    id: str
    document_id: str
    text: str
    chunk_index: int
    metadata: dict = {}


class DocumentDetailResponse(BaseModel):
    """Schema for detailed document response with full info"""
    id: str
    filename: str
    notebook_id: str
    chunks_count: int = 0
    status: str = "processed"
    summary: Optional[str] = None
    key_topics: List[str] = []
    categories: List[CategoryAssignment] = []
    file_size: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
