"""
Category Models
Pydantic schemas for document categories
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class CategoryType(str, Enum):
    """Category type enumeration"""
    ACM = "ACM"
    EXTENDED = "Extended"
    CUSTOM = "Custom"


class ConfidenceLevel(str, Enum):
    """Classification confidence level"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CategoryInfo(BaseModel):
    """Schema for category information"""
    name: str
    description: str
    type: CategoryType = CategoryType.ACM
    keywords: List[str] = []


class CategoryAssignment(BaseModel):
    """Schema for a category assignment to a document"""
    category: str
    score: float = Field(ge=0, le=1)
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    is_auto: bool = True  # True = AI assigned, False = user assigned
    suggested: Optional[str] = None  # Suggested category if uncategorized


class DocumentCategory(BaseModel):
    """Schema for document with category info"""
    document_id: str
    categories: List[CategoryAssignment] = []


class CategoryListResponse(BaseModel):
    """Schema for listing all categories"""
    categories: List[CategoryInfo]
    total: int


class UpdateCategoryRequest(BaseModel):
    """Schema for updating document categories"""
    document_id: str
    categories: List[str]  # List of category names


class CategoryFilterRequest(BaseModel):
    """Schema for filtering documents by category"""
    notebook_id: str
    categories: List[str] = []  # Empty = all categories
    include_uncategorized: bool = True
