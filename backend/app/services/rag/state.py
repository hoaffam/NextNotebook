"""
Graph State
State definitions for LangGraph workflow
"""

from typing import List, Dict, Optional, TypedDict, Annotated
from operator import add


class WebSource(TypedDict):
    """Web search result source"""
    title: str
    url: str
    content: str
    score: float


class GraphState(TypedDict):
    """
    State for the Corrective RAG (CRAG) workflow graph

    Attributes:
        question: Original user question
        notebook_id: ID of the notebook being queried
        chat_history: Previous conversation messages
        documents: Retrieved relevant documents
        generation: Generated answer
        web_search_needed: Flag for web search
        steps: List of workflow steps taken
        answer: Final answer
        sources: Source references
        retrieval_count: Number of retrieval attempts
        web_sources: Web search results (separate from document sources)
    """

    # Input
    question: str
    notebook_id: str
    chat_history: List[Dict]

    # Processing
    documents: List[Dict]
    filtered_documents: List[Dict]
    rewritten_question: Optional[str]
    web_search_needed: bool
    web_results: List[Dict]

    # Quality signals (from grade_documents)
    coverage_score: float
    answerable: bool
    citable: bool

    # Output
    answer: str
    sources: List[Dict]  # Backward compatible format
    citations: List[Dict]  # Enhanced citations with file-type-specific metadata
    web_sources: List[WebSource]  # Separate web sources for UI display

    # Control flags
    force_web_search: bool  # Force web search from user toggle

    # Metadata
    steps: Annotated[List[str], add]
    retrieval_count: int
    used_web_search: bool  # Flag if web search was used
