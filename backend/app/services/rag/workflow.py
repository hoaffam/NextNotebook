"""
Corrective RAG (CRAG) Workflow
Main LangGraph workflow for document Q&A with web search fallback
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END

from app.services.rag.state import GraphState
from app.services.rag.nodes import GraphNodes
from app.services.rag.edges import decide_to_rewrite
from app.database.milvus_client import MilvusService
from app.services.shared.embedding_service import EmbeddingService
from app.services.shared.llm_service import LLMService
from app.services.shared.web_search_service import WebSearchService, get_web_search_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_rag_workflow(
    milvus_service: MilvusService,
    embedding_service: EmbeddingService,
    llm_service: LLMService,
    web_search_service: WebSearchService = None,
    lexical_service=None
) -> StateGraph:
    """
    Create the Corrective RAG (CRAG) workflow graph

    CRAG Workflow:
    1. Retrieve documents from Milvus
    2. Grade document relevance (Corrective step)
    3. Decide:
       - If enough relevant docs → generate
       - If few docs & first try → rewrite query → retrieve again
       - If still few docs → web search → generate
    4. Generate final answer with sources

    Graph:

    START → retrieve → grade → [decision]
                                   ↓ enough docs → generate → END
                                   ↓ few docs (1st) → rewrite → retrieve
                                   ↓ few docs (2nd) → web_search → generate → END
    """

    # Get web search service if not provided
    if web_search_service is None:
        web_search_service = get_web_search_service()

    # Initialize nodes
    nodes = GraphNodes(
        milvus_service=milvus_service,
        embedding_service=embedding_service,
        llm_service=llm_service,
        web_search_service=web_search_service,
        lexical_service=lexical_service
    )

    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("retrieve", nodes.retrieve)
    workflow.add_node("grade_documents", nodes.grade_documents)
    workflow.add_node("rewrite_query", nodes.rewrite_query)
    workflow.add_node("web_search", nodes.web_search)
    workflow.add_node("generate", nodes.generate)

    # Set entry point
    workflow.set_entry_point("retrieve")

    # Add edges
    workflow.add_edge("retrieve", "grade_documents")

    # CRAG Conditional edge: decide to rewrite, web search, or generate
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_rewrite,
        {
            "rewrite": "rewrite_query",
            "web_search": "web_search",
            "generate": "generate"
        }
    )

    # After rewrite, go back to retrieve
    workflow.add_edge("rewrite_query", "retrieve")

    # Web search leads to generate
    workflow.add_edge("web_search", "generate")

    # Generate is the end
    workflow.add_edge("generate", END)

    # Compile the graph
    compiled = workflow.compile()

    logger.info("CRAG workflow created successfully")

    return compiled


async def run_rag_workflow(
    question: str,
    notebook_id: str,
    chat_history: list = None,
    milvus_service: MilvusService = None,
    embedding_service: EmbeddingService = None,
    llm_service: LLMService = None,
    web_search_service: WebSearchService = None
) -> Dict[str, Any]:
    """
    Convenience function to run the CRAG workflow

    Args:
        question: User question
        notebook_id: Notebook to query
        chat_history: Previous messages
        milvus_service: Milvus instance
        embedding_service: Embedding instance
        llm_service: LLM instance
        web_search_service: Web search instance (optional)

    Returns:
        Workflow result with answer, sources, and web_sources
    """
    # Create workflow
    workflow = create_rag_workflow(
        milvus_service=milvus_service,
        embedding_service=embedding_service,
        llm_service=llm_service,
        web_search_service=web_search_service
    )

    # Initial state
    initial_state = {
        "question": question,
        "notebook_id": notebook_id,
        "chat_history": chat_history or [],
        "documents": [],
        "filtered_documents": [],
        "rewritten_question": None,
        "web_search_needed": False,
        "web_results": [],
        "answer": "",
        "sources": [],
        "web_sources": [],
        "steps": [],
        "retrieval_count": 0,
        "used_web_search": False
    }

    # Run the workflow
    result = await workflow.ainvoke(initial_state)

    return result
