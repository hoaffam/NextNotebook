"""
FAQ Models
Pydantic models for FAQ generation
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class FAQGenerateRequest(BaseModel):
    """Request to generate FAQ"""
    notebook_id: str = Field(..., description="Notebook ID to generate FAQ from")
    num_questions: int = Field(5, ge=1, le=20, description="Number of FAQ pairs to generate")


class FAQItem(BaseModel):
    """Single FAQ item"""
    question: str = Field(..., description="FAQ question")
    answer: str = Field(..., description="FAQ answer")
    topic: Optional[str] = Field(None, description="Related topic")


class FAQResponse(BaseModel):
    """Response with generated FAQs"""
    faqs: List[FAQItem] = Field(..., description="List of FAQ items")
    total: int = Field(..., description="Total number of FAQs generated")
    topics: List[str] = Field(default_factory=list, description="Topics covered")
