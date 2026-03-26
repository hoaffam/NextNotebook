"""
Notebook Models
Pydantic schemas for notebook operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NotebookCreate(BaseModel):
    """Schema for creating a notebook"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class NotebookUpdate(BaseModel):
    """Schema for updating a notebook"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class NotebookResponse(BaseModel):
    """Schema for notebook response"""
    id: str
    name: str
    description: Optional[str] = None
    sources_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NotebookListResponse(BaseModel):
    """Schema for list of notebooks"""
    notebooks: List[NotebookResponse]
    total: int
