"""
FAQ Generator Workflow Edges
Conditional routing logic for the FAQ Generator workflow
"""

from typing import Literal
from app.services.faq_generator.state import FAQGeneratorState
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def route_by_topic_type(state: FAQGeneratorState) -> Literal["single", "multi"]:
    """
    Route based on topic type (single vs multi)

    Args:
        state: Current workflow state

    Returns:
        "single" for single-topic FAQ generation
        "multi" for multi-topic FAQ generation
    """
    topic_type = state.get("topic_type", "single")

    if topic_type == "single":
        logger.info("[FAQGenerator] Routing to single-topic FAQ generation")
        return "single"
    else:
        logger.info("[FAQGenerator] Routing to multi-topic FAQ generation")
        return "multi"
