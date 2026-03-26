"""
MCQ Generator State Definition
State for the MCQ Generator LangGraph workflow
"""

from typing import TypedDict, List, Dict, Annotated
from typing_extensions import Literal


def add(a: List, b: List) -> List:
    """Operator to accumulate steps"""
    return a + b


class MCQGeneratorState(TypedDict):
    """State definition for MCQ Generator workflow"""

    # Input
    notebook_id: str
    num_questions: int
    difficulty: str  # "easy", "medium", "hard"

    # Processing
    all_chunks: List[Dict]  # All chunks from Milvus
    selected_chunks: List[Dict]  # Selected diverse chunks
    combined_text: str  # Combined text for generation
    raw_questions: List[Dict]  # Raw questions from LLM

    # Output
    questions: List[Dict]  # Final formatted questions
    total_generated: int

    # Metadata
    steps: Annotated[List[str], add]
    chunk_diversity_score: float
    chunk_count: int
