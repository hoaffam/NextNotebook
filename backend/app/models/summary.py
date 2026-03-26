"""
Summary Models
Pydantic schemas for summary operations
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class SummaryRequest(BaseModel):
    """Schema for summary request"""
    notebook_id: str
    style: Literal["brief", "detailed", "bullet_points"] = "detailed"
    max_length: Optional[int] = Field(None, ge=100, le=5000)


class SummaryResponse(BaseModel):
    """Schema for summary response"""
    summary: str
    sources_used: int
    style: str
