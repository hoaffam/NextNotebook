"""
Quiz Models
Pydantic schemas for quiz operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime


class QuizQuestion(BaseModel):
    """Schema for a quiz question"""
    id: str
    question: str
    options: List[str]  # A, B, C, D options
    correct_answer: str  # The correct option letter
    explanation: str  # Explanation with source reference
    source_chunk: Optional[str] = None  # Related text from document
    difficulty: str = "medium"


class QuizGenerateRequest(BaseModel):
    """Schema for quiz generation request"""
    notebook_id: str
    num_questions: int = Field(default=10, ge=1, le=50)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    question_types: Optional[List[str]] = None  # multiple_choice, true_false


class QuizResponse(BaseModel):
    """Schema for quiz response"""
    id: str
    notebook_id: str
    title: Optional[str] = None
    questions: List[QuizQuestion]
    total_questions: int
    difficulty: str
    created_at: datetime
    attempts: int = 0
    best_score: Optional[float] = None


class QuizListItem(BaseModel):
    """Schema for quiz list item (without questions)"""
    id: str
    notebook_id: str
    title: str
    total_questions: int
    difficulty: str
    created_at: datetime
    attempts: int = 0
    best_score: Optional[float] = None


class QuizSubmitRequest(BaseModel):
    """Schema for quiz submission"""
    answers: Dict[str, str]  # question_id -> selected answer


class QuizResultItem(BaseModel):
    """Schema for individual quiz result"""
    question_id: str
    user_answer: Optional[str]
    correct_answer: str
    is_correct: bool
    explanation: str


class QuizResultResponse(BaseModel):
    """Schema for quiz result response"""
    quiz_id: str
    score: float  # Percentage
    correct_count: int
    total_questions: int
    results: List[Dict]
