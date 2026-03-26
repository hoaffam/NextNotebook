"""
FAQ Generator State Definition
State for the FAQ Generator LangGraph workflow
"""

from typing import TypedDict, List, Dict, Annotated
from typing_extensions import Literal


def add(a: List, b: List) -> List:
    """Operator to accumulate steps"""
    return a + b


class FAQGeneratorState(TypedDict):
    """State definition for FAQ Generator workflow"""

    # Input
    notebook_id: str
    num_questions: int

    # Processing
    all_chunks: List[Dict]  # All chunks from Milvus
    combined_text: str  # Combined text for generation
    detected_topics: List[str]  # Topics detected in content
    topic_type: str  # "single" or "multi"
    raw_faqs: List[Dict]  # Raw FAQs from LLM

    # Output
    faqs: List[Dict]  # Final formatted FAQs {question, answer, topic}
    total_generated: int

    # Metadata
    steps: Annotated[List[str], add]
    topic_count: int
    chunk_count: int
