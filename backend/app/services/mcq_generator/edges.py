"""
MCQ Generator Workflow Edges
Conditional routing logic for the MCQ Generator workflow
"""

from typing import Literal
from app.services.mcq_generator.state import MCQGeneratorState
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def check_chunk_availability(state: MCQGeneratorState) -> Literal["enough", "generate"]:
    """
    Check if we have enough chunks to generate quality questions

    Args:
        state: Current workflow state

    Returns:
        "enough" if sufficient chunks available
        "generate" to proceed with generation anyway (will handle in node)
    """
    chunks = state.get("all_chunks", [])
    num_questions = state.get("num_questions", 10)

    # Need at least 2 chunks per question for diversity
    required_chunks = num_questions * 2

    if len(chunks) >= required_chunks:
        logger.info(f"[MCQGenerator] Sufficient chunks: {len(chunks)} >= {required_chunks}")
        return "enough"
    else:
        logger.warning(f"[MCQGenerator] Limited chunks: {len(chunks)} < {required_chunks}, proceeding anyway")
        return "generate"
