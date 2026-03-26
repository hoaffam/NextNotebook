"""
Graph Edges
Conditional edge functions for the Corrective RAG (CRAG) LangGraph workflow
"""

from typing import Literal
from app.services.rag.state import GraphState
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

ANSWERABLE_THRESHOLD = 0.6   # coverage/answerable threshold (tune as needed)
COVERAGE_THRESHOLD   = 0.5   # minimal coverage to be acceptable
BEST_REL_THRESHOLD   = 0.35  # minimal relevance score for evidence
CITABLE_REQUIRED     = True  # require at least one citable chunk


def _best_relevance(state: GraphState) -> float:
    docs = state.get("filtered_documents", [])
    return max((d.get("score", 0) or 0) for d in docs) if docs else 0.0


def _is_answerable(state: GraphState) -> bool:
    # Either explicit flag or coverage high enough
    if state.get("answerable"):
        return True
    return state.get("coverage_score", 0) >= ANSWERABLE_THRESHOLD


def _coverage_ok(state: GraphState) -> bool:
    return state.get("coverage_score", 0) >= COVERAGE_THRESHOLD


def _is_citable(state: GraphState) -> bool:
    # This should be set upstream when a chunk has verbatim overlap and is not paraphrase
    return bool(state.get("citable"))


def decide_to_rewrite(state: GraphState) -> Literal["rewrite", "web_search", "generate"]:
    """
    CRAG Decision: Rewrite query, do web search, or proceed to generation

    Based on:
    - Number of relevant documents
    - Retrieval count (avoid infinite loops)
    - Web search availability
    - Force web search flag (user toggle)
    """
    retrieval_count = state.get("retrieval_count", 0)
    web_search_needed = state.get("web_search_needed", False)
    force_web_search = state.get("force_web_search", False)

    force_web_search = state.get("force_web_search", False)

    answerable = _is_answerable(state)
    coverage_ok = _coverage_ok(state)
    citable = _is_citable(state)
    best_rel = _best_relevance(state)

    # User forced web search (only then allow web search path)
    if force_web_search:
        logger.info("Decision: web search (user enabled)")
        return "web_search"

    # Not answerable or coverage low
    if not answerable or not coverage_ok:
        if retrieval_count < 2:
            logger.info("Decision: rewrite (not answerable/coverage low)")
            return "rewrite"
        if force_web_search:
            logger.info("Decision: web search (not answerable/coverage low after rewrite; user enabled)")
            return "web_search"
        logger.info("Decision: generate (web search disabled by UI)")
        return "generate"

    # Need a citable chunk
    if CITABLE_REQUIRED and not citable:
        if force_web_search:
            logger.info("Decision: web search (need citable chunk; user enabled)")
            return "web_search"
        logger.info("Decision: generate (web search disabled by UI, no citable chunk)")
        return "generate"

    # Evidence relevance too low
    if best_rel < BEST_REL_THRESHOLD:
        if retrieval_count < 2:
            logger.info("Decision: rewrite (evidence relevance low)")
        return "rewrite"
        if force_web_search:
            logger.info("Decision: web search (evidence relevance low after rewrite; user enabled)")
        return "web_search"
        logger.info("Decision: generate (web search disabled by UI despite low relevance)")
        return "generate"

    # Quality conditions satisfied -> generate
    logger.info("Decision: generate (answerable & coverage ok & citable & relevance ok)")
    return "generate"


def decide_after_rewrite(state: GraphState) -> Literal["retrieve", "web_search"]:
    """
    After rewriting, decide whether to retrieve again or web search
    """
    retrieval_count = state.get("retrieval_count", 0)

    if retrieval_count < 2:
        logger.info("Decision: retrieve again with rewritten query")
        return "retrieve"

    logger.info("Decision: web search (max retrieval reached)")
    return "web_search"


def decide_web_search(state: GraphState) -> Literal["web_search", "generate"]:
    """
    Decide whether to perform web search

    Based on:
    - web_search_needed flag
    - Number of filtered documents
    """
    web_search_needed = state.get("web_search_needed", False)
    filtered_docs = state.get("filtered_documents", [])
    force_web_search = state.get("force_web_search", False)

    answerable = _is_answerable(state)
    coverage_ok = _coverage_ok(state)
    citable = _is_citable(state)
    best_rel = _best_relevance(state)

    if force_web_search:
        if web_search_needed and not filtered_docs:
            logger.info("Decision: web search needed (no filtered docs, user enabled)")
            return "web_search"
        if (not answerable) or (not coverage_ok) or (CITABLE_REQUIRED and not citable) or (best_rel < BEST_REL_THRESHOLD):
            logger.info("Decision: web search (quality conditions not met, user enabled)")
        return "web_search"
        logger.info("Decision: skip web search (quality conditions satisfied, user enabled)")
        return "generate"

    # Web search disabled by UI
    logger.info("Decision: skip web search (disabled by UI)")
    return "generate"


def should_continue_retrieval(state: GraphState) -> Literal["retrieve", "end"]:
    """
    Decide if we should do another retrieval iteration
    """
    retrieval_count = state.get("retrieval_count", 0)
    rewritten = state.get("rewritten_question")

    if rewritten and retrieval_count < 2:
        logger.info("Decision: continue retrieval with rewritten query")
        return "retrieve"

    return "end"
