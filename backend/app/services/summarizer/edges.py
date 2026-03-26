"""
Summarizer Workflow Edges
Conditional routing logic for the Summarizer workflow
"""

from typing import Literal
from app.services.summarizer.state import SummarizerState
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def route_by_style(state: SummarizerState) -> Literal["document", "notebook"]:
    """
    Route based on summarization style

    Args:
        state: Current workflow state

    Returns:
        "document" for single document summary
        "notebook" for notebook overview
    """
    style = state.get("style", "notebook")

    # If document_id is provided, always do document summary
    if state.get("document_id"):
        logger.info("[Summarizer] Routing to document summary (document_id provided)")
        return "document"

    # Otherwise, check style
    if style == "document":
        logger.info("[Summarizer] Routing to document summary")
        return "document"
    else:
        logger.info("[Summarizer] Routing to notebook overview")
        return "notebook"
