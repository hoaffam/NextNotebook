"""
Summarizer State Definition
State for the Summarizer LangGraph workflow
"""

from typing import TypedDict, List, Dict, Optional, Annotated
from typing_extensions import Literal


def add(a: List, b: List) -> List:
    """Operator to accumulate steps"""
    return a + b


class SummarizerState(TypedDict):
    """State definition for Summarizer workflow"""

    # Input
    notebook_id: str
    document_id: Optional[str]  # None = summarize whole notebook
    style: str  # "document", "notebook"
    max_length: Optional[int]

    # Processing
    documents: List[Dict]  # Documents from MongoDB
    chunks: List[Dict]  # Retrieved chunks from Milvus (optional)
    selected_text: str  # Combined text for summarization
    all_summaries: List[Dict]  # Individual document summaries

    # Output
    summary: str
    key_topics: List[str]
    suggested_questions: List[str]
    summary_embedding: Optional[List[float]]
    sources_used: int

    # Metadata
    steps: Annotated[List[str], add]
    document_count: int
